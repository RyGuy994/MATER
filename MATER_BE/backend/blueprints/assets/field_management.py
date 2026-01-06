# filepath: backend/blueprints/assets/field_management.py
"""
Template Field Management Routes

Provides endpoints for creating, updating, and managing field definitions
within asset templates, including dropdown/select field options.

Routes:
    POST   /api/asset-templates/<template_id>/fields - Create field
    GET    /api/asset-templates/<template_id>/fields - List template fields
    GET    /api/asset-templates/<template_id>/fields/<field_id> - Get field
    PUT    /api/asset-templates/<template_id>/fields/<field_id> - Update field
    DELETE /api/asset-templates/<template_id>/fields/<field_id> - Delete field
    PUT    /api/asset-templates/<template_id>/fields/<field_id>/options - Update options
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import and_

from backend.models.asset_template import AssetTemplate, TemplateField
from backend.models.db import db
from backend.models.user import User

from backend.helpers.asset_permissions import (
    get_current_user_from_request,
    check_template_permission,
)
from backend.helpers.asset_validation import validate_select_field_definition

bp = Blueprint("field_management", __name__)


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_select_field(data):
    """
    Validate a select field definition.
    
    Args:
        data: Field data dictionary
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if data.get("field_type") != "select":
        return True, None

    # Check select_type ONLY if it's provided (skip for option-only updates)
    select_type = data.get("select_type")
    if select_type is not None and select_type not in ["single", "multi"]:
        return False, "select_type must be 'single' or 'multi' for select fields"

    # Check options
    options = data.get("options", [])
    if not isinstance(options, list) or len(options) == 0:
        return False, "select fields must have at least one option"

    # Validate each option
    seen_values = set()
    for idx, opt in enumerate(options):
        if not isinstance(opt, dict):
            return False, f"Option {idx} is not a dictionary"
        
        if "label" not in opt or "value" not in opt:
            return False, f"Option {idx} missing 'label' or 'value' key"
        
        if not isinstance(opt["label"], str) or not opt["label"].strip():
            return False, f"Option {idx} has empty or non-string label"
        
        if not isinstance(opt["value"], str) or not opt["value"].strip():
            return False, f"Option {idx} has empty or non-string value"
        
        # Check for duplicate values
        if opt["value"] in seen_values:
            return False, f"Duplicate option value '{opt['value']}'"
        
        seen_values.add(opt["value"])

    return True, None

