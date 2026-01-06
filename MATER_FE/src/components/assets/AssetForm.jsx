import React, { useState } from 'react';
import './AssetForm.css';

export const AssetForm = ({ template, asset = null, onSubmit, onCancel }) => {
  const [values, setValues] = useState(asset?.template_values || {});
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (fieldName, value) => {
    setValues(prev => ({
      ...prev,
      [fieldName]: value
    }));
    if (errors[fieldName]) {
      setErrors(prev => ({ ...prev, [fieldName]: null }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    template.fields.forEach(field => {
      const value = values[field.field_name];
      
      if (field.is_required) {
        if (!value || (Array.isArray(value) && value.length === 0)) {
          newErrors[field.field_name] = `${field.field_label} is required`;
        }
      }

      if (field.field_type === 'select' && value) {
        const validValues = field.options?.map(opt => opt.value) || [];
        
        if (field.select_type === 'single') {
          if (!validValues.includes(value)) {
            newErrors[field.field_name] = `Invalid ${field.field_label}`;
          }
        } else if (field.select_type === 'multi') {
          if (Array.isArray(value)) {
            const invalidValues = value.filter(v => !validValues.includes(v));
            if (invalidValues.length > 0) {
              newErrors[field.field_name] = `Invalid option(s) in ${field.field_label}`;
            }
          }
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) return;

    setIsSubmitting(true);

    try {
      onSubmit(values);
    } catch (err) {
      setErrors(prev => ({ ...prev, submit: err.message }));
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!template || !template.fields) {
    return <div className="asset-form">Loading...</div>;
  }

  return (
    <form onSubmit={handleSubmit} className="asset-form">
      {errors.submit && <div className="error-message">{errors.submit}</div>}

      {template.fields.map(field => (
        <div key={field.id} className="form-field">
          <label htmlFor={field.field_name}>
            {field.field_label}
            {field.is_required && <span className="required">*</span>}
          </label>

          {field.field_type === 'select' ? (
            field.select_type === 'single' ? (
              <select
                id={field.field_name}
                value={values[field.field_name] || ''}
                onChange={(e) => handleChange(field.field_name, e.target.value)}
                className={errors[field.field_name] ? 'error' : ''}
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
                  <label key={opt.value} className="checkbox-label">
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
                    <span>{opt.label}</span>
                  </label>
                ))}
              </div>
            )
          ) : field.field_type === 'text' ? (
            <input
              id={field.field_name}
              type="text"
              value={values[field.field_name] || ''}
              onChange={(e) => handleChange(field.field_name, e.target.value)}
              className={errors[field.field_name] ? 'error' : ''}
            />
          ) : field.field_type === 'number' ? (
            <input
              id={field.field_name}
              type="number"
              value={values[field.field_name] || ''}
              onChange={(e) => handleChange(field.field_name, e.target.value)}
              className={errors[field.field_name] ? 'error' : ''}
            />
          ) : field.field_type === 'date' ? (
            <input
              id={field.field_name}
              type="date"
              value={values[field.field_name] || ''}
              onChange={(e) => handleChange(field.field_name, e.target.value)}
              className={errors[field.field_name] ? 'error' : ''}
            />
          ) : field.field_type === 'currency' ? (
            <input
              id={field.field_name}
              type="number"
              step="0.01"
              value={values[field.field_name] || ''}
              onChange={(e) => handleChange(field.field_name, e.target.value)}
              className={errors[field.field_name] ? 'error' : ''}
            />
          ) : field.field_type === 'boolean' ? (
            <input
              id={field.field_name}
              type="checkbox"
              checked={values[field.field_name] || false}
              onChange={(e) => handleChange(field.field_name, e.target.checked)}
            />
          ) : null}

          {field.help_text && <small className="help-text">{field.help_text}</small>}
          {errors[field.field_name] && <span className="error-text">{errors[field.field_name]}</span>}
        </div>
      ))}

      <div className="form-actions">
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : 'Save Asset'}
        </button>
        <button type="button" onClick={onCancel} className="btn-secondary">
          Cancel
        </button>
      </div>
    </form>
  );
};

export default AssetForm;
