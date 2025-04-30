from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app import db
from sqlalchemy import text, inspect
from app.models import User, Property, Tenant, MaintenanceRequest, RentPayment

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    # Get financial summary for user's properties
    financial_summary = db.session.execute(text("""
        SELECT 
            p.name as property_name,
            p.rent_amount,
            COUNT(t.id) as total_tenants,
            SUM(CASE WHEN rp.status = 'paid' THEN rp.amount ELSE 0 END) as total_paid,
            COUNT(CASE WHEN rp.status = 'late' THEN 1 END) as late_payments
        FROM property p
        LEFT JOIN tenant t ON p.id = t.property_id
        LEFT JOIN rent_payment rp ON t.id = rp.tenant_id
        WHERE p.owner_id = :user_id
        GROUP BY p.id, p.name, p.rent_amount
    """), {'user_id': current_user.id}).fetchall()
    
    # Get recent maintenance requests
    maintenance_requests = db.session.execute(text("""
        SELECT mr.*, p.name as property_name
        FROM maintenance_request mr
        JOIN property p ON mr.property_id = p.id
        WHERE p.owner_id = :user_id
        ORDER BY mr.created_at DESC
        LIMIT 5
    """), {'user_id': current_user.id}).fetchall()
    
    # Get upcoming rent payments
    upcoming_payments = db.session.execute(text("""
        SELECT rp.*, t.name as tenant_name, p.name as property_name
        FROM rent_payment rp
        JOIN tenant t ON rp.tenant_id = t.id
        JOIN property p ON t.property_id = p.id
        WHERE p.owner_id = :user_id
        AND rp.status = 'pending'
        ORDER BY rp.payment_date ASC
        LIMIT 5
    """), {'user_id': current_user.id}).fetchall()
    
    return render_template('dashboard.html',
                         financial_summary=financial_summary,
                         maintenance_requests=maintenance_requests,
                         upcoming_payments=upcoming_payments)

@bp.route('/database')
@login_required
def database_view():
    inspector = inspect(db.engine)
    tables = {}
    
    for table_name in inspector.get_table_names():
        # Get table schema
        columns = inspector.get_columns(table_name)
        schema = [[col['name'], str(col['type']), col['nullable']] for col in columns]
        
        # Get table contents
        result = db.session.execute(text(f"SELECT * FROM {table_name}"))
        rows = result.fetchall()
        
        tables[table_name] = {
            'schema': schema,
            'headers': result.keys(),
            'rows': rows
        }
    
    return render_template('main/database.html', tables=tables) 