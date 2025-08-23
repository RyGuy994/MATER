/* src/components/assets/AssetEditForm.jsx */
import React, { useState, useEffect } from 'react';
import '../common/common.css';
import '../common/form.css';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { useNavigate } from 'react-router-dom';
import AssetFormFields from './common/AssetFormFields'; // Import the new modular component

const AssetEditForm = ({ asset, onSubmit, onClose }) => {
  const navigate = useNavigate();
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
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Populate initial form data and preview
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

  // Fetch asset status options
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

    try {
      const baseUrl = import.meta.env.VITE_BASE_URL;
      const editAssetUrl = `${baseUrl}/assets/asset_edit/${asset.id}`;
      const response = await fetch(editAssetUrl, {
        method: 'POST',
        body: formData,
      });

      const responseData = await response.json();
      if (!response.ok) {
        throw new Error(responseData.error || 'Failed to update asset');
      }

      toast.success(responseData.message || 'Asset updated successfully');
      onClose();
      navigate('/assets-view-all');
    } catch (error) {
      console.error('Failed to update asset:', error.message);
      setErrorMessage('Failed to update asset');
      toast.error('Failed to update asset: ' + error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="form-container">
      <h3>Edit Asset</h3>
      <form onSubmit={handleSubmit}>
        <AssetFormFields
          assetData={assetData}
          setAssetData={setAssetData}
          statusOptions={statusOptions}
          imagePreview={imagePreview}
          setImagePreview={setImagePreview}
          setImage={(file) => setAssetData({ ...assetData, image: file })}
          isSubmitting={isSubmitting}
        />
        <button type="submit" className="standard-btn" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : 'Save'}
        </button>
        <button type="button" className="standard-del-btn" onClick={onClose}>
          Cancel
        </button>
      </form>
      {errorMessage && <p className="error-message">{errorMessage}</p>}
      <ToastContainer />
    </div>
  );
};

export default AssetEditForm;
