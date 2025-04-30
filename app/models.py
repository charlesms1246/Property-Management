from app import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    properties = db.relationship('Property', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # apartment, house, commercial
    status = db.Column(db.String(20), nullable=False)  # vacant, occupied, maintenance
    rent_amount = db.Column(db.Float, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tenants = db.relationship('Tenant', backref='property', lazy=True)
    maintenance_requests = db.relationship('MaintenanceRequest', backref='property', lazy=True)

class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    lease_start = db.Column(db.Date, nullable=False)
    lease_end = db.Column(db.Date, nullable=False)
    rent_payments = db.relationship('RentPayment', backref='tenant', lazy=True)
    maintenance_requests = db.relationship('MaintenanceRequest', backref='tenant', lazy=True)

    def calculate_late_fee(self, days_late):
        """Calculate late fee based on rent amount and days late"""
        return self.property.rent_amount * 0.05 * days_late

class MaintenanceRequest(db.Model):
    __tablename__ = 'maintenance_requests'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # pending, in_progress, completed
    priority = db.Column(db.String(20), nullable=False)  # low, medium, high
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<MaintenanceRequest {self.title}>'

class RentPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # paid, pending, late

def init_db():
    """Initialize database with views, triggers, and functions"""
    try:
        # First create all tables
        db.create_all()
        
        # Create a view for property financial summary
        db.session.execute(text("""
        DROP VIEW IF EXISTS property_financial_summary;
        """))
        db.session.execute(text("""
        CREATE VIEW property_financial_summary AS
        SELECT 
            p.id as property_id,
            p.name as property_name,
            p.rent_amount,
            COUNT(t.id) as total_tenants,
            SUM(CASE WHEN rp.status = 'paid' THEN rp.amount ELSE 0 END) as total_paid,
            COUNT(CASE WHEN rp.status = 'late' THEN 1 END) as late_payments
        FROM property p
        LEFT JOIN tenant t ON p.id = t.property_id
        LEFT JOIN rent_payment rp ON t.id = rp.tenant_id
        GROUP BY p.id, p.name, p.rent_amount;
        """))

        # Create a trigger to update property status when tenant moves in/out
        db.session.execute(text("""
        DROP TRIGGER IF EXISTS update_property_status;
        """))
        db.session.execute(text("""
        CREATE TRIGGER update_property_status
        AFTER INSERT ON tenant
        BEGIN
            UPDATE property
            SET status = 'occupied'
            WHERE id = NEW.property_id;
        END;
        """))

        # Create indexes for better performance
        db.session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_property_status ON property(status);
        """))
        db.session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_tenant_property ON tenant(property_id);
        """))
        db.session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_rent_payment_date ON rent_payment(payment_date);
        """))

        db.session.commit()
        print("Database initialized successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing database: {str(e)}")
        raise 