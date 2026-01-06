import React, { useState } from 'react';

export const FieldEditor = ({ templateId, field = null, onSave, onCancel }) => {
  const [fieldData, setFieldData] = useState(field || {
    field_name: '',
    field_label: '',
    field_type: 'text',
    select_type: 'single',
    is_required: false,
    display_order: 0,
    help_text: '',
    default_value: '',
    options: []
  });

  const [newOption, setNewOption] = useState({ label: '', value: '' });

  const handleFieldChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFieldData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleFieldTypeChange = (e) => {
    const fieldType = e.target.value;
    setFieldData(prev => ({
      ...prev,
      field_type: fieldType,
      ...(fieldType !== 'select' && {
        select_type: null,
        options: null
      })
    }));
  };

  const addOption = () => {
    if (!newOption.label.trim() || !newOption.value.trim()) {
      alert('Please enter both label and value');
      return;
    }

    const currentOptions = fieldData.options || [];
    
    if (currentOptions.some(opt => opt.value === newOption.value)) {
      alert(`Option with value "${newOption.value}" already exists`);
      return;
    }

    setFieldData(prev => ({
      ...prev,
      options: [...(prev.options || []), { ...newOption }]
    }));

    setNewOption({ label: '', value: '' });
  };

  const removeOption = (index) => {
    setFieldData(prev => ({
      ...prev,
      options: prev.options.filter((_, i) => i !== index)
    }));
  };

  const updateOption = (index, field, value) => {
    setFieldData(prev => ({
      ...prev,
      options: prev.options.map((opt, i) => 
        i === index ? { ...opt, [field]: value } : opt
      )
    }));
  };

  const handleSave = async () => {
    if (!fieldData.field_name.trim()) {
      alert('Field name is required');
      return;
    }
    if (!fieldData.field_label.trim()) {
      alert('Field label is required');
      return;
    }

    if (fieldData.field_type === 'select') {
      if (!fieldData.select_type) {
        alert('Please select single or multi-select');
        return;
      }
      if (!fieldData.options || fieldData.options.length === 0) {
        alert('Select fields must have at least one option');
        return;
      }
    }

    try {
      const method = field ? 'PUT' : 'POST';
      const url = field 
        ? `/api/asset-templates/${templateId}/fields/${field.id}`
        : `/api/asset-templates/${templateId}/fields`;

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fieldData)
      });

      if (!response.ok) {
        const error = await response.json();
        alert(`Error: ${error.error}`);
        return;
      }

      onSave(await response.json());
    } catch (err) {
      alert(`Error saving field: ${err.message}`);
    }
  };

  return (
    <div className="field-editor">
      <h3>{field ? 'Edit Field' : 'Create New Field'}</h3>

      <div className="form-group">
        <label>Field Name (identifier)</label>
        <input
          type="text"
          name="field_name"
          value={fieldData.field_name}
          onChange={handleFieldChange}
          placeholder="e.g., status, color, priority"
          disabled={!!field}
        />
      </div>

      <div className="form-group">
        <label>Field Label (display name)</label>
        <input
          type="text"
          name="field_label"
          value={fieldData.field_label}
          onChange={handleFieldChange}
          placeholder="e.g., Equipment Status, Color, Priority"
        />
      </div>

      <div className="form-group">
        <label>Field Type</label>
        <select name="field_type" value={fieldData.field_type} onChange={handleFieldTypeChange}>
          <option value="text">Text</option>
          <option value="number">Number</option>
          <option value="date">Date</option>
          <option value="currency">Currency</option>
          <option value="boolean">Boolean</option>
          <option value="select">Dropdown/Select</option>
        </select>
      </div>

      <div className="form-group">
        <label>
          <input
            type="checkbox"
            name="is_required"
            checked={fieldData.is_required}
            onChange={handleFieldChange}
          />
          Required field
        </label>
      </div>

      <div className="form-group">
        <label>Display Order</label>
        <input
          type="number"
          name="display_order"
          value={fieldData.display_order}
          onChange={handleFieldChange}
        />
      </div>

      <div className="form-group">
        <label>Help Text</label>
        <textarea
          name="help_text"
          value={fieldData.help_text}
          onChange={handleFieldChange}
          placeholder="Optional help text for users"
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
                Single Select
              </label>
              <label>
                <input
                  type="radio"
                  name="select_type"
                  value="multi"
                  checked={fieldData.select_type === 'multi'}
                  onChange={handleFieldChange}
                />
                Multi Select
              </label>
            </div>
          </div>

          <div className="add-option-form">
            <input
              type="text"
              placeholder="Option Label"
              value={newOption.label}
              onChange={(e) => setNewOption(prev => ({ ...prev, label: e.target.value }))}
            />
            <input
              type="text"
              placeholder="Option Value"
              value={newOption.value}
              onChange={(e) => setNewOption(prev => ({ ...prev, value: e.target.value }))}
            />
            <button onClick={addOption}>Add Option</button>
          </div>

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
                      onClick={() => removeOption(idx)}
                      className="remove-btn"
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
