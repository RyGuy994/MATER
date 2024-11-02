/* src/components/SettingsLocal.jsx */

import React, { useEffect, useState } from 'react';
import './settingsShared.css';
import '../common/common.css';
import DeleteModal from '../common/DeleteModal';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const SettingsLocal = () => {
  const [settings, setSettings] = useState([]);
  const [error, setError] = useState('');
  const [editMode, setEditMode] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false); // Modal visibility state
  const [settingToDelete, setSettingToDelete] = useState(null); // Store the ID of the setting to delete
  const [editValue, setEditValue] = useState('');
  const [newSetting, setNewSetting] = useState({ whatfor: 'service_status', value: '', globalsetting: false });
  const baseUrl = import.meta.env.VITE_BASE_URL; // Use your base URL

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const settingUrl = `${baseUrl}/settings/appsettings/local`;
        const jwtToken = localStorage.getItem('jwt'); // Retrieve JWT from local storage

        if (!jwtToken) {
          setError('JWT token is missing');
          return;
        }

        console.log('Fetching settings with JWT:', jwtToken);

        const response = await fetch(settingUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            jwt: jwtToken // Include JWT token in the body
          }),
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

    fetchSettings();
  }, [baseUrl]);

  const handleToggle = async (settingId, currentValue) => {
    const newValue = currentValue === 'Yes' ? 'No' : 'Yes';
    try {
      const updateUrl = `${baseUrl}/settings/appsettings/update`;
      const response = await fetch(updateUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
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
    try {
      const updateUrl = `${baseUrl}/settings/appsettings/update`;
      const response = await fetch(updateUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
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

  // Add the handleDelete function to show the modal
  const handleDelete = (settingId) => {
    setSettingToDelete(settingId); // Set the setting ID for deletion
    setShowDeleteModal(true); // Show the delete confirmation modal
  };

  const confirmDelete = async () => {
    setShowDeleteModal(false); // Close the modal
    try {
      const jwtToken = localStorage.getItem('jwt');
      const deleteUrl = `${baseUrl}/settings/appsettings/delete/${settingToDelete}`;

      const response = await fetch(deleteUrl, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${jwtToken}`
        },
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
    try {
      const jwtToken = localStorage.getItem('jwt'); // Retrieve JWT from local storage

      if (!jwtToken) {
        setError('JWT token is missing');
        toast.error('JWT token is missing');
        return;
      }

      const addUrl = `${baseUrl}/settings/appsettings/add`;
      console.log('Adding new setting with JWT:', jwtToken);

      const response = await fetch(addUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...newSetting, jwt: jwtToken }),
      });

      if (response.ok) {
        const newAddedSetting = await response.json();
        setSettings([...settings, newAddedSetting]);
        setNewSetting({ whatfor: 'service_status', value: '', globalsetting: false });
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
      <h1>Local Settings Page</h1>
      {error && <div className="error">{error}</div>}
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
                {['service_status', 'asset_status','service_type'].includes(setting.whatfor) && (
                  <>
                    {editMode === setting.id ? (
                      <>
                        <button className="standard-btn" onClick={() => handleEdit(setting.id)}>Save</button>
                        <button className="standard-btn" onClick={() => { setEditMode(null); setEditValue(''); }}>Cancel</button>
                      </>
                    ) : (
                      <>
                        <button className="standard-btn" onClick={() => { setEditMode(setting.id); setEditValue(setting.value); }}>Edit</button>
                        <button className="standard-del-btn" onClick={() => handleDelete(setting.id)}>Delete</button> {/* Call handleDelete here */}
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
        onClose={() => setShowDeleteModal(false)} // Close modal on cancel
        onConfirm={confirmDelete} // Confirm delete on modal confirm button
      />
      <ToastContainer />
    </div>
  );
};

export default SettingsLocal;
