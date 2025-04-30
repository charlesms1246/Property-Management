from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Property, Tenant, MaintenanceRequest
from sqlalchemy import text

bp = Blueprint('properties', __name__)

@bp.route('/properties')
@login_required
def list_properties():
    properties = Property.query.filter_by(owner_id=current_user.id).all()
    return render_template('properties/list.html', properties=properties)

@bp.route('/properties/add', methods=['GET', 'POST'])
@login_required
def add_property():
    if request.method == 'POST':
        property = Property(
            name=request.form['name'],
            address=request.form['address'],
            type=request.form['type'],
            status='vacant',
            rent_amount=float(request.form['rent_amount']),
            owner_id=current_user.id
        )
        db.session.add(property)
        db.session.commit()
        flash('Property added successfully!', 'success')
        return redirect(url_for('properties.list_properties'))
    return render_template('properties/add.html')

@bp.route('/properties/<int:property_id>')
@login_required
def view_property(property_id):
    property = Property.query.get_or_404(property_id)
    if property.owner_id != current_user.id:
        flash('You do not have permission to view this property.', 'danger')
        return redirect(url_for('properties.list_properties'))
    
    # Get financial summary for the property
    financial_summary = db.session.execute(text("""
        SELECT 
            COUNT(t.id) as total_tenants,
            SUM(CASE WHEN rp.status = 'paid' THEN rp.amount ELSE 0 END) as total_paid,
            COUNT(CASE WHEN rp.status = 'late' THEN 1 END) as late_payments
        FROM property p
        LEFT JOIN tenant t ON p.id = t.property_id
        LEFT JOIN rent_payment rp ON t.id = rp.tenant_id
        WHERE p.id = :property_id
    """), {'property_id': property_id}).fetchone()
    
    # Get tenants for the property
    tenants = Tenant.query.filter_by(property_id=property_id).all()
    
    # Get maintenance requests for the property
    maintenance_requests = MaintenanceRequest.query.filter_by(
        property_id=property_id
    ).order_by(MaintenanceRequest.created_at.desc()).all()
    
    return render_template('properties/view.html',
                         property=property,
                         financial_summary=financial_summary,
                         tenants=tenants,
                         maintenance_requests=maintenance_requests)

@bp.route('/properties/<int:property_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_property(property_id):
    property = Property.query.get_or_404(property_id)
    if property.owner_id != current_user.id:
        flash('You do not have permission to edit this property.', 'danger')
        return redirect(url_for('properties.list_properties'))
    
    if request.method == 'POST':
        property.name = request.form['name']
        property.address = request.form['address']
        property.type = request.form['type']
        property.rent_amount = float(request.form['rent_amount'])
        db.session.commit()
        flash('Property updated successfully!', 'success')
        return redirect(url_for('properties.view_property', property_id=property_id))
    
    return render_template('properties/edit.html', property=property)

@bp.route('/properties/<int:property_id>/delete', methods=['POST'])
@login_required
def delete_property(property_id):
    property = Property.query.get_or_404(property_id)
    if property.owner_id != current_user.id:
        flash('You do not have permission to delete this property.', 'danger')
        return redirect(url_for('properties.list_properties'))
    
    db.session.delete(property)
    db.session.commit()
    flash('Property deleted successfully!', 'success')
    return redirect(url_for('properties.list_properties'))

@bp.route('/properties/<int:property_id>/maintenance', methods=['GET', 'POST'])
@login_required
def add_maintenance(property_id):
    property = Property.query.get_or_404(property_id)
    if property.owner_id != current_user.id:
        flash('You do not have permission to add maintenance for this property.', 'danger')
        return redirect(url_for('properties.list_properties'))
    
    if request.method == 'POST':
        # Check if tenant exists and belongs to the property
        tenant_id = request.form.get('tenant_id')
        tenant = Tenant.query.filter_by(id=tenant_id, property_id=property_id).first()
        if not tenant:
            flash('Invalid tenant selected.', 'danger')
            return redirect(url_for('properties.add_maintenance', property_id=property_id))
        
        maintenance = MaintenanceRequest(
            property_id=property_id,
            tenant_id=tenant_id,
            title=request.form['title'],
            description=request.form['description'],
            status='pending',
            priority=request.form.get('priority', 'medium')
        )
        db.session.add(maintenance)
        db.session.commit()
        flash('Maintenance request added successfully!', 'success')
        return redirect(url_for('properties.view_property', property_id=property_id))
    
    return render_template('properties/maintenance.html', property=property) 