import psycopg2
import json
from datetime import datetime
import sys
from collections import defaultdict, deque

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

def build_relationship_graph(database_schema):
    """Build a graph of table relationships for path finding"""
    graph = defaultdict(list)
    reverse_graph = defaultdict(list)
    
    for table_name, table_info in database_schema["tables"].items():
        if "relationships" in table_info:
            for rel in table_info["relationships"]:
                from_table = table_name
                to_table = rel["to_table"]
                from_col = rel["from_column"]
                to_col = rel["to_column"]
                
                # Build bidirectional graph for path finding
                graph[from_table].append({
                    "table": to_table,
                    "from_col": from_col,
                    "to_col": to_col,
                    "type": "FK"
                })
                
                reverse_graph[to_table].append({
                    "table": from_table,
                    "from_col": to_col,
                    "to_col": from_col,
                    "type": "FK_REV"
                })
    
    # Merge graphs
    all_connections = defaultdict(list)
    for table, connections in graph.items():
        all_connections[table].extend(connections)
    for table, connections in reverse_graph.items():
        all_connections[table].extend(connections)
    
    return all_connections

def find_table_path(graph, start_table, end_table):
    """Find the shortest path between two tables using BFS"""
    if start_table == end_table:
        return [start_table]
    
    if start_table not in graph:
        return None
    
    queue = deque([(start_table, [start_table])])
    visited = set([start_table])
    
    while queue:
        current_table, path = queue.popleft()
        
        for connection in graph[current_table]:
            next_table = connection["table"]
            
            if next_table == end_table:
                return path + [next_table]
            
            if next_table not in visited:
                visited.add(next_table)
                queue.append((next_table, path + [next_table]))
    
    return None

def get_path_details(graph, path):
    """Get detailed connection information for a path"""
    if len(path) < 2:
        return []
    
    path_details = []
    for i in range(len(path) - 1):
        current_table = path[i]
        next_table = path[i + 1]
        
        # Find the connection between current and next table
        for connection in graph[current_table]:
            if connection["table"] == next_table:
                path_details.append({
                    "from_table": current_table,
                    "to_table": next_table,
                    "from_column": connection["from_col"],
                    "to_column": connection["to_col"],
                    "connection_type": connection["type"]
                })
                break
    
    return path_details

def generate_all_table_paths(relationship_graph, max_depth=4):
    """Generate all possible paths between tables (non-recursive, limited depth)"""
    all_paths = {}
    tables = list(relationship_graph.keys())
    
    for start_table in tables:
        for end_table in tables:
            if start_table != end_table:
                path = find_table_path(relationship_graph, start_table, end_table)
                if path and len(path) <= max_depth:  # Limit depth to avoid very long paths
                    path_key = f"{start_table} -> {end_table}"
                    
                    # Get detailed path with columns
                    if len(path) > 1:
                        path_details = get_path_details(relationship_graph, path)
                        detailed_path = []
                        
                        for detail in path_details:
                            detailed_path.append(f"{detail['from_table']}({detail['from_column']})")
                        
                        if path_details:
                            detailed_path.append(f"{path_details[-1]['to_table']}({path_details[-1]['to_column']})")
                        
                        all_paths[path_key] = " → ".join(detailed_path)
                    else:
                        all_paths[path_key] = start_table
    
    return all_paths

