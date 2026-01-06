import React, { useState } from 'react';

export const AssetForm = ({ template, asset = null, onSubmit, onCancel }) => {
  const [values, setValues] = useState(asset?.template_values || {});

  const handleChange = (fieldName, value) => {
    setValues(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(values);
  };

  return (
    <form onSubmit={handleSubmit}>
      {template.fields.map(field => (
        <div key={field.id} className="form-field">
          <label>{field.field_label}</label>
          {field.field_type === 'select' ? (
            field.select_type === 'single' ? (
              <select
                value={values[field.field_name] || ''}
                onChange={(e) => handleChange(field.field_name, e.target.value)}
                required={field.is_required}
              >
                <option value="">-- Select {field.field_label} --</option>
                {field.options?.map(opt => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            ) : (
              <div className="checkbox-group">
                {field.options?.map(opt => (
                  <label key={opt.value}>
                    <input
                      type="checkbox"
                      checked={(values[field.field_name] || []).includes(opt.value)}
                      onChange={(e) => {
                        const current = values[field.field_name] || [];
                        if (e.target.checked) {
                          handleChange(field.field_name, [...current, opt.value]);
                        } else {
                          handleChange(field.field_name, current.filter(v => v !== opt.value));
                        }
                      }}
                    />
                    {opt.label}
                  </label>
                ))}
              </div>
            )
          ) : field.field_type === 'text' ? (
            <input
              type="text"
              value={values[field.field_name] || ''}
              onChange={(e) => handleChange(field.field_name, e.target.value)}
              required={field.is_required}
            />
          ) : field.field_type === 'number' ? (
            <input
              type="number"
              value={values[field.field_name] || ''}
              onChange={(e) => handleChange(field.field_name, e.target.value)}
              required={field.is_required}
            />
          ) : field.field_type === 'date' ? (
            <input
              type="date"
              value={values[field.field_name] || ''}
              onChange={(e) => handleChange(field.field_name, e.target.value)}
              required={field.is_required}
            />
          ) : field.field_type === 'boolean' ? (
            <input
              type="checkbox"
              checked={values[field.field_name] || false}
              onChange={(e) => handleChange(field.field_name, e.target.checked)}
            />
          ) : null}
          {field.help_text && <small className="help-text">{field.help_text}</small>}
        </div>
      ))}

      <div className="form-actions">
        <button type="submit" className="btn-primary">Save Asset</button>
        <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>
      </div>
    </form>
  );
};
