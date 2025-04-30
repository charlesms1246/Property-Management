from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import MaintenanceRequest, Property
from datetime import datetime

bp = Blueprint('maintenance', __name__)

@bp.route('/maintenance/<int:request_id>')
@login_required
def view_request(request_id):
    request = db.session.query(MaintenanceRequest).join(Property).filter(
        MaintenanceRequest.id == request_id,
        Property.owner_id == current_user.id
    ).first_or_404()
    
    return render_template('maintenance/view.html', request=request)

@bp.route('/maintenance/<int:request_id>/update', methods=['POST'])
@login_required
def update_request(request_id):
    request = db.session.query(MaintenanceRequest).join(Property).filter(
        MaintenanceRequest.id == request_id,
        Property.owner_id == current_user.id
    ).first_or_404()
    
    request.status = request.form.get('status')
    request.notes = request.form.get('notes')
    db.session.commit()
    
    flash('Maintenance request updated successfully', 'success')
    return redirect(url_for('maintenance.view_request', request_id=request_id)) 