
import sqlite3
import os
from contextlib import contextmanager
import sys

# Import configuration
try:
    from config import DATABASE_PATH
except ImportError:
    # Fallback to using the dev_game.db in root directory
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dev_game.db')

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def view_tables():
    """List all tables in the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database.")
            return
            
        print("\nTables in database:")
        for i, table in enumerate(tables):
            print(f"{i+1}. {table['name']}")

def view_table_schema(table_name):
    """View the schema of a specific table"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        if not columns:
            print(f"Table '{table_name}' not found or has no columns.")
            return
            
        print(f"\nSchema for table '{table_name}':")
        for col in columns:
            print(f"- {col['name']} ({col['type']})")

def execute_query(query):
    """Execute a custom SQL query"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            
            # Check if this is a SELECT query
            if query.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                
                if not rows:
                    print("Query returned no results.")
                    return
                
                # Get column names
                column_names = [description[0] for description in cursor.description]
                
                # Print header
                header = " | ".join(column_names)
                print("\nResults:")
                print(header)
                print("-" * len(header))
                
                # Print rows
                for row in rows:
                    row_dict = dict(row)
                    print(" | ".join(str(row_dict[col]) for col in column_names))
                
                print(f"\nTotal rows: {len(rows)}")
            else:
                conn.commit()
                print(f"Query executed successfully. Rows affected: {cursor.rowcount}")
                
        except sqlite3.Error as e:
            print(f"Error executing query: {e}")

def interactive_mode():
    """Run the viewer in interactive mode"""
    while True:
        print("\n==== SQLite Database Viewer ====")
        print("1. View all tables")
        print("2. View table schema")
        print("3. Execute custom query")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            view_tables()
        elif choice == '2':
            table_name = input("Enter table name: ")
            view_table_schema(table_name)
        elif choice == '3':
            query = input("Enter SQL query: ")
            execute_query(query)
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        print(f"Error: Database file not found at {DATABASE_PATH}")
        sys.exit(1)
        
    print(f"Connected to database: {DATABASE_PATH}")
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--tables":
            view_tables()
        elif sys.argv[1] == "--schema" and len(sys.argv) > 2:
            view_table_schema(sys.argv[2])
        elif sys.argv[1] == "--query" and len(sys.argv) > 2:
            execute_query(" ".join(sys.argv[2:]))
        else:
            print("Usage:")
            print("  python db_viewer.py                   # Interactive mode")
            print("  python db_viewer.py --tables          # List all tables")
            print("  python db_viewer.py --schema TABLE    # View table schema")
            print("  python db_viewer.py --query SQL_QUERY # Execute custom query")
    else:
        interactive_mode()