def generate_llm_friendly_format(database_schema, relationship_graph):
    """Generate a Markdown-formatted, LLM-friendly text format"""
    output = []
    
    # Database header with metadata
    output.append(f"# Database Schema: {database_schema['database']}")
    output.append(f"**Extracted:** {database_schema['extracted_at']}")
    output.append("")
    
    # Overview section
    table_count = len(database_schema["tables"])
    output.append("## Overview")
    output.append(f"- **Total Tables:** {table_count}")
    output.append("")
    
    # Tables of Contents
    output.append("## Table of Contents")
    output.append("- [Tables](#tables)")
    output.append("- [Relationship Paths](#relationship-paths)")
    output.append("")
    
    # Tables section
    output.append("## Tables")
    output.append("")
    
    for table_name, table_info in database_schema["tables"].items():
        # Table header
        output.append(f"### `{table_name}`")
        output.append("")
        
        # Columns section
        output.append("#### Columns")
        output.append("")
        
        pk_cols = []
        fk_cols = []
        regular_cols = []
        
        for col_name, col_info in table_info["columns"].items():
            col_type = col_info['type']
            nullable_symbol = "✓" if col_info.get("nullable", True) else "✗"
            
            if col_info.get("primary_key"):
                pk_cols.append((col_name, col_type, nullable_symbol))
            elif "foreign_key" in col_info:
                fk_info = col_info["foreign_key"]
                fk_cols.append((col_name, col_type, nullable_symbol, fk_info))
            else:
                regular_cols.append((col_name, col_type, nullable_symbol))
        
        # Primary Keys table
        if pk_cols:
            output.append("**Primary Keys:**")
            output.append("")
            output.append("| Column | Type | Nullable |")
            output.append("|--------|------|----------|")
            for col_name, col_type, nullable in pk_cols:
                output.append(f"| `{col_name}` | {col_type} | {nullable} |")
            output.append("")
        
        # Foreign Keys table
        if fk_cols:
            output.append("**Foreign Keys:**")
            output.append("")
            output.append("| Column | Type | References | Nullable |")
            output.append("|--------|------|------------|----------|")
            for col_name, col_type, nullable, fk_info in fk_cols:
                ref_table = fk_info['references_table']
                ref_column = fk_info['references_column']
                output.append(f"| `{col_name}` | {col_type} | `{ref_table}.{ref_column}` | {nullable} |")
            output.append("")
        
        # Regular columns table
        if regular_cols:
            output.append("**Other Columns:**")
            output.append("")
            output.append("| Column | Type | Nullable |")
            output.append("|--------|------|----------|")
            for col_name, col_type, nullable in regular_cols:
                output.append(f"| `{col_name}` | {col_type} | {nullable} |")
            output.append("")
        
        # Indexes section
        if "indexes" in table_info and table_info["indexes"]:
            output.append("#### Indexes")
            output.append("")
            output.append("| Index Name | Columns | Type |")
            output.append("|------------|---------|------|")
            for idx in table_info["indexes"]:
                idx_type = "🔑 UNIQUE" if idx["unique"] else "📇 INDEX"
                cols = ", ".join([f"`{col}`" for col in idx['columns']])
                output.append(f"| `{idx['name']}` | {cols} | {idx_type} |")
            output.append("")
        
        output.append("---")
        output.append("")
    
    # Relationship paths section
    output.append("## Relationship Paths")
    output.append("")
    output.append("Pre-calculated paths between all tables for query optimization.")
    output.append("")
    
    all_paths = generate_all_table_paths(relationship_graph)
    
    if all_paths:
        # Group paths by starting table for better organization
        paths_by_start_table = {}
        for path_key, path_detail in all_paths.items():
            start_table = path_key.split(' -> ')[0]
            if start_table not in paths_by_start_table:
                paths_by_start_table[start_table] = []
            paths_by_start_table[start_table].append((path_key, path_detail))
        
        for start_table in sorted(paths_by_start_table.keys()):
            output.append(f"### From `{start_table}`")
            output.append("")
            
            # Create table for paths from this starting table
            output.append("| Destination | Path |")
            output.append("|-------------|------|")
            
            for path_key, path_detail in sorted(paths_by_start_table[start_table]):
                end_table = path_key.split(' -> ')[1]
                # Format path with code blocks for table/column names
                formatted_path = path_detail.replace('(', '(` ').replace(')', ' `)').replace(' → ', ' → `')
                if not formatted_path.startswith('`'):
                    formatted_path = '`' + formatted_path
                if not formatted_path.endswith('`'):
                    formatted_path = formatted_path + '`'
                output.append(f"| `{end_table}` | {formatted_path} |")
            
            output.append("")
    else:
        output.append("*No relationship paths found between tables.*")
        output.append("")
    
    # Footer
    output.append("---")
    output.append("")
    output.append("*This schema documentation was automatically generated for LLM query optimization.*")
    
    return "\n".join(output)

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
        
        # Get column information
        columns_info = get_column_info(cursor, schema_name, table_name)
        
        # Get indexes (excluding primary keys)
        indexes_info = get_indexes(cursor, schema_name, table_name)
        
        # Process columns - keep only essential info
        columns = {}
        relationships = []
        
        for col_info in columns_info:
            (col_name, data_type, is_nullable, col_comment, is_pk, 
             fk_schema, fk_table, fk_column, fk_constraint, fk_update_rule, fk_delete_rule) = col_info
            
            # Store only essential column info
            columns[col_name] = {
                "type": data_type,
                "nullable": is_nullable == 'YES'
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
                
                columns[col_name]["foreign_key"] = fk_details
                
                # Also add to relationships array for easier parsing
                relationships.append({
                    "from_column": col_name,
                    "to_table": f"{fk_schema}.{fk_table}" if fk_schema != schema_name else fk_table,
                    "to_column": fk_column,
                    "constraint": fk_constraint,
                    "relationship_type": "many_to_one"
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
            "columns": columns
        }
        
        # Add optional info only if present
        if relationships:
            table_data["relationships"] = relationships
        if indexes:
            table_data["indexes"] = indexes
        
        database_schema["tables"][f"{schema_name}.{table_name}"] = table_data
    
    # Close database connection
    cursor.close()
    conn.close()
    
    # Build relationship graph for path finding
    relationship_graph = build_relationship_graph(database_schema)
    
    # Generate LLM-friendly format
    llm_format = generate_llm_friendly_format(database_schema, relationship_graph)
    
    # Save the Markdown-formatted output
    md_filename = f"schema_{DB_PARAMS['dbname']}.md"
    with open(md_filename, 'w', encoding='utf-8') as f:
        f.write(llm_format)
    
    print(f"\n✅ Database schema extracted!")
    print(f"📄 Output file: {md_filename}")
    print(f"📊 Total tables: {len(database_schema['tables'])}")
    
    # Print compact summary
    for table_name, table_info in database_schema["tables"].items():
        col_count = len(table_info['columns'])
        print(f"  📋 {table_name}: {col_count} columns")
    
    # Test path finding
    print("\n🔗 Testing path finding...")
    tables = list(database_schema["tables"].keys())
    if len(tables) >= 2:
        test_path = find_table_path(relationship_graph, tables[0], tables[-1])
        if test_path:
            path_details = get_path_details(relationship_graph, test_path)
            path_str = " → ".join([
                f"{detail['from_table']}({detail['from_column']})" for detail in path_details
            ] + [f"{path_details[-1]['to_table']}({path_details[-1]['to_column']})"] if path_details else [test_path[-1]])
            print(f"  Example path from {tables[0]} to {tables[-1]}: {path_str}")
        else:
            print(f"  No path found between {tables[0]} and {tables[-1]}")
    
    return database_schema, relationship_graph, llm_format

if __name__ == "__main__":
    try:
        schema, graph, llm_text = extract_database_schema()
        print("\n✅ Schema extraction completed successfully!")
        print("\n📝 Output Preview:")
        print("=" * 50)
        print(llm_text[:1500] + "..." if len(llm_text) > 1500 else llm_text)
    except Exception as e:
        print(f"❌ Error during schema extraction: {e}")
        sys.exit(1)