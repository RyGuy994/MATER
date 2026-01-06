# filepath: backend/helpers/asset_validation.py
"""
Asset Field Validation Helper

Provides validation utilities for asset field values against their 
template field definitions, including support for select/dropdown fields.
"""


def validate_field_value(field, value):
    """
    Validate an asset field value against its template field definition.
    
    Args:
        field: TemplateField object
        value: The value to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Handle empty values
    if value is None or value == "":
        if field.is_required:
            return False, f"Field '{field.field_label}' is required"
        return True, None

    # Validate based on field type
    if field.field_type == "text":
        return validate_text_field(field, value)
    
    elif field.field_type == "number":
        return validate_number_field(field, value)
    
    elif field.field_type == "date":
        return validate_date_field(field, value)
    
    elif field.field_type == "currency":
        return validate_currency_field(field, value)
    
    elif field.field_type == "boolean":
        return validate_boolean_field(field, value)
    
    elif field.field_type == "select":
        return validate_select_field_value(field, value)  # RENAMED
    
    else:
        return False, f"Unknown field type: {field.field_type}"


def validate_text_field(field, value):
    """Validate text field value."""
    if not isinstance(value, str):
        return False, f"Field '{field.field_label}' must be text"
    return True, None


def validate_number_field(field, value):
    """Validate number field value."""
    try:
        num = float(value) if isinstance(value, str) else value
        if not isinstance(num, (int, float)):
            return False, f"Field '{field.field_label}' must be a number"
        
        # Check validation rules (min/max)
        if field.validation_rules:
            if "min" in field.validation_rules and num < field.validation_rules["min"]:
                return False, f"Field '{field.field_label}' must be >= {field.validation_rules['min']}"
            if "max" in field.validation_rules and num > field.validation_rules["max"]:
                return False, f"Field '{field.field_label}' must be <= {field.validation_rules['max']}"
        
        return True, None
    except (ValueError, TypeError):
        return False, f"Field '{field.field_label}' must be a valid number"


def validate_date_field(field, value):
    """Validate date field value."""
    from datetime import datetime
    
    if isinstance(value, str):
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
            return True, None
        except ValueError:
            return False, f"Field '{field.field_label}' must be a valid ISO 8601 date"
    
    return False, f"Field '{field.field_label}' must be a date string"


def validate_currency_field(field, value):
    """Validate currency field value."""
    try:
        num = float(value) if isinstance(value, str) else value
        if not isinstance(num, (int, float)):
            return False, f"Field '{field.field_label}' must be a currency value"
        
        if num < 0:
            return False, f"Field '{field.field_label}' cannot be negative"
        
        return True, None
    except (ValueError, TypeError):
        return False, f"Field '{field.field_label}' must be a valid currency value"


def validate_boolean_field(field, value):
    """Validate boolean field value."""
    if isinstance(value, bool):
        return True, None
    
    if isinstance(value, str):
        if value.lower() in ["true", "1", "yes", "on"]:
            return True, None
        if value.lower() in ["false", "0", "no", "off"]:
            return True, None
    
    return False, f"Field '{field.field_label}' must be a boolean value"


# ============================================================================
# SELECT FIELD VALIDATION (Two purposes: definition validation + value validation)
# ============================================================================

def validate_select_field_definition(data):
    """
    Validate a select field DEFINITION (used when creating/updating fields).
    
    Args:
        data: Field data dictionary with field_type, select_type, options
        
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


def validate_select_field_value(field, value):
    """
    Validate a select field VALUE (used when creating/updating assets).
    
    For single-select: value must be a string matching one of the option values
    For multi-select: value must be a list of strings matching option values
    
    Args:
        field: TemplateField object
        value: The value to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not field.options:
        return False, f"Field '{field.field_label}' has no options defined"
    
    # Get valid option values
    valid_values = [opt["value"] for opt in field.options if "value" in opt]
    
    if field.select_type == "single":
        return validate_single_select(field, value, valid_values)
    
    elif field.select_type == "multi":
        return validate_multi_select(field, value, valid_values)
    
    else:
        return False, f"Field '{field.field_label}' has invalid select_type"


def validate_single_select(field, value, valid_values):
    """Validate single-select field value."""
    if not isinstance(value, str):
        return False, f"Field '{field.field_label}' (single-select) must be a string"
    
    if value not in valid_values:
        return False, f"Field '{field.field_label}' value '{value}' is not a valid option"
    
    return True, None


def validate_multi_select(field, value, valid_values):
    """Validate multi-select field value."""
    if not isinstance(value, list):
        return False, f"Field '{field.field_label}' (multi-select) must be an array"
    
    if len(value) == 0:
        if field.is_required:
            return False, f"Field '{field.field_label}' requires at least one selection"
        return True, None
    
    for item in value:
        if not isinstance(item, str):
            return False, f"Field '{field.field_label}' contains non-string value: {item}"
        if item not in valid_values:
            return False, f"Field '{field.field_label}' contains invalid option: {item}"
    
    return True, None


# ============================================================================
# ASSET VALIDATION
# ============================================================================

def validate_asset_values(template, asset_data):
    """
    Validate all asset field values against template definition.
    
    Args:
        template: AssetTemplate object
        asset_data: Dictionary of field values
        
    Returns:
        tuple: (is_valid, errors_list)
        errors_list: List of error messages for invalid fields
    """
    errors = []
    
    for field in template.fields:
        value = asset_data.get(field.field_name)
        is_valid, error = validate_field_value(field, value)
        
        if not is_valid:
            errors.append(error)
    
    return len(errors) == 0, errors


def get_field_by_name(template, field_name):
    """Get a field definition by field name."""
    from backend.models.asset_template import TemplateField
    return TemplateField.query.filter(
        TemplateField.asset_template_id == template.id,
        TemplateField.field_name == field_name
    ).first()