def validate_field_data(data, is_update=False):
    """
    Validate field creation/update data.
    
    Args:
        data: Field data dictionary
        is_update: Whether this is an update (allows partial data)
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # For creation, these are required
    if not is_update:
        if not data.get("field_name"):
            return False, "field_name is required"
        if not data.get("field_label"):
            return False, "field_label is required"
        if not data.get("field_type"):
            return False, "field_type is required"

    # Validate field_name format (alphanumeric + underscores)
    if "field_name" in data:
        field_name = data["field_name"]
        if not field_name.replace("_", "").isalnum():
            return False, "field_name must be alphanumeric with underscores only"

    # Validate field_type
    if "field_type" in data:
        valid_types = ["text", "number", "date", "currency", "boolean", "select"]
        if data["field_type"] not in valid_types:
            return False, f"field_type must be one of: {', '.join(valid_types)}"

    # Validate select-specific data
    if data.get("field_type") == "select" or (is_update and "select_type" in data):
        is_valid, error = validate_select_field(data)
        if not is_valid:
            return False, error

    return True, None


# ============================================================================
# FIELD CRUD ENDPOINTS
# ============================================================================

@bp.route("/asset-templates/<template_id>/fields", methods=["POST"])
def create_field(template_id):
    """
    Create a new field in a template.
    
    JSON Request Body:
    {
        "field_name": "status",
        "field_label": "Equipment Status",
        "field_type": "select",
        "select_type": "single",
        "is_required": true,
        "display_order": 1,
        "help_text": "Current operational status",
        "default_value": "operational",
        "options": [
            {"label": "Operational", "value": "operational"},
            {"label": "Maintenance", "value": "maintenance"}
        ]
    }
    """
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Check template exists and user has permission
    template = AssetTemplate.query.get(template_id)
    if not template or template.is_deleted:
        return jsonify({"error": "Template not found"}), 404

    ok, reason = check_template_permission(template_id, user_id, "editor")
    if not ok:
        return jsonify({"error": reason}), 403

    if template.is_locked:
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({"error": "Template is locked"}), 403

    data = request.get_json() or {}

    # Validate field data
    is_valid, error = validate_field_data(data, is_update=False)
    if not is_valid:
        return jsonify({"error": error}), 400

    # Check for duplicate field names within this template
    existing = TemplateField.query.filter(
        and_(
            TemplateField.asset_template_id == template_id,
            TemplateField.field_name == data["field_name"]
        )
    ).first()
    if existing:
        return jsonify({"error": f"Field name '{data['field_name']}' already exists in this template"}), 400

    field = TemplateField(
        asset_template_id=template_id,
        field_name=data.get("field_name"),
        field_label=data.get("field_label"),
        field_type=data.get("field_type"),
        select_type=data.get("select_type"),  # Only used for select fields
        is_required=data.get("is_required", False),
        default_value=data.get("default_value"),
        validation_rules=data.get("validation_rules"),
        display_order=data.get("display_order", 0),
        help_text=data.get("help_text"),
        options=data.get("options")  # For select fields
    )

    db.session.add(field)
    db.session.commit()

    return jsonify(field.to_dict()), 201


@bp.route("/asset-templates/<template_id>/fields", methods=["GET"])
def list_fields(template_id):
    """List all fields in a template."""
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    ok, reason = check_template_permission(template_id, user_id, "viewer")
    if not ok:
        return jsonify({"error": reason}), 403

    template = AssetTemplate.query.get(template_id)
    if not template or template.is_deleted:
        return jsonify({"error": "Template not found"}), 404

    fields = TemplateField.query.filter(
        TemplateField.asset_template_id == template_id
    ).order_by(TemplateField.display_order).all()

    return jsonify([f.to_dict() for f in fields]), 200


@bp.route("/asset-templates/<template_id>/fields/<field_id>", methods=["GET"])
def get_field(template_id, field_id):
    """Get a specific field definition."""
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    ok, reason = check_template_permission(template_id, user_id, "viewer")
    if not ok:
        return jsonify({"error": reason}), 403

    field = TemplateField.query.filter(
        and_(
            TemplateField.id == field_id,
            TemplateField.asset_template_id == template_id
        )
    ).first()

    if not field:
        return jsonify({"error": "Field not found"}), 404

    return jsonify(field.to_dict()), 200


@bp.route("/asset-templates/<template_id>/fields/<field_id>", methods=["PUT"])
def update_field(template_id, field_id):
    """
    Update a field definition.
    
    Can update: field_label, field_type, select_type, is_required, 
    default_value, validation_rules, display_order, help_text, options
    """
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    ok, reason = check_template_permission(template_id, user_id, "editor")
    if not ok:
        return jsonify({"error": reason}), 403

    field = TemplateField.query.filter(
        and_(
            TemplateField.id == field_id,
            TemplateField.asset_template_id == template_id
        )
    ).first()

    if not field:
        return jsonify({"error": "Field not found"}), 404

    template = AssetTemplate.query.get(template_id)
    if template.is_locked:
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({"error": "Template is locked"}), 403

    data = request.get_json() or {}

    # Validate field data
    is_valid, error = validate_field_data(data, is_update=True)
    if not is_valid:
        return jsonify({"error": error}), 400

    # Update allowed fields
    if "field_label" in data:
        field.field_label = data["field_label"]
    if "field_type" in data:
        field.field_type = data["field_type"]
    if "select_type" in data:
        field.select_type = data["select_type"]
    if "is_required" in data:
        field.is_required = data["is_required"]
    if "default_value" in data:
        field.default_value = data["default_value"]
    if "validation_rules" in data:
        field.validation_rules = data["validation_rules"]
    if "display_order" in data:
        field.display_order = data["display_order"]
    if "help_text" in data:
        field.help_text = data["help_text"]
    if "options" in data:
        field.options = data["options"]

    db.session.commit()
    return jsonify(field.to_dict()), 200


@bp.route("/asset-templates/<template_id>/fields/<field_id>", methods=["DELETE"])
def delete_field(template_id, field_id):
    """Delete a field from a template."""
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    ok, reason = check_template_permission(template_id, user_id, "editor")
    if not ok:
        return jsonify({"error": reason}), 403

    field = TemplateField.query.filter(
        and_(
            TemplateField.id == field_id,
            TemplateField.asset_template_id == template_id
        )
    ).first()

    if not field:
        return jsonify({"error": "Field not found"}), 404

    if not field.is_deletable:
        return jsonify({"error": "This system field cannot be deleted"}), 403

    template = AssetTemplate.query.get(template_id)
    if template.is_locked:
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({"error": "Template is locked"}), 403

    db.session.delete(field)
    db.session.commit()

    return jsonify({"message": "Field deleted"}), 200


# ============================================================================
# DROPDOWN OPTIONS MANAGEMENT
# ============================================================================

@bp.route("/asset-templates/<template_id>/fields/<field_id>/options", methods=["PUT"])
def update_field_options(template_id, field_id):
    """
    Update options for a select field.
    
    JSON Request Body:
    {
        "options": [
            {"label": "Operational", "value": "operational"},
            {"label": "Maintenance", "value": "maintenance"},
            {"label": "Out of Service", "value": "out_of_service"}
        ]
    }
    """
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    ok, reason = check_template_permission(template_id, user_id, "editor")
    if not ok:
        return jsonify({"error": reason}), 403

    field = TemplateField.query.filter(
        and_(
            TemplateField.id == field_id,
            TemplateField.asset_template_id == template_id
        )
    ).first()

    if not field:
        return jsonify({"error": "Field not found"}), 404

    if field.field_type != "select":
        return jsonify({"error": "Only select fields can have options"}), 400

    data = request.get_json() or {}
    new_options = data.get("options", [])

    # FIX: Only validate options, not select_type
    # Create a temporary dict with field_type for validation
    validation_data = {
        "field_type": "select",
        "options": new_options
    }
    
    is_valid, error = validate_select_field(validation_data)
    if not is_valid:
        return jsonify({"error": error}), 400

    template = AssetTemplate.query.get(template_id)
    if template.is_locked:
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({"error": "Template is locked"}), 403

    field.options = new_options
    db.session.commit()

    return jsonify(field.to_dict()), 200


@bp.route("/asset-templates/<template_id>/fields/<field_id>/options", methods=["GET"])
def get_field_options(template_id, field_id):
    """Get options for a select field."""
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    ok, reason = check_template_permission(template_id, user_id, "viewer")
    if not ok:
        return jsonify({"error": reason}), 403

    field = TemplateField.query.filter(
        and_(
            TemplateField.id == field_id,
            TemplateField.asset_template_id == template_id
        )
    ).first()

    if not field:
        return jsonify({"error": "Field not found"}), 404

    if field.field_type != "select":
        return jsonify({"error": "Only select fields have options"}), 400

    return jsonify({
        "field_id": field.id,
        "field_name": field.field_name,
        "field_label": field.field_label,
        "select_type": field.select_type,
        "options": field.options or []
    }), 200
