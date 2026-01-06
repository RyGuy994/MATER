import { useState, useEffect } from 'react';
import { assetApi } from '../api/assetApi';

export const useTemplates = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const data = await assetApi.listTemplates();
      setTemplates(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const createTemplate = async (templateData) => {
    try {
      const newTemplate = await assetApi.createTemplate(templateData);
      setTemplates(prev => [...prev, newTemplate]);
      return newTemplate;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const updateTemplate = async (templateId, updates) => {
    try {
      const updated = await assetApi.updateTemplate(templateId, updates);
      setTemplates(prev => prev.map(t => t.id === templateId ? updated : t));
      return updated;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const deleteTemplate = async (templateId) => {
    try {
      await assetApi.deleteTemplate(templateId);
      setTemplates(prev => prev.filter(t => t.id !== templateId));
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  return {
    templates,
    loading,
    error,
    fetchTemplates,
    createTemplate,
    updateTemplate,
    deleteTemplate
  };
};
