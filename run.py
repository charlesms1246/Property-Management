from app import create_app, db
from app.models import User, Property, Tenant, MaintenanceRequest, RentPayment

app = create_app()

@app.cli.command('init-db')
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database tables created.')

if __name__ == '__main__':
    app.run(debug=True) 