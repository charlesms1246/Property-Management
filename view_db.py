from app import create_app, db
from app.models import User, Property, Tenant, MaintenanceRequest, RentPayment
from tabulate import tabulate
import sys
from sqlalchemy import text

def init_db():
    """Initialize the database and create all tables"""
    app = create_app()
    with app.app_context():
        print("Initializing database...")
        db.create_all()
        print("Database tables created successfully!")

def view_tables():
    """View database tables and their contents"""
    app = create_app()
    with app.app_context():
        # Get all table names
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if not tables:
            print("\nNo tables found in the database.")
            return

        print("\nAvailable tables:")
        for i, table in enumerate(tables, 1):
            print(f"{i}. {table}")

        while True:
            print("\nOptions:")
            print("1. View table schema")
            print("2. View table contents")
            print("3. Exit")
            
            choice = input("\nEnter your choice (1-3): ")
            
            if choice == '3':
                sys.exit(0)
            
            if choice not in ['1', '2']:
                print("Invalid choice. Please try again.")
                continue
            
            table_name = input("Enter table name: ")
            if table_name not in tables:
                print(f"Table {table_name} not found")
                continue
            
            if choice == '1':
                # View table schema
                columns = inspector.get_columns(table_name)
                headers = ['Column Name', 'Type', 'Nullable', 'Default']
                rows = [[col['name'], col['type'], col['nullable'], col['default']] for col in columns]
                print(f"\nSchema for table {table_name}:")
                print(tabulate(rows, headers=headers, tablefmt='grid'))
            
            elif choice == '2':
                # View table contents
                try:
                    result = db.session.execute(text(f"SELECT * FROM {table_name}"))
                    rows = result.fetchall()
                    if not rows:
                        print(f"\nNo data found in table {table_name}")
                    else:
                        headers = result.keys()
                        print(f"\nContents of table {table_name}:")
                        print(tabulate(rows, headers=headers, tablefmt='grid'))
                except Exception as e:
                    print(f"Error viewing table contents: {str(e)}")

if __name__ == '__main__':
    init_db()
    view_tables() 