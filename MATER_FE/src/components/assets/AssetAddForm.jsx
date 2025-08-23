/* src/components/assets/AssetAddForm.jsx */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../common/common.css';
import '../common/form.css';
import ConfirmationModal from '../common/ConfirmationModal';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import ImageDragDrop from './common/ImageDragDrop';

const AssetAddForm = ({ onClose }) => {
  // Initialize current date in YYYY-MM-DD format
  const currentDate = new Date().toISOString().split('T')[0];

  // State for asset data, image preview, and status options
  const [assetData, setAssetData] = useState({
    name: '',
    asset_sn: '',
    description: '',
    acquired_date: currentDate,
    image: null,
    asset_status: 'Ready',
  });
  const [errorMessage, setErrorMessage] = useState('');
  const [imagePreview, setImagePreview] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [statusOptions, setStatusOptions] = useState(['Ready', 'Needs Attention', 'Sold']);

  const navigate = useNavigate();

  // Fetch asset status options on component mount
  useEffect(() => {
    const fetchStatusOptions = async () => {
      try {
        const jwtToken = localStorage.getItem('jwt');
        const baseUrl = import.meta.env.VITE_BASE_URL;
        const statusUrl = `${baseUrl}/settings/appsettings/assets/status`;

        const response = await fetch(statusUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ jwt: jwtToken }),
        });

        if (response.ok) {
          const data = await response.json();
          setStatusOptions(data.map(setting => setting.value));
        } else {
          const errMessage = await response.json();
          setErrorMessage(`Failed to fetch status options: ${errMessage.error}`);
          toast.error(`Failed to fetch status options: ${errMessage.error}`);
        }
      } catch (err) {
        setErrorMessage('An error occurred while fetching status options');
        toast.error('An error occurred while fetching status options');
      }
    };

    fetchStatusOptions();
  }, []);

  // Handle changes in input fields
  const handleChange = (e) => {
    const { name, value, type } = e.target;
    const newValue = type === 'file' ? (e.target.files[0] || null) : value;
    setAssetData({ ...assetData, [name]: newValue });
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    const jwtToken = localStorage.getItem('jwt');
    const formData = new FormData();
    formData.append('name', assetData.name);
    formData.append('asset_sn', assetData.asset_sn);
    formData.append('description', assetData.description);
    formData.append('acquired_date', assetData.acquired_date);
    formData.append('asset_status', assetData.asset_status);
    formData.append('jwt', jwtToken);
    if (assetData.image) {
      formData.append('image', assetData.image);
    }

    try {
      const baseUrl = import.meta.env.VITE_BASE_URL;
      const AddAssetUrl = `${baseUrl}/assets/asset_add`;

      const response = await fetch(AddAssetUrl, {
        method: 'POST',
        body: formData,
      });

      const responseData = await response.json();

      if (response.ok) {
        toast.success(responseData.message || 'Asset added successfully');
        setShowConfirmation(true);
      } else {
        throw new Error(responseData.error || 'Failed to add asset');
      }
    } catch (error) {
      console.error('Failed to add asset:', error.message);
      setErrorMessage('Failed to add asset');
    }
  };

  // Handle confirmation of asset addition
  const handleConfirm = () => {
    setShowConfirmation(false);
    setAssetData({
      name: '',
      asset_sn: '',
      description: '',
      acquired_date: currentDate,
      image: null,
      asset_status: 'Ready',
    });
    setImagePreview(null);
  };

  // Handle cancellation of asset addition
  const handleCancel = () => {
    setShowConfirmation(false);
    onClose();
    navigate('/assets-view-all');
  };

  return (
    <div className="form-container">
      <h3>Add New Asset</h3>
      <form onSubmit={handleSubmit}>
        <label htmlFor="name">Asset Name:</label>
        <input
          type="text"
          id="name"
          name="name"
          value={assetData.name}
          onChange={handleChange}
          className="form-input"
          required
        />
        
        <label htmlFor="asset_sn">
          Asset Serial Number:
          <span className="tooltip" data-tooltip="Serial Number or Unique Identifier.">
            ⓘ
          </span>
        </label>
        <input
          type="text"
          id="asset_sn"
          name="asset_sn"
          value={assetData.asset_sn}
          onChange={handleChange}
          className="form-input"
          required
        />

        <label htmlFor="description">
          Description:
          <span className="tooltip" data-tooltip="Description of asset.">
            ⓘ
          </span>
        </label>
        <textarea
          id="description"
          name="description"
          value={assetData.description}
          onChange={handleChange}
          className="form-input"
          required
        />

        <label htmlFor="acquired_date">
          Acquired Date:
          <span className="tooltip" data-tooltip="Date asset was Acquired">
            ⓘ
          </span>
        </label>
        <input
          type="date"
          id="acquired_date"
          name="acquired_date"
          value={assetData.acquired_date}
          onChange={handleChange}
          className="form-input"
          required
        />

        <label htmlFor="asset_status">
          Asset Status:
          <span className="tooltip" data-tooltip="Status of asset. To make/edit global settings, please go to Settings > Global Settings. To make/edit local settings, go to Settings > Local Settings.">
            ⓘ
          </span>
        </label>
        <select
          id="asset_status"
          name="asset_status"
          value={assetData.asset_status}
          onChange={handleChange}
          className="form-input"
          required
        >
          {statusOptions.map(option => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
        
        <label htmlFor="image">Asset Image:</label>
        <ImageDragDrop
          imagePreview={imagePreview}
          setImagePreview={setImagePreview}
          setImage={(file) => setAssetData({ ...assetData, image: file })}
        />

        <button type="submit" className="standard-btn">Add Asset</button>
      </form>

      {showConfirmation && (
        <ConfirmationModal
        message="Do you want to add another asset?"
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
      )}
      <ToastContainer />
    </div>
  );
};

export default AssetAddForm;
