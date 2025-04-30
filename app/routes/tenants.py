from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Tenant, Property, RentPayment
from datetime import datetime, timedelta

bp = Blueprint('tenants', __name__)

@bp.route('/tenants')
@login_required
def list_tenants():
    tenants = db.session.query(Tenant).join(Property).filter(
        Property.owner_id == current_user.id
    ).all()
    return render_template('tenants/list.html', 
                         tenants=tenants,
                         now=datetime.utcnow().date())

@bp.route('/tenants/add', methods=['GET', 'POST'])
@login_required
def add_tenant():
    if request.method == 'POST':
        property_id = request.form.get('property_id')
        property = Property.query.get(property_id)
        
        if not property or property.owner_id != current_user.id:
            flash('Invalid property')
            return redirect(url_for('tenants.add_tenant'))
        
        tenant = Tenant(
            name=request.form.get('name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            property_id=property_id,
            lease_start=datetime.strptime(request.form.get('lease_start'), '%Y-%m-%d').date(),
            lease_end=datetime.strptime(request.form.get('lease_end'), '%Y-%m-%d').date()
        )
        
        db.session.add(tenant)
        db.session.commit()
        flash('Tenant added successfully')
        return redirect(url_for('tenants.list_tenants'))
    
    properties = Property.query.filter_by(owner_id=current_user.id, status='vacant').all()
    return render_template('tenants/add.html', properties=properties)

@bp.route('/tenants/<int:tenant_id>')
@login_required
def view_tenant(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    if tenant.property.owner_id != current_user.id:
        flash('You do not have permission to view this tenant.', 'danger')
        return redirect(url_for('properties.list_properties'))
    
    return render_template('tenants/view.html', 
                         tenant=tenant,
                         now=datetime.utcnow().date())

@bp.route('/tenants/<int:tenant_id>/payment', methods=['GET', 'POST'])
@login_required
def add_payment(tenant_id):
    tenant = db.session.query(Tenant).join(Property).filter(
        Tenant.id == tenant_id,
        Property.owner_id == current_user.id
    ).first_or_404()
    
    if request.method == 'POST':
        payment_date = datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date()
        days_late = max(0, (payment_date - tenant.lease_start).days % 30 - 1)
        
        # Calculate late fee using the Python method
        late_fee = tenant.calculate_late_fee(days_late)
        
        payment = RentPayment(
            tenant_id=tenant_id,
            amount=tenant.property.rent_amount + late_fee,
            payment_date=payment_date,
            status='paid' if late_fee == 0 else 'late'
        )
        
        db.session.add(payment)
        db.session.commit()
        flash('Payment recorded successfully', 'success')
        return redirect(url_for('tenants.view_tenant', tenant_id=tenant_id))
    
    return render_template('tenants/payment.html', tenant=tenant)

@bp.route('/tenants/<int:tenant_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_tenant(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    if tenant.property.owner_id != current_user.id:
        flash('You do not have permission to edit this tenant.', 'danger')
        return redirect(url_for('tenants.list_tenants'))
    
    if request.method == 'POST':
        tenant.name = request.form.get('name')
        tenant.email = request.form.get('email')
        tenant.phone = request.form.get('phone')
        tenant.property_id = request.form.get('property_id')
        tenant.lease_start = datetime.strptime(request.form.get('lease_start'), '%Y-%m-%d').date()
        tenant.lease_end = datetime.strptime(request.form.get('lease_end'), '%Y-%m-%d').date()
        
        db.session.commit()
        flash('Tenant updated successfully', 'success')
        return redirect(url_for('tenants.view_tenant', tenant_id=tenant.id))
    
    properties = Property.query.filter_by(owner_id=current_user.id).all()
    return render_template('tenants/edit.html', 
                         tenant=tenant,
                         properties=properties)

@bp.route('/tenants/payments/<int:payment_id>')
@login_required
def view_payment(payment_id):
    payment = db.session.query(RentPayment).join(Tenant).join(Property).filter(
        RentPayment.id == payment_id,
        Property.owner_id == current_user.id
    ).first_or_404()
    
    return render_template('tenants/payment_view.html', payment=payment) 