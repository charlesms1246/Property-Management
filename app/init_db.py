import sqlite3
from pathlib import Path

def init_db():
    """Initialize the database with the schema."""
    # Get the path to the schema file
    schema_path = Path(__file__).parent / 'schema.sql'
    
    # Connect to the database
    db_path = Path(__file__).parent.parent / 'instance' / 'property_management.db'
    conn = sqlite3.connect(db_path)
    
    try:
        # Read and execute the schema file
        with open(schema_path) as f:
            schema = f.read()
        
        # Split the schema into individual statements
        statements = schema.split(';')
        
        # Execute each statement
        for statement in statements:
            if statement.strip():
                conn.execute(statement)
        
        # Commit the changes
        conn.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    init_db() 