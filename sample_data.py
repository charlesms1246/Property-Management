from app import create_app, db
from app.models import User, Property, Tenant, MaintenanceRequest, RentPayment, init_db
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from sqlalchemy import text

def add_sample_data():
    app = create_app()
    with app.app_context():
        # Initialize database with all tables and constraints
        init_db()
        
        # Clear existing data
        db.session.query(RentPayment).delete()
        db.session.execute(text("DELETE FROM maintenance_requests"))
        db.session.query(Tenant).delete()
        db.session.query(Property).delete()
        db.session.query(User).delete()
        db.session.commit()

        # Create sample user
        user = User(
            username='demo_user',
            email='demo@example.com'
        )
        user.set_password('demo123')  # Password will be 'demo123'
        db.session.add(user)
        db.session.commit()

        # Create sample properties
        properties = [
            Property(
                name='Sunset Apartments 101',
                address='123 Sunset Blvd, Los Angeles, CA 90001',
                type='apartment',
                status='occupied',
                rent_amount=2000.00,
                owner_id=user.id
            ),
            Property(
                name='Ocean View House',
                address='456 Beach Road, Miami, FL 33101',
                type='house',
                status='occupied',
                rent_amount=3500.00,
                owner_id=user.id
            ),
            Property(
                name='Mountain Condo',
                address='789 Pine Street, Denver, CO 80201',
                type='condo',
                status='vacant',
                rent_amount=1800.00,
                owner_id=user.id
            )
        ]
        for prop in properties:
            db.session.add(prop)
        db.session.commit()

        # Create sample tenants
        tenants = [
            Tenant(
                name='John Smith',
                email='john@example.com',
                phone='555-0101',
                property_id=properties[0].id,
                lease_start=datetime.now().date(),
                lease_end=(datetime.now() + timedelta(days=365)).date()
            ),
            Tenant(
                name='Sarah Johnson',
                email='sarah@example.com',
                phone='555-0102',
                property_id=properties[1].id,
                lease_start=datetime.now().date(),
                lease_end=(datetime.now() + timedelta(days=730)).date()
            )
        ]
        for tenant in tenants:
            db.session.add(tenant)
        db.session.commit()

        # Create sample maintenance requests
        requests = [
            MaintenanceRequest(
                property_id=properties[0].id,
                tenant_id=tenants[0].id,
                title='Kitchen Faucet Issue',
                description='Leaking faucet in kitchen needs immediate attention',
                status='pending',
                priority='medium',
                created_at=datetime.now()
            ),
            MaintenanceRequest(
                property_id=properties[1].id,
                tenant_id=tenants[1].id,
                title='AC Malfunction',
                description='AC not working properly, temperature control issues',
                status='in_progress',
                priority='high',
                created_at=datetime.now() - timedelta(days=2)
            )
        ]
        for request in requests:
            db.session.add(request)
        db.session.commit()

        # Create sample rent payments
        payments = [
            RentPayment(
                tenant_id=tenants[0].id,
                amount=2000.00,
                payment_date=datetime.now().date(),
                status='paid'
            ),
            RentPayment(
                tenant_id=tenants[1].id,
                amount=3500.00,
                payment_date=datetime.now().date() - timedelta(days=5),
                status='paid'
            ),
            RentPayment(
                tenant_id=tenants[0].id,
                amount=2100.00,  # Including late fee
                payment_date=datetime.now().date() - timedelta(days=35),
                status='late'
            )
        ]
        for payment in payments:
            db.session.add(payment)
        db.session.commit()

        print("Sample data added successfully!")
        print("\nLogin credentials:")
        print("Username: demo_user")
        print("Password: demo123")

if __name__ == '__main__':
    add_sample_data() 