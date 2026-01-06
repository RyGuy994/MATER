# backend/blueprints/assets/assets.py
"""
Asset Routes
GET /api/assets - List user's assets
POST /api/assets - Create asset
GET /api/assets/<id> - Get asset
PUT /api/assets/<id> - Update asset
DELETE /api/assets/<id> - Soft delete asset
POST /api/assets/<id>/custom-fields - Add custom field
PUT /api/assets/<id>/custom-fields/<name> - Update custom field
DELETE /api/assets/<id>/custom-fields/<name> - Delete custom field
GET /api/assets/<id>/audit - Get audit log
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, timezone
from backend.models.asset import Asset, AssetAuditLog
from backend.models.asset_template import AssetTemplate
from backend.models.db import db
from backend.helpers.asset_permissions import (
    get_current_user_from_request,
    check_asset_permission,
    log_asset_action
)

bp = Blueprint('assets', __name__)


@bp.route('/assets', methods=['GET'])
def list_assets():
    """List all assets for current user"""
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get owned assets + shared assets
    owned = Asset.query.filter_by(owner_id=user_id, is_deleted=False).all()
    
    return jsonify([a.to_dict() for a in owned]), 200


@bp.route('/assets', methods=['POST'])
def create_asset():
    """Create new asset"""
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    if not data or not data.get('asset_template_id') or not data.get('name'):
        return jsonify({'error': 'asset_template_id and name required'}), 400
    
    # Verify template exists and user has access
    template = AssetTemplate.query.get(data.get('asset_template_id'))
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    if template.owner_id != user_id and not template.is_shared_with_all:
        return jsonify({'error': 'Access denied to this template'}), 403
    
    asset = Asset(
        asset_template_id=data.get('asset_template_id'),
        owner_id=user_id,
        name=data.get('name'),
        template_values=data.get('template_values', {}),
        custom_fields=data.get('custom_fields', [])
    )
    db.session.add(asset)
    db.session.flush()
    
    # Log action
    log_asset_action(
        asset_id=asset.id,
        user_id=user_id,
        action='created',
        description=f'Created asset "{asset.name}"'
    )
    
    db.session.commit()
    return jsonify(asset.to_dict()), 201


@bp.route('/assets/<asset_id>', methods=['GET'])
def get_asset(asset_id):
    """Get asset details"""
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    asset = Asset.query.get(asset_id)
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    # Check permission
    has_access, reason = check_asset_permission(asset_id, user_id, 'viewer')
    if not has_access:
        return jsonify({'error': reason}), 403
    
    return jsonify(asset.to_dict()), 200


@bp.route('/assets/<asset_id>', methods=['PUT'])
def update_asset(asset_id):
    """Update asset"""
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    asset = Asset.query.get(asset_id)
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    # Check permission (need editor role)
    has_access, reason = check_asset_permission(asset_id, user_id, 'editor')
    if not has_access and asset.owner_id != user_id:
        return jsonify({'error': reason}), 403
    
    if asset.is_locked and asset.owner_id != user_id:
        return jsonify({'error': 'Asset is locked'}), 403
    
    data = request.get_json()
    old_values = {}
    
    # Track changes
    if 'name' in data and data['name'] != asset.name:
        old_values['name'] = asset.name
        asset.name = data['name']
    
    if 'template_values' in data:
        old_values['template_values'] = asset.template_values
        asset.template_values = data['template_values']
    
    if 'custom_fields' in data:
        old_values['custom_fields'] = asset.custom_fields
        asset.custom_fields = data['custom_fields']
    
    db.session.commit()
    
    # Log update
    changes = {k: {'old': v, 'new': data.get(k)} for k, v in old_values.items()}
    log_asset_action(
        asset_id=asset_id,
        user_id=user_id,
        action='updated',
        changes=changes if changes else None
    )
    
    return jsonify(asset.to_dict()), 200


@bp.route('/assets/<asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    """Soft delete asset"""
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    asset = Asset.query.get(asset_id)
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    if asset.owner_id != user_id:
        return jsonify({'error': 'You can only delete your own assets'}), 403
    
    asset.is_deleted = True
    asset.deleted_at = datetime.now(timezone.utc)
    db.session.commit()
    
    # Log deletion
    log_asset_action(
        asset_id=asset_id,
        user_id=user_id,
        action='deleted',
        description=f'Deleted asset "{asset.name}"'
    )
    
    return jsonify({'message': 'Asset deleted'}), 200


@bp.route('/assets/<asset_id>/custom-fields', methods=['POST'])
def add_custom_field(asset_id):
    """Add custom field to asset"""
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    asset = Asset.query.get(asset_id)
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    # Check permission
    has_access, reason = check_asset_permission(asset_id, user_id, 'editor')
    if not has_access and asset.owner_id != user_id:
        return jsonify({'error': reason}), 403
    
    data = request.get_json()
    field_name = data.get('field_name')
    field_value = data.get('field_value')
    
    if not field_name or field_value is None:
        return jsonify({'error': 'field_name and field_value required'}), 400
    
    # Initialize custom_fields if null
    if asset.custom_fields is None:
        asset.custom_fields = []
    
    # Add or update field
    found = False
    for field in asset.custom_fields:
        if field.get('field_name') == field_name:
            field['field_value'] = field_value
            found = True
            break
    
    if not found:
        asset.custom_fields.append({
            'field_name': field_name,
            'field_value': field_value
        })
    
    db.session.commit()
    
    # Log action
    log_asset_action(
        asset_id=asset_id,
        user_id=user_id,
        action='updated',
        description=f'Added custom field "{field_name}"'
    )
    
    return jsonify(asset.to_dict()), 200


@bp.route('/assets/<asset_id>/custom-fields/<field_name>', methods=['PUT'])
def update_custom_field(asset_id, field_name):
    """Update custom field"""
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    asset = Asset.query.get(asset_id)
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    # Check permission
    has_access, reason = check_asset_permission(asset_id, user_id, 'editor')
    if not has_access and asset.owner_id != user_id:
        return jsonify({'error': reason}), 403
    
    data = request.get_json()
    field_value = data.get('field_value')
    
    if asset.custom_fields:
        for field in asset.custom_fields:
            if field.get('field_name') == field_name:
                field['field_value'] = field_value
                db.session.commit()
                
                # Log action
                log_asset_action(
                    asset_id=asset_id,
                    user_id=user_id,
                    action='updated',
                    description=f'Updated custom field "{field_name}"'
                )
                
                return jsonify(asset.to_dict()), 200
    
    return jsonify({'error': 'Field not found'}), 404


@bp.route('/assets/<asset_id>/custom-fields/<field_name>', methods=['DELETE'])
def delete_custom_field(asset_id, field_name):
    """Delete custom field"""
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    asset = Asset.query.get(asset_id)
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    # Check permission
    has_access, reason = check_asset_permission(asset_id, user_id, 'editor')
    if not has_access and asset.owner_id != user_id:
        return jsonify({'error': reason}), 403
    
    if asset.custom_fields:
        asset.custom_fields = [f for f in asset.custom_fields if f.get('field_name') != field_name]
        db.session.commit()
        
        # Log action
        log_asset_action(
            asset_id=asset_id,
            user_id=user_id,
            action='updated',
            description=f'Deleted custom field "{field_name}"'
        )
        
        return jsonify(asset.to_dict()), 200
    
    return jsonify({'error': 'Field not found'}), 404


@bp.route('/assets/<asset_id>/audit', methods=['GET'])
def get_audit_log(asset_id):
    """Get asset audit log"""
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    asset = Asset.query.get(asset_id)
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    # Check permission
    has_access, reason = check_asset_permission(asset_id, user_id, 'viewer')
    if not has_access:
        return jsonify({'error': reason}), 403
    
    logs = AssetAuditLog.query.filter_by(asset_id=asset_id).order_by(AssetAuditLog.timestamp.desc()).all()
    return jsonify([log.to_dict() for log in logs]), 200
