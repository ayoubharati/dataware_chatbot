from sentence_transformers import SentenceTransformer
import psycopg2
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Global model (shared across threads - SentenceTransformer is thread-safe)
model = SentenceTransformer('all-MiniLM-L12-v2')

# Database connection parameters
DB_CONFIG = {
    'dbname': 'dataware_test',
    'user': 'postgres',
    'password': 'bath123',
    'host': 'localhost',
    'port': 5433
}

# Thread-safe print with timestamp and thread info
def thread_print(message, table_name=None):
    thread_id = threading.current_thread().ident
    thread_name = threading.current_thread().name
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if table_name:
        print(f"[{timestamp}] Thread-{thread_id} ({thread_name}) [{table_name}]: {message}")
    else:
        print(f"[{timestamp}] Thread-{thread_id} ({thread_name}): {message}")

def process_table(table_name):
    """Process a single table in its own thread"""
    start_time = time.time()
    thread_print(f"Started processing table", table_name)
    
    # Each thread gets its own connection
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        thread_print("Database connection established", table_name)
        
        # Check if table has 'embedding' column
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns
            WHERE table_schema = 'public' 
              AND table_name = %s 
              AND column_name = 'embedding'
        """, (table_name,))
        
        if cur.fetchone()[0] == 0:
            thread_print("SKIPPED - no embedding column", table_name)
            return {"table": table_name, "status": "skipped", "reason": "no embedding column", "rows": 0, "duration": 0}
        
        # Get columns except embedding
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns
            WHERE table_schema = 'public' 
              AND table_name = %s 
              AND column_name != 'embedding'
            ORDER BY ordinal_position
        """, (table_name,))
        columns = [row[0] for row in cur.fetchall()]
        
        if not columns:
            thread_print("SKIPPED - no data columns", table_name)
            return {"table": table_name, "status": "skipped", "reason": "no data columns", "rows": 0, "duration": 0}
        
        # Get ALL rows
        select_cols = ", ".join(columns)
        cur.execute(f"SELECT {select_cols} FROM public.{table_name}")
        rows = cur.fetchall()
        
        if not rows:
            thread_print("SKIPPED - no data rows", table_name)
            return {"table": table_name, "status": "skipped", "reason": "no data rows", "rows": 0, "duration": 0}
        
        thread_print(f"Found {len(rows)} rows to process", table_name)
        
        # Process each row
        pk_col = columns[0]  # Assuming first column is PK
        rows_updated = 0
        
        for i, row in enumerate(rows, 1):
            # Progress update every 100 rows or for small tables
            if i % 100 == 0 or len(rows) <= 50:
                thread_print(f"Processing row {i}/{len(rows)}", table_name)
            
            # Build text for embedding
            pieces = []
            for col_name, val in zip(columns, row):
                val_str = str(val).replace("'", "''") if val is not None else 'NULL'
                pieces.append(f"{col_name}:'{val_str}'")
            text = ", ".join(pieces)
            
            # Create embedding
            embedding = model.encode(text).tolist()
            
            # Update embedding in DB
            update_sql = f"UPDATE public.{table_name} SET embedding = %s WHERE {pk_col} = %s"
            cur.execute(update_sql, (embedding, row[0]))
            rows_updated += 1
        
        conn.commit()
        duration = time.time() - start_time
        thread_print(f"✅ COMPLETED - Updated {rows_updated} rows in {duration:.2f}s", table_name)
        
        return {
            "table": table_name, 
            "status": "completed", 
            "rows": rows_updated, 
            "duration": duration
        }
        
    except Exception as e:
        duration = time.time() - start_time
        thread_print(f"❌ ERROR - {str(e)}", table_name)
        if 'conn' in locals():
            conn.rollback()
        return {
            "table": table_name, 
            "status": "error", 
            "error": str(e), 
            "rows": 0, 
            "duration": duration
        }
    
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()
        thread_print("Database connection closed", table_name)

def main():
    start_time = time.time()
    print("🚀 Starting parallel embedding processing...")
    
    # Get list of tables
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    """)
    tables = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    
    print(f"📋 Found {len(tables)} tables to process: {', '.join(tables)}")
    
    # Process tables in parallel
    max_workers = min(len(tables), 4)  # Limit concurrent threads
    print(f"🔧 Using {max_workers} worker threads")
    
    results = []
    completed_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="TableProcessor") as executor:
        # Submit all table processing tasks
        future_to_table = {executor.submit(process_table, table): table for table in tables}
        
        # Process completed tasks as they finish
        for future in as_completed(future_to_table):
            table = future_to_table[future]
            try:
                result = future.result()
                results.append(result)
                completed_count += 1
                
                print(f"\n📊 PROGRESS: {completed_count}/{len(tables)} tables completed")
                print(f"   Latest: {result['table']} - {result['status'].upper()}")
                if result['status'] == 'completed':
                    print(f"   Rows: {result['rows']}, Duration: {result['duration']:.2f}s")
                
            except Exception as e:
                print(f"❌ Unexpected error for table {table}: {e}")
                results.append({
                    "table": table,
                    "status": "failed",
                    "error": str(e),
                    "rows": 0,
                    "duration": 0
                })
                completed_count += 1
    
    # Print final summary
    total_duration = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"🏁 FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"Total processing time: {total_duration:.2f} seconds")
    print(f"Tables processed: {len(results)}")
    
    completed = [r for r in results if r['status'] == 'completed']
    skipped = [r for r in results if r['status'] == 'skipped']
    errors = [r for r in results if r['status'] in ['error', 'failed']]
    
    print(f"✅ Completed: {len(completed)}")
    print(f"⏭️  Skipped: {len(skipped)}")
    print(f"❌ Errors: {len(errors)}")
    
    if completed:
        total_rows = sum(r['rows'] for r in completed)
        avg_duration = sum(r['duration'] for r in completed) / len(completed)
        print(f"📈 Total rows processed: {total_rows}")
        print(f"⏱️  Average time per table: {avg_duration:.2f}s")
    
    # Detailed breakdown
    if completed:
        print(f"\n✅ COMPLETED TABLES:")
        for r in completed:
            print(f"   {r['table']}: {r['rows']} rows in {r['duration']:.2f}s")
    
    if skipped:
        print(f"\n⏭️  SKIPPED TABLES:")
        for r in skipped:
            print(f"   {r['table']}: {r['reason']}")
    
    if errors:
        print(f"\n❌ FAILED TABLES:")
        for r in errors:
            error_msg = r.get('error', 'Unknown error')
            print(f"   {r['table']}: {error_msg}")

if __name__ == "__main__":
    main()