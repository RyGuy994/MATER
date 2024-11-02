import React, { useEffect, useState } from 'react';
import './settingsShared.css';
import '../common/common.css';
import DeleteModal from '../common/DeleteModal';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const SettingsGlobal = () => {
  const [settings, setSettings] = useState([]);
  const [error, setError] = useState('');
  const [editMode, setEditMode] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [settingToDelete, setSettingToDelete] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [newSetting, setNewSetting] = useState({ whatfor: 'service_status', value: '', globalsetting: true });
  const [tables, setTables] = useState([]); // State to hold tables list
  const [selectedTables, setSelectedTables] = useState([]); // State for selected tables
  const baseUrl = import.meta.env.VITE_BASE_URL;

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const settingUrl = `${baseUrl}/settings/appsettings`;
        const jwtToken = localStorage.getItem('jwt');

        if (!jwtToken) {
          setError('JWT token is missing');
          return;
        }

        const response = await fetch(settingUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ jwt: jwtToken }), // Send the JWT in the body
        });

        if (response.ok) {
          const data = await response.json();
          setSettings(data);
        } else {
          const errMessage = await response.json();
          setError(`Failed to fetch settings: ${errMessage.error}`);
        }
      } catch (err) {
        setError('An error occurred');
      }
    };

    const fetchTables = async () => {
      try {
        const tablesUrl = `${baseUrl}/get_tables`;
        const jwtToken = localStorage.getItem('jwt');

        const response = await fetch(tablesUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ jwt: jwtToken }),
        });

        if (response.ok) {
          const data = await response.json();
          setTables(data.tables);
        } else {
          toast.error('Failed to fetch tables');
        }
      } catch (err) {
        toast.error('An error occurred while fetching tables');
      }
    };

    fetchSettings();
    fetchTables();
  }, [baseUrl]);

  const handleTableSelection = (tableName) => {
    setSelectedTables((prevSelectedTables) =>
      prevSelectedTables.includes(tableName)
        ? prevSelectedTables.filter((table) => table !== tableName)
        : [...prevSelectedTables, tableName]
    );
  };

  const handleExport = async () => {
    if (selectedTables.length === 0) {
      toast.error('No tables selected for export');
      return;
    }

    try {
      const exportUrl = `${baseUrl}/export_tables`;
      const jwtToken = localStorage.getItem('jwt');

      const response = await fetch(exportUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jwt: jwtToken,
          tables: selectedTables, // Send selected tables to backend
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'exported_tables.zip';
        link.click();
        toast.success('Tables exported successfully');
      } else {
        toast.error('Failed to export tables');
      }
    } catch (err) {
      toast.error('An error occurred during export');
    }
  };

  const handleToggle = async (settingId, currentValue) => {
    const newValue = currentValue === 'Yes' ? 'No' : 'Yes';
    const jwtToken = localStorage.getItem('jwt');

    try {
      const updateUrl = `${baseUrl}/settings/appsettings/update`;
      const response = await fetch(updateUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jwt: jwtToken, // Include JWT in the body
          id: settingId,
          value: newValue
        }),
      });

      if (response.ok) {
        setSettings(prevSettings =>
          prevSettings.map(setting =>
            setting.id === settingId ? { ...setting, value: newValue } : setting
          )
        );
        toast.success('Setting updated successfully');
      } else {
        const errMessage = await response.json();
        setError(`Failed to update setting: ${errMessage.error}`);
        toast.error(`Failed to update setting: ${errMessage.error}`);
      }
    } catch (err) {
      setError('An error occurred');
      toast.error('An error occurred');
    }
  };

  const handleEdit = async (settingId) => {
    const jwtToken = localStorage.getItem('jwt');

    try {
      const updateUrl = `${baseUrl}/settings/appsettings/update`;
      const response = await fetch(updateUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jwt: jwtToken, // Include JWT in the body
          id: settingId,
          value: editValue
        }),
      });

      if (response.ok) {
        setSettings(prevSettings =>
          prevSettings.map(setting =>
            setting.id === settingId ? { ...setting, value: editValue } : setting
          )
        );
        setEditMode(null);
        setEditValue('');
        toast.success('Setting updated successfully');
      } else {
        const errMessage = await response.json();
        setError(`Failed to update setting: ${errMessage.error}`);
        toast.error(`Failed to update setting: ${errMessage.error}`);
      }
    } catch (err) {
      setError('An error occurred');
      toast.error('An error occurred');
    }
  };

  const handleDelete = (settingId) => {
    setSettingToDelete(settingId);
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    setShowDeleteModal(false);
    const jwtToken = localStorage.getItem('jwt');

    try {
      const deleteUrl = `${baseUrl}/settings/appsettings/delete/${settingToDelete}`;
      const response = await fetch(deleteUrl, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ jwt: jwtToken }), // Include JWT in the body
      });

      if (response.ok) {
        setSettings(prevSettings => prevSettings.filter(setting => setting.id !== settingToDelete));
        toast.success('Setting deleted successfully');
      } else {
        const errMessage = await response.json();
        setError(`Failed to delete setting: ${errMessage.error}`);
        toast.error(`Failed to delete setting: ${errMessage.error}`);
      }
    } catch (err) {
      setError('An error occurred');
      toast.error('An error occurred');
    }
  };

  const handleAddSetting = async (e) => {
    e.preventDefault();
    const jwtToken = localStorage.getItem('jwt');

    if (!jwtToken) {
      setError('JWT token is missing');
      toast.error('JWT token is missing');
      return;
    }

    try {
      const addUrl = `${baseUrl}/settings/appsettings/add`;
      const response = await fetch(addUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jwt: jwtToken, // Include JWT in the body
          ...newSetting
        }),
      });

      if (response.ok) {
        const newAddedSetting = await response.json();
        setSettings([...settings, newAddedSetting]);
        setNewSetting({ whatfor: 'service_status', value: '', globalsetting: true });
        toast.success('Setting added successfully');
      } else {
        const errMessage = await response.json();
        setError(`Failed to add setting: ${errMessage.error}`);
        toast.error(`Failed to add setting: ${errMessage.error}`);
      }
    } catch (err) {
      setError('An error occurred');
      toast.error('An error occurred');
    }
  };

  return (
    <div className="scrollable-container">
      <h1>Global Settings Page</h1>
      {error && <div className="error">{error}</div>}
      {/* Table export section */}
      <div className="export-section">
        <h2>Export Tables to CSV</h2>
        {tables.length === 0 ? (
          <p>No tables available for export</p>
        ) : (
          <div className="table-list">
            {tables.map((table, index) => (
              <div key={index}>
                <label>
                  <input
                    type="checkbox"
                    checked={selectedTables.includes(table)}
                    onChange={() => handleTableSelection(table)}
                  />
                  {table}
                </label>
              </div>
            ))}
          </div>
        )}
        <button className="standard-btn" onClick={handleExport}>
          Export Selected Tables
        </button>
      </div>

      <form onSubmit={handleAddSetting} className="add-setting-form">
        <label>
          Setting Type:
          <select
            value={newSetting.whatfor}
            onChange={(e) => setNewSetting({ ...newSetting, whatfor: e.target.value })}
          >
            <option value="service_status">Service Status</option>
            <option value="service_type">Service Type</option>
            <option value="asset_status">Asset Status</option>
          </select>
        </label>
        <label>
          Value:
          <input
            type="text"
            value={newSetting.value}
            onChange={(e) => setNewSetting({ ...newSetting, value: e.target.value })}
          />
        </label>
        <button className="standard-btn" type="submit">Add Setting</button>
      </form>
      <table>
  <thead>
    <tr>
      <th>Setting</th>
      <th>Value</th>
      <th>Global Setting</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody>
    {settings.map(setting => (
      <tr key={setting.id}>
        <td>{setting.whatfor}</td>
        <td>
          {editMode === setting.id ? (
            <input
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
            />
          ) : (
            <span>
              {['allowselfregister', 'global_service_status', 'global_asset_status', 'global_service_type'].includes(setting.whatfor) ? (
                <label className="switch">
                  <input 
                    type="checkbox" 
                    checked={setting.value === 'Yes'} 
                    onChange={() => handleToggle(setting.id, setting.value)} 
                  />
                  <span className="slider round"></span>
                </label>
              ) : (
                setting.value
              )}
            </span>
          )}
        </td>
        <td>
          {/* Displaying the global setting status */}
          {setting.globalsetting ? 'Yes' : 'No'}
        </td>
        <td>
          {['service_status', 'asset_status', 'service_type'].includes(setting.whatfor) && (
            <>
              {editMode === setting.id ? (
                <>
                  <button className="standard-btn" onClick={() => handleEdit(setting.id)}>Save</button>
                  <button className="standard-btn" onClick={() => { setEditMode(null); setEditValue(''); }}>Cancel</button>
                </>
              ) : (
                <>
                  <button className="standard-btn" onClick={() => { setEditMode(setting.id); setEditValue(setting.value); }}>Edit</button>
                  <button className="standard-del-btn" onClick={() => handleDelete(setting.id)}>Delete</button>
                </>
              )}
            </>
          )}
        </td>
      </tr>
    ))}
  </tbody>
</table>
      <DeleteModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={confirmDelete}
      />
      <ToastContainer />
    </div>
  );
};

export default SettingsGlobal;
