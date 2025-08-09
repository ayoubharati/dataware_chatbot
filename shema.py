import psycopg2
import json
from datetime import datetime
import sys

# Database connection parameters
DB_PARAMS = {
    'dbname': 'dataware_test',
    'user': 'postgres',
    'password': 'bath123',
    'host': 'localhost',
    'port': '5433'
}

def connect_to_database():
    """Establish connection to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def get_table_info(cursor):
    """Get all tables with their basic information"""
    query = """
    SELECT 
        t.table_schema,
        t.table_name,
        t.table_type,
        obj_description(c.oid) as table_comment
    FROM information_schema.tables t
    LEFT JOIN pg_class c ON c.relname = t.table_name
    LEFT JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = t.table_schema
    WHERE t.table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
    ORDER BY t.table_schema, t.table_name;
    """
    
    cursor.execute(query)
    return cursor.fetchall()

def get_column_info(cursor, schema_name, table_name):
    """Get essential column information including detailed FK info for query generation"""
    query = """
    SELECT 
        c.column_name,
        c.data_type,
        c.is_nullable,
        col_description(pgc.oid, c.ordinal_position) as column_comment,
        CASE 
            WHEN pk.column_name IS NOT NULL THEN true
            ELSE false
        END as is_primary_key,
        fk.foreign_table_schema,
        fk.foreign_table_name,
        fk.foreign_column_name,
        fk.constraint_name,
        fk.update_rule,
        fk.delete_rule
    FROM information_schema.columns c
    LEFT JOIN pg_class pgc ON pgc.relname = c.table_name
    LEFT JOIN pg_namespace pgn ON pgn.oid = pgc.relnamespace AND pgn.nspname = c.table_schema
    -- Primary key information
    LEFT JOIN (
        SELECT ku.table_schema, ku.table_name, ku.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage ku 
            ON tc.constraint_name = ku.constraint_name
            AND tc.table_schema = ku.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY'
    ) pk ON pk.table_schema = c.table_schema 
        AND pk.table_name = c.table_name 
        AND pk.column_name = c.column_name
    -- Detailed foreign key information
    LEFT JOIN (
        SELECT 
            tc.table_schema,
            tc.table_name,
            kcu.column_name,
            tc.constraint_name,
            ccu.table_schema AS foreign_table_schema,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            rc.update_rule,
            rc.delete_rule
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu 
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        LEFT JOIN information_schema.referential_constraints rc
            ON rc.constraint_name = tc.constraint_name
            AND rc.constraint_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
    ) fk ON fk.table_schema = c.table_schema 
        AND fk.table_name = c.table_name 
        AND fk.column_name = c.column_name
    WHERE c.table_schema = %s AND c.table_name = %s
    ORDER BY c.ordinal_position;
    """
    
    cursor.execute(query, (schema_name, table_name))
    return cursor.fetchall()

def get_table_stats(cursor, schema_name, table_name):
    """Get basic table statistics - just row count for context"""
    try:
        # Get row count only - most important for query planning
        count_query = f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}";'
        cursor.execute(count_query)
        row_count = cursor.fetchone()[0]
        return row_count
    except Exception as e:
        print(f"Warning: Could not get row count for {schema_name}.{table_name}: {e}")
        return None

def get_indexes(cursor, schema_name, table_name):
    """Get only essential index information for query optimization"""
    query = """
    SELECT 
        i.relname as index_name,
        array_agg(a.attname ORDER BY a.attname) as columns,
        ix.indisunique as is_unique
    FROM pg_class t
    JOIN pg_namespace n ON n.oid = t.relnamespace
    JOIN pg_index ix ON t.oid = ix.indrelid
    JOIN pg_class i ON i.oid = ix.indexrelid
    JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
    WHERE n.nspname = %s AND t.relname = %s AND NOT ix.indisprimary
    GROUP BY i.relname, ix.indisunique
    ORDER BY i.relname;
    """
    
    cursor.execute(query, (schema_name, table_name))
    return cursor.fetchall()

def generate_intelligent_descriptions(table_name, column_name, data_type, is_pk, has_fk):
    """Generate concise, query-focused descriptions"""
    column_lower = column_name.lower()
    
    # Primary key
    if is_pk:
        return f"Primary key for {table_name}"
    
    # Foreign key
    if has_fk:
        return f"References {has_fk}"
    
    # Common patterns - keep very concise
    if column_lower.endswith('_id') or column_lower == 'id':
        return f"Identifier"
    if 'date' in column_lower or 'time' in column_lower:
        if 'created' in column_lower:
            return "Record creation time"
        elif 'updated' in column_lower:
            return "Last update time"
        else:
            return "Date/time value"
    if 'name' in column_lower:
        return "Name/title"
    if 'email' in column_lower:
        return "Email address"
    if 'status' in column_lower:
        return "Status/state"
    if 'amount' in column_lower or 'price' in column_lower:
        return "Monetary value"
    if data_type == 'boolean':
        return "True/false flag"
    
    return f"{column_name} value"

def extract_database_schema():
    """Main function to extract complete database schema"""
    conn = connect_to_database()
    cursor = conn.cursor()
    
    print("Connecting to PostgreSQL database...")
    print(f"Database: {DB_PARAMS['dbname']} at {DB_PARAMS['host']}:{DB_PARAMS['port']}")
    
    # Get all tables
    tables_info = get_table_info(cursor)
    print(f"Found {len(tables_info)} tables")
    
    # Build the minimal schema dictionary for query generation
    database_schema = {
        "database": DB_PARAMS['dbname'],
        "extracted_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "tables": {}
    }
    
    for table_info in tables_info:
        schema_name, table_name, table_type, table_comment = table_info
        
        print(f"Processing table: {schema_name}.{table_name}")
        
        # Initialize schema if not exists - removed, using flat structure now
        
        # Get column information
        columns_info = get_column_info(cursor, schema_name, table_name)
        
        # Get table row count
        row_count = get_table_stats(cursor, schema_name, table_name)
        
        # Get indexes (excluding primary keys)
        indexes_info = get_indexes(cursor, schema_name, table_name)
        
        # Process columns - keep only essential info
        columns = {}
        relationships = []
        
        for col_info in columns_info:
            (col_name, data_type, is_nullable, col_comment, is_pk, 
             fk_schema, fk_table, fk_column, fk_constraint, fk_update_rule, fk_delete_rule) = col_info
            
            # Generate description if no comment exists
            fk_ref = f"{fk_table}.{fk_column}" if fk_table and fk_column else None
            description = col_comment if col_comment else generate_intelligent_descriptions(
                table_name, col_name, data_type, is_pk, fk_ref
            )
            
            # Store only essential column info
            columns[col_name] = {
                "type": data_type,
                "nullable": is_nullable == 'YES',
                "description": description
            }
            
            # Mark primary key
            if is_pk:
                columns[col_name]["primary_key"] = True
            
            # Store detailed foreign key info
            if fk_table and fk_column:
                fk_details = {
                    "references_table": f"{fk_schema}.{fk_table}" if fk_schema != schema_name else fk_table,
                    "references_column": fk_column,
                    "constraint_name": fk_constraint
                }
                
                # Add cascade rules if they exist and are not default
                if fk_update_rule and fk_update_rule != 'NO ACTION':
                    fk_details["on_update"] = fk_update_rule
                if fk_delete_rule and fk_delete_rule != 'NO ACTION':
                    fk_details["on_delete"] = fk_delete_rule
                    
                columns[col_name]["foreign_key"] = fk_details
                
                # Also add to relationships array for easier parsing
                relationships.append({
                    "from_column": col_name,
                    "to_table": f"{fk_schema}.{fk_table}" if fk_schema != schema_name else fk_table,
                    "to_column": fk_column,
                    "constraint": fk_constraint,
                    "relationship_type": "many_to_one"  # Most FK relationships are many-to-one
                })
        
        # Process indexes - simplified
        indexes = []
        for idx_info in indexes_info:
            idx_name, columns_array, is_unique = idx_info
            indexes.append({
                "name": idx_name,
                "columns": columns_array,
                "unique": is_unique
            })
        
        # Build minimal table info
        table_data = {
            "description": table_comment if table_comment else f"{table_name} data table",
            "columns": columns
        }
        
        # Add optional info only if present
        if row_count is not None:
            table_data["row_count"] = row_count
        if relationships:
            table_data["relationships"] = relationships
        if indexes:
            table_data["indexes"] = indexes
        
        database_schema["tables"][f"{schema_name}.{table_name}"] = table_data
    
    # Close database connection
    cursor.close()
    conn.close()
    
    # Save to compact JSON file
    output_filename = f"schema_compact_{DB_PARAMS['dbname']}.json"
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(database_schema, f, indent=1, ensure_ascii=False, separators=(',', ':'))
    
    print(f"\n✅ Compact database schema extracted!")
    print(f"📄 Output saved to: {output_filename}")
    print(f"📊 Total tables: {len(database_schema['tables'])}")
    
    # Print compact summary
    for table_name, table_info in database_schema["tables"].items():
        col_count = len(table_info['columns'])
        row_info = f", ~{table_info['row_count']} rows" if 'row_count' in table_info else ""
        print(f"  📋 {table_name}: {col_count} columns{row_info}")
    
    return database_schema

if __name__ == "__main__":
    try:
        schema = extract_database_schema()
        print("\n✅ Schema extraction completed successfully!")
    except Exception as e:
        print(f"❌ Error during schema extraction: {e}")
        sys.exit(1)