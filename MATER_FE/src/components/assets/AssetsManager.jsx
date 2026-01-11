// filepath: MATER_FE/src/components/assets/AssetsManager.jsx
import { useState, useEffect } from 'react';
import { assetApi } from '../../features/assets/api/assetApi';
import { FieldEditor } from './FieldEditor';
import { AssetForm } from './AssetForm';
import Modal from '../common/Modal';
import './AssetsManager.css';

export default function AssetsManager() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeView, setActiveView] = useState('templates');
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [showFieldEditor, setShowFieldEditor] = useState(false);
  const [editingField, setEditingField] = useState(null);

  // New Template modal state
  const [showCreateTemplateModal, setShowCreateTemplateModal] = useState(false);
  const [newTemplateName, setNewTemplateName] = useState('');
  const [newTemplateDescription, setNewTemplateDescription] = useState('');
  const [createTemplateError, setCreateTemplateError] = useState('');
  const [creatingTemplate, setCreatingTemplate] = useState(false);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await assetApi.listTemplates();
      const nextTemplates = data || [];
      setTemplates(nextTemplates);

      setSelectedTemplate((prevSelected) => {
        if (!prevSelected) return null;
        return nextTemplates.find((t) => t.id === prevSelected.id) || null;
      });
    } catch (err) {
      console.error('Error fetching templates:', err);
      setError(`Failed to load templates: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Modal open/close helpers
  const openCreateTemplateModal = () => {
    setCreateTemplateError('');
    setNewTemplateName('');
    setNewTemplateDescription('');
    setShowCreateTemplateModal(true);
  };

  const closeCreateTemplateModal = () => {
    if (creatingTemplate) return;
    setShowCreateTemplateModal(false);
  };

  const handleCreateTemplate = async (e) => {
    e?.preventDefault?.();
    setCreateTemplateError('');

    const name = newTemplateName.trim();
    if (!name) {
      setCreateTemplateError('Template name is required.');
      return;
    }

    try {
      setCreatingTemplate(true);
      const newTemplate = await assetApi.createTemplate({
        name,
        description: newTemplateDescription.trim(),
      });

      setTemplates((prev) => [...prev, newTemplate]);
      setSelectedTemplate(newTemplate);
      setShowCreateTemplateModal(false);
    } catch (err) {
      console.error('Error creating template:', err);
      setCreateTemplateError(err.message || 'Error creating template');
    } finally {
      setCreatingTemplate(false);
    }
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this template?')) return;

    try {
      await assetApi.deleteTemplate(templateId);
      setTemplates((prev) => prev.filter((t) => t.id !== templateId));
      if (selectedTemplate?.id === templateId) setSelectedTemplate(null);
    } catch (err) {
      console.error('Error deleting template:', err);
      alert('Error deleting template: ' + err.message);
    }
  };

  const handleDeleteField = async (fieldId) => {
    if (!selectedTemplate) return;
    if (!window.confirm('Are you sure you want to delete this field?')) return;

    try {
      await assetApi.deleteField(selectedTemplate.id, fieldId);
      fetchTemplates();
    } catch (err) {
      console.error('Error deleting field:', err);
      alert('Error deleting field: ' + err.message);
    }
  };

  const handleAddField = (template) => {
    setSelectedTemplate(template);
    setEditingField(null);
    setShowFieldEditor(true);
  };

  const handleEditField = (field) => {
    if (!selectedTemplate) return;
    setEditingField(field);
    setShowFieldEditor(true);
  };

  const handleFieldSaved = () => {
    setShowFieldEditor(false);
    setEditingField(null);
    fetchTemplates();
  };

  const closeFieldEditor = () => {
    setShowFieldEditor(false);
    setEditingField(null);
  };

  if (loading) {
    return (
      <div className="assets-manager loading">
        <div className="spinner"></div>
        <p>Loading templates...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="assets-manager error">
        <div className="error-box">
          <h3>Error</h3>
          <p>{error}</p>
          <button className="btn-primary" onClick={fetchTemplates}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="assets-manager">
      <div className="view-tabs">
        <button
          className={`tab ${activeView === 'templates' ? 'active' : ''}`}
          onClick={() => setActiveView('templates')}
        >
          Asset Templates
        </button>
        <button
          className={`tab ${activeView === 'assets' ? 'active' : ''}`}
          onClick={() => setActiveView('assets')}
        >
          Assets
        </button>
      </div>

      {activeView === 'templates' && (
        <div className="templates-section">
          <div className="section-header">
            <button className="btn-primary" onClick={openCreateTemplateModal}>
              + New Template
            </button>
          </div>

          {templates.length === 0 ? (
            <div className="empty-state">
              <p>No templates yet. Create one to get started!</p>
              <button className="btn-primary" onClick={openCreateTemplateModal}>
                Create First Template
              </button>
            </div>
          ) : (
            <div className="templates-grid">
              {templates.map((template) => (
                <div
                  key={template.id}
                  className={`template-card ${selectedTemplate?.id === template.id ? 'selected' : ''}`}
                  onClick={() => setSelectedTemplate(template)}
                >
                  <h3>{template.name}</h3>
                  <p>{template.description || 'No description'}</p>
                  <div className="template-meta">
                    <span>{template.fields?.length || 0} fields</span>
                  </div>

                  <div className="template-actions">
                    <button
                      className="btn-primary btn-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAddField(template);
                      }}
                    >
                      + Add Field
                    </button>

                    <button
                      className="btn-danger btn-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteTemplate(template.id);
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Create Template Modal (reusable Modal) */}
          <Modal
            open={showCreateTemplateModal}
            title="Create template"
            onClose={closeCreateTemplateModal}
          >
            {createTemplateError && (
              <p className="error-message" style={{ marginTop: '0.5rem' }}>
                {createTemplateError}
              </p>
            )}

            <form
              onSubmit={handleCreateTemplate}
              style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <label style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  <span>Name:</span>
                  <input
                    type="text"
                    value={newTemplateName}
                    onChange={(e) => setNewTemplateName(e.target.value)}
                    placeholder="e.g. Laptop"
                    autoFocus
                  />
                </label>

                <label style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  <span>Description (optional):</span>
                  <input
                    type="text"
                    value={newTemplateDescription}
                    onChange={(e) => setNewTemplateDescription(e.target.value)}
                    placeholder="Short description"
                  />
                </label>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={closeCreateTemplateModal}
                  disabled={creatingTemplate}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={creatingTemplate}>
                  {creatingTemplate ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </Modal>

          {/* Field Editor Modal (reusable Modal) */}
          <Modal
            open={showFieldEditor && !!selectedTemplate}
            title={editingField ? 'Edit field' : 'Add field'}
            onClose={closeFieldEditor}
          >
            {selectedTemplate && (
              <FieldEditor
                templateId={selectedTemplate.id}
                field={editingField}
                onSave={handleFieldSaved}
                onCancel={closeFieldEditor}
              />
            )}
          </Modal>

          {selectedTemplate && (
            <div className="fields-section">
              <h3>Template Fields: {selectedTemplate.name}</h3>

              {selectedTemplate.fields && selectedTemplate.fields.length > 0 ? (
                <div className="fields-list">
                  {selectedTemplate.fields.map((field) => (
                    <div key={field.id} className="field-item">
                      <div className="field-info">
                        <h4>{field.field_label}</h4>
                        <p className="field-type">{field.field_type}</p>
                        {field.help_text && <p className="field-help">{field.help_text}</p>}
                      </div>

                      <div className="field-actions">
                        <div className="field-badges">
                          {field.is_required && <span className="badge required">Required</span>}
                          {field.field_type === 'select' && (
                            <span className="badge select">{field.options?.length || 0} options</span>
                          )}
                        </div>

                        <button className="btn-secondary btn-sm" onClick={() => handleEditField(field)}>
                          Edit
                        </button>

                        <button className="btn-danger btn-sm" onClick={() => handleDeleteField(field.id)}>
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-fields">No fields yet. Click "+ Add Field" to create one.</p>
              )}
            </div>
          )}
        </div>
      )}

      {activeView === 'assets' && (
        <div className="assets-section">
          <div className="section-header">
            {selectedTemplate && <button className="btn-primary">+ New Asset from {selectedTemplate.name}</button>}
          </div>

          {!selectedTemplate ? (
            <div className="no-selection">
              <p>Select a template from the Templates tab to create assets</p>
            </div>
          ) : (
            <div className="asset-form-wrapper">
              <AssetForm
                template={selectedTemplate}
                onSubmit={(values) => {
                  console.log('Asset values:', values);
                  alert('Asset would be saved with values: ' + JSON.stringify(values));
                }}
                onCancel={() => setSelectedTemplate(null)}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
