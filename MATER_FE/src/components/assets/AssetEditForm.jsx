/* src/components/assets/AssetEditForm.jsx */

import React, { useState, useEffect, useRef } from 'react';
import '../common/common.css';
import '../common/form.css'; // Use form.css for styling
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { useNavigate } from 'react-router-dom';

const AssetEditForm = ({ asset, onSubmit, onClose }) => {
  const navigate = useNavigate(); // Ensure this is correctly initialized
  const [assetData, setAssetData] = useState({
    name: '',
    asset_sn: '',
    description: '',
    acquired_date: '',
    asset_status: '',
    image: null,
  });
  const [statusOptions, setStatusOptions] = useState([]);
  const [imagePreview, setImagePreview] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false); // Added for form submission
  const fileInputRef = useRef(null); // Reference for the hidden file input

  useEffect(() => {
    if (asset) {
      setAssetData({
        name: asset.name || '',
        asset_sn: asset.asset_sn || '',
        description: asset.description || '',
        acquired_date: asset.acquired_date || '',
        asset_status: asset.asset_status || 'Ready',
        image: null,
      });

      if (asset.image_path) {
        const baseUrl = import.meta.env.VITE_BASE_URL;
        setImagePreview(`${baseUrl}/static/assets/${asset.id}/image/${asset.image_path.split('/').pop()}`);
      }
    }
  }, [asset]);

  useEffect(() => {
    const fetchStatusOptions = async () => {
      try {
        const jwtToken = localStorage.getItem('jwt'); // Retrieve JWT from local storage
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

  // Handle input changes and file selection
  const handleChange = (e) => {
    const { name, value, type } = e.target;
    if (type === 'file') {
      const file = e.target.files[0] || null;

      // Validate file type
      const validTypes = ['image/jpeg', 'image/png'];
      if (file && !validTypes.includes(file.type)) {
        toast.error('Invalid file type. Only JPEG and PNG are allowed.');
        return;
      }

      // Validate file size (5MB limit)
      const maxSize = 5 * 1024 * 1024;
      if (file && file.size > maxSize) {
        toast.error('File is too large. Maximum allowed size is 5MB.');
        return;
      }

      setAssetData({ ...assetData, image: file });

      if (file) {
        const reader = new FileReader();
        reader.onloadend = () => {
          setImagePreview(reader.result);
        };
        reader.readAsDataURL(file);
      } else {
        setImagePreview(null);
      }
    } else {
      setAssetData({ ...assetData, [name]: value });
    }
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
  
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
  
    console.log('Form Data:', Array.from(formData.entries()));
  
    try {
      const baseUrl = import.meta.env.VITE_BASE_URL;
      const EditAssetUrl = `${baseUrl}/assets/asset_edit/${asset.id}`;
      const response = await fetch(EditAssetUrl, {
        method: 'POST',
        body: formData,
      });
  
      const responseData = await response.json();
      if (!response.ok) {
        throw new Error(responseData.error || 'Failed to update asset');
      }
  
      toast.success(responseData.message || 'Asset updated successfully');
      onClose(); // Close the modal on successful submission
  
      // Redirect to AssetViewAll page
      navigate('/assets-view-all'); // Update the route as needed
    } catch (error) {
      console.error('Failed to update asset:', error.message);
      setErrorMessage('Failed to update asset');
      toast.error('Failed to update asset: ' + error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle drag events for file drop area
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = () => {
    setIsDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      setAssetData({ ...assetData, image: file });
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  // Trigger file input dialog on drop area click
  const handleDropAreaClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // Handle confirmation of asset addition
  const handleRemoveImage = (e) => {
    e.stopPropagation(); // Prevent click from triggering file input
    setAssetData({ ...assetData, image: null });
    setImagePreview(null);
  };

  return (
    <div className="form-container">
      <h3>Edit Asset</h3>
      <form onSubmit={handleSubmit}>
        <label htmlFor="name" className="required-field">Asset Name:</label>
        <input
          type="text"
          id="name"
          name="name"
          className="form-input"
          placeholder="Asset Name"
          value={assetData.name}
          onChange={handleChange}
          required
        /><br />
        <label htmlFor="asset_sn" className="required-field">Asset Serial Number:</label>
        <input
          type="text"
          id="asset_sn"
          name="asset_sn"
          className="form-input"
          placeholder="Asset Serial Number"
          value={assetData.asset_sn}
          onChange={handleChange}
          required
        /><br />
        <label htmlFor="description">Asset Description:</label>
        <input
          type="text"
          id="description"
          name="description"
          className="form-input"
          placeholder="Asset Description"
          value={assetData.description}
          onChange={handleChange}
        /><br />
        <label htmlFor="acquired_date" className="required-field">Acquired Date:</label>
        <input
          type="date"
          id="acquired_date"
          name="acquired_date"
          className="form-input"
          value={assetData.acquired_date}
          onChange={handleChange}
          required
        /><br />
        <label htmlFor="asset_status" className="required-field">Asset Status:</label>
        <select
          id="asset_status"
          name="asset_status"
          className="form-input"
          value={assetData.asset_status}
          onChange={handleChange}
          required
        >
          {statusOptions.map((status, index) => (
            <option key={index} value={status}>
              {status}
            </option>
          ))}
        </select><br />
        <label htmlFor="image">Asset Image:</label>
        <div
          className={`drop-area ${isDragActive ? 'highlight' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleDropAreaClick} // Trigger file input dialog on click
        >
          <input
            type="file"
            id="image"
            name="image"
            className="form-input"
            ref={fileInputRef} // Hidden file input reference
            onChange={handleChange}
            accept="image/*"
            style={{ display: 'none' }} // Hide the file input
            aria-label="Upload an image for the asset"
          />
            {imagePreview ? (
              <div className="image-preview-container">
                <img
                  src={imagePreview}
                  alt="Image Preview"
                  className="image-preview"
                />
                <button
                  type="button"
                  className="remove-image-btn"
                  onClick={handleRemoveImage}
                >
                  X
                </button>
              </div>
            ) : (
              <p>Drag & drop an image or click to upload</p>
            )}
        </div><br />
        <button type="submit" className="standard-btn" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : 'Save'}
        </button>
        <button type="button" className="standard-del-btn" onClick={onClose}>Cancel</button>
      </form>
      {errorMessage && <p className="error-message">{errorMessage}</p>}
      <ToastContainer />
    </div>
  );
};

export default AssetEditForm;
