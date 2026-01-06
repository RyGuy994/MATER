// filepath: MATER_FE/src/features/assets/api/assetApi.js
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API_BASE = `${BACKEND_URL}/api`;

const getAuthHeaders = () => {
  const token = localStorage.getItem('mater_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

const parseJsonSafe = async (res) => {
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    const message =
      (data && (data.error || data.message)) ||
      text ||
      `HTTP ${res.status} ${res.statusText}`;
    throw new Error(message);
  }

  return data;
};

export const assetApi = {
  // Template endpoints
  createTemplate: async (templateData) => {
    const res = await fetch(`${API_BASE}/asset-templates`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(templateData),
    });
    return parseJsonSafe(res);
  },

  listTemplates: async () => {
    const res = await fetch(`${API_BASE}/asset-templates`, {
      headers: getAuthHeaders(),
    });
    return parseJsonSafe(res);
  },

  getTemplate: async (templateId) => {
    const res = await fetch(`${API_BASE}/asset-templates/${templateId}`, {
      headers: getAuthHeaders(),
    });
    return parseJsonSafe(res);
  },

  updateTemplate: async (templateId, updates) => {
    const res = await fetch(`${API_BASE}/asset-templates/${templateId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(updates),
    });
    return parseJsonSafe(res);
  },

  deleteTemplate: async (templateId) => {
    const res = await fetch(`${API_BASE}/asset-templates/${templateId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    return parseJsonSafe(res);
  },

  // Field endpoints
  createField: async (templateId, fieldData) => {
    const res = await fetch(`${API_BASE}/asset-templates/${templateId}/fields`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(fieldData),
    });
    return parseJsonSafe(res);
  },

  listFields: async (templateId) => {
    const res = await fetch(`${API_BASE}/asset-templates/${templateId}/fields`, {
      headers: getAuthHeaders(),
    });
    return parseJsonSafe(res);
  },

  getField: async (templateId, fieldId) => {
    const res = await fetch(
      `${API_BASE}/asset-templates/${templateId}/fields/${fieldId}`,
      { headers: getAuthHeaders() }
    );
    return parseJsonSafe(res);
  },

  updateField: async (templateId, fieldId, updates) => {
    const res = await fetch(
      `${API_BASE}/asset-templates/${templateId}/fields/${fieldId}`,
      {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(updates),
      }
    );
    return parseJsonSafe(res);
  },

  deleteField: async (templateId, fieldId) => {
    const res = await fetch(
      `${API_BASE}/asset-templates/${templateId}/fields/${fieldId}`,
      { method: 'DELETE', headers: getAuthHeaders() }
    );
    return parseJsonSafe(res);
  },

  updateFieldOptions: async (templateId, fieldId, options) => {
    const res = await fetch(
      `${API_BASE}/asset-templates/${templateId}/fields/${fieldId}/options`,
      {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ options }),
      }
    );
    return parseJsonSafe(res);
  },

  getFieldOptions: async (templateId, fieldId) => {
    const res = await fetch(
      `${API_BASE}/asset-templates/${templateId}/fields/${fieldId}/options`,
      { headers: getAuthHeaders() }
    );
    return parseJsonSafe(res);
  },

  // Asset endpoints
  createAsset: async (assetData) => {
    const res = await fetch(`${API_BASE}/assets`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(assetData),
    });
    return parseJsonSafe(res);
  },

  listAssets: async () => {
    const res = await fetch(`${API_BASE}/assets`, {
      headers: getAuthHeaders(),
    });
    return parseJsonSafe(res);
  },

  getAsset: async (assetId) => {
    const res = await fetch(`${API_BASE}/assets/${assetId}`, {
      headers: getAuthHeaders(),
    });
    return parseJsonSafe(res);
  },

  updateAsset: async (assetId, updates) => {
    const res = await fetch(`${API_BASE}/assets/${assetId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(updates),
    });
    return parseJsonSafe(res);
  },

  deleteAsset: async (assetId) => {
    const res = await fetch(`${API_BASE}/assets/${assetId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    return parseJsonSafe(res);
  },
};
