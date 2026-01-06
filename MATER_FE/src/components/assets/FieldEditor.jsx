// filepath: MATER_FE/src/components/assets/FieldEditor.jsx
import React, { useState } from 'react';
import { assetApi } from '../../features/assets/api/assetApi';
import './FieldEditor.css';

export const FieldEditor = ({ templateId, field = null, onSave, onCancel }) => {
  const [fieldData, setFieldData] = useState(
    field || {
      field_name: '',
      field_label: '',
      field_type: 'text',
      select_type: 'single',
      is_required: false,
      display_order: 0,
      help_text: '',
      default_value: '',
      options: [],
    }
  );

  const [newOption, setNewOption] = useState({ label: '', value: '' });
  const [errors, setErrors] = useState({});

  const handleFieldChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFieldData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));

    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const handleFieldTypeChange = (e) => {
    const fieldType = e.target.value;
    setFieldData((prev) => ({
      ...prev,
      field_type: fieldType,
      ...(fieldType !== 'select' && {
        select_type: null,
        options: null,
      }),
    }));
  };

  const addOption = () => {
    if (!newOption.label.trim() || !newOption.value.trim()) {
      setErrors((prev) => ({ ...prev, options: 'Please enter both label and value' }));
      return;
    }

    const currentOptions = fieldData.options || [];

    if (currentOptions.some((opt) => opt.value === newOption.value)) {
      setErrors((prev) => ({
        ...prev,
        options: `Option with value "${newOption.value}" already exists`,
      }));
      return;
    }

    setFieldData((prev) => ({
      ...prev,
      options: [...(prev.options || []), { ...newOption }],
    }));

    setNewOption({ label: '', value: '' });
    setErrors((prev) => ({ ...prev, options: null }));
  };

  const removeOption = (index) => {
    setFieldData((prev) => ({
      ...prev,
      options: prev.options.filter((_, i) => i !== index),
    }));
  };

  const updateOption = (index, optionField, value) => {
    setFieldData((prev) => ({
      ...prev,
      options: prev.options.map((opt, i) => (i === index ? { ...opt, [optionField]: value } : opt)),
    }));
  };

  const validateForm = () => {
    const newErrors = {};

    if (!fieldData.field_name?.trim()) newErrors.field_name = 'Field name is required';
    if (!fieldData.field_label?.trim()) newErrors.field_label = 'Field label is required';
    if (!fieldData.field_type) newErrors.field_type = 'Field type is required';

    if (fieldData.field_type === 'select') {
      if (!fieldData.select_type) newErrors.select_type = 'Please select single or multi-select';
      if (!fieldData.options || fieldData.options.length === 0) {
        newErrors.options = 'Select fields must have at least one option';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) return;

    try {
      setErrors((prev) => ({ ...prev, submit: null }));

      const saved = field
        ? await assetApi.updateField(templateId, field.id, fieldData)
        : await assetApi.createField(templateId, fieldData);

      onSave(saved);
    } catch (err) {
      setErrors((prev) => ({ ...prev, submit: `Error saving field: ${err.message}` }));
    }
  };

  return (
    <div className="field-editor">
      <h3>{field ? 'Edit Field' : 'Create New Field'}</h3>

      {errors.submit && <div className="error-message">{errors.submit}</div>}

      <div className="form-group">
        <label>Field Name (identifier)</label>
        <input
          type="text"
          name="field_name"
          value={fieldData.field_name || ''}
          onChange={handleFieldChange}
          placeholder="e.g., status, color, priority"
          disabled={!!field}
          className={errors.field_name ? 'error' : ''}
        />
        {errors.field_name && <span className="error-text">{errors.field_name}</span>}
      </div>

      <div className="form-group">
        <label>Field Label (display name)</label>
        <input
          type="text"
          name="field_label"
          value={fieldData.field_label || ''}
          onChange={handleFieldChange}
          placeholder="e.g., Equipment Status, Color, Priority"
          className={errors.field_label ? 'error' : ''}
        />
        {errors.field_label && <span className="error-text">{errors.field_label}</span>}
      </div>

      <div className="form-group">
        <label>Field Type</label>
        <select
          name="field_type"
          value={fieldData.field_type || 'text'}
          onChange={handleFieldTypeChange}
          className={errors.field_type ? 'error' : ''}
        >
          <option value="text">Text</option>
          <option value="number">Number</option>
          <option value="date">Date</option>
          <option value="currency">Currency</option>
          <option value="boolean">Boolean</option>
          <option value="select">Dropdown/Select</option>
        </select>
        {errors.field_type && <span className="error-text">{errors.field_type}</span>}
      </div>

      <div className="form-group checkbox">
        <label>
          <input
            type="checkbox"
            name="is_required"
            checked={!!fieldData.is_required}
            onChange={handleFieldChange}
          />
          <span>Required field</span>
        </label>
      </div>

      <div className="form-group">
        <label>Display Order</label>
        <input
          type="number"
          name="display_order"
          value={fieldData.display_order ?? 0}
          onChange={handleFieldChange}
        />
      </div>

      <div className="form-group">
        <label>Help Text</label>
        <textarea
          name="help_text"
          value={fieldData.help_text || ''}
          onChange={handleFieldChange}
          placeholder="Optional help text for users"
          rows={3}
        />
      </div>

      {fieldData.field_type === 'select' && (
        <div className="select-options-section">
          <h4>Dropdown Options</h4>

          <div className="form-group">
            <label>Selection Type</label>
            <div className="radio-group">
              <label>
                <input
                  type="radio"
                  name="select_type"
                  value="single"
                  checked={fieldData.select_type === 'single'}
                  onChange={handleFieldChange}
                />
                <span>Single Select</span>
              </label>
              <label>
                <input
                  type="radio"
                  name="select_type"
                  value="multi"
                  checked={fieldData.select_type === 'multi'}
                  onChange={handleFieldChange}
                />
                <span>Multi Select</span>
              </label>
            </div>
            {errors.select_type && <span className="error-text">{errors.select_type}</span>}
          </div>

          <div className="add-option-form">
            <input
              type="text"
              placeholder="Option Label"
              value={newOption.label}
              onChange={(e) => setNewOption((prev) => ({ ...prev, label: e.target.value }))}
            />
            <input
              type="text"
              placeholder="Option Value"
              value={newOption.value}
              onChange={(e) => setNewOption((prev) => ({ ...prev, value: e.target.value }))}
            />
            <button type="button" onClick={addOption} className="btn-secondary">
              Add Option
            </button>
          </div>

          {errors.options && <span className="error-text">{errors.options}</span>}

          {fieldData.options && fieldData.options.length > 0 && (
            <div className="options-list">
              <h5>Current Options ({fieldData.options.length})</h5>
              <ul>
                {fieldData.options.map((opt, idx) => (
                  <li key={idx} className="option-item">
                    <input
                      type="text"
                      value={opt.label}
                      onChange={(e) => updateOption(idx, 'label', e.target.value)}
                      placeholder="Label"
                    />
                    <input
                      type="text"
                      value={opt.value}
                      onChange={(e) => updateOption(idx, 'value', e.target.value)}
                      placeholder="Value"
                    />
                    <button
                      type="button"
                      onClick={() => removeOption(idx)}
                      className="btn-danger"
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="form-actions">
        <button onClick={handleSave} className="btn-primary">
          {field ? 'Update Field' : 'Create Field'}
        </button>
        <button onClick={onCancel} className="btn-secondary">
          Cancel
        </button>
      </div>
    </div>
  );
};

export default FieldEditor;
