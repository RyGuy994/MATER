/* src/components/assets/AssetEditPage.jsx */

import React, { useState, useEffect, useRef } from 'react'; // Importing React and necessary hooks
import '../common/common.css'; // Importing common styles
import { ToastContainer, toast } from 'react-toastify'; // Importing toast notifications
import 'react-toastify/dist/ReactToastify.css'; // Importing toast styles
import DeleteModal from '../common/DeleteModal.jsx'; // Importing DeleteModal component for asset deletion confirmation
import { useNavigate, useParams } from 'react-router-dom'; // Importing hooks for navigation and URL parameters
import GenericModal from '../common/Modal.jsx';

const AssetEditPage = ({ onSubmit, onClose }) => {
  const { asset_id } = useParams(); // Get asset_id from the URL parameters
  const navigate = useNavigate(); // Initialize navigation function
  const [assetData, setAssetData] = useState({ // State for managing asset data
    name: '', // Asset name
    asset_sn: '', // Asset serial number
    description: '', // Asset description
    acquired_date: '', // Date the asset was acquired
    asset_status: '', // Current status of the asset
    image: null, // State to hold the asset image file
  });
  const [statusOptions, setStatusOptions] = useState([]); // State for asset status options
  const [imagePreview, setImagePreview] = useState(null); // State for image preview
  const [errorMessage, setErrorMessage] = useState(null); // State for error messages
  const [isDragActive, setIsDragActive] = useState(false); // State to manage drag-and-drop status
  const [isSubmitting, setIsSubmitting] = useState(false); // State to indicate if the form is being submitted
  const [showDeleteModal, setShowDeleteModal] = useState(false); // State to control visibility of the delete confirmation modal
  const [modalOpen, setModalOpen] = useState(false);
  const [editAsset, setEditAsset] = useState(null);  // For asset being edited
  const [modalType, setModalType] = useState(null);  // To differentiate modal type
  const [needsFetch, setNeedsFetch] = useState(false); // If you need to refetch after modal

  const [assetToDelete, setAssetToDelete] = useState(null); // State to hold the asset ID to be deleted
  const fileInputRef = useRef(null); // Reference for the file input element
  const baseUrl = import.meta.env.VITE_BASE_URL; // Base URL for API requests, fetched from environment variables

  // Fetch asset data when the component loads
  useEffect(() => {
    const fetchAssetData = async () => {
      try {
        const baseUrl = import.meta.env.VITE_BASE_URL;
        const assetUrl = `${baseUrl}/assets/asset_edit/${asset_id}`;
        const response = await fetch(assetUrl);

        if (response.ok) {
          const asset = await response.json();
          setAssetData({
            name: asset.name || '',
            asset_sn: asset.asset_sn || '',
            description: asset.description || '',
            acquired_date: asset.acquired_date || '',
            asset_status: asset.asset_status || 'Ready',
            image: null,
          });

          if (asset.image_path) {
            setImagePreview(`${baseUrl}/static/assets/${asset_id}/image/${asset.image_path.split('/').pop()}`);
          } else {
            setImagePreview(`${baseUrl}/static/images/default.png`); // Default image if no image path
          }
        } else {
          const errMessage = await response.json();
          setErrorMessage(`Failed to fetch asset details: ${errMessage.error}`);
          toast.error(`Failed to fetch asset details: ${errMessage.error}`);
        }
      } catch (error) {
        setErrorMessage('An error occurred while fetching asset data');
        toast.error('An error occurred while fetching asset data');
      }
    };

    fetchAssetData();
  }, [asset_id]);

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

  const handleDownload = async (asset_id) => {
    try {
        const jwtToken = localStorage.getItem('jwt'); // Retrieve JWT from local storage
        const response = await fetch(`${baseUrl}/assets/generate_zip/${asset_id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ jwt: jwtToken })
        });

        if (!response.ok) {
            const errorData = await response.json(); // Parse JSON error response
            const errorText = errorData.error || 'Failed to download ZIP file'; // Get error message or fallback
            throw new Error(errorText);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `asset_${asset_id}_files.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Error downloading ZIP file:', error);
        toast.error(error.message || 'Failed to download ZIP file'); // Show specific error message
    }
};

  const handleDelete = (asset_id) => {
    console.log('handleDelete called with asset:', asset_id);
    setAssetToDelete(asset_id);
    setShowDeleteModal(true);
    console.log('showDeleteModal:', showDeleteModal);
    console.log('assetToDelete:', assetToDelete);
  };

  const confirmDelete = async () => {
    setShowDeleteModal(false); // Close the modal
    console.log('Deleting asset with ID:', assetToDelete);
    if (!assetToDelete) return; // Early exit if no asset to delete
  
    try {
      const deleteUrl = `${baseUrl}/assets/asset_delete/${assetToDelete}`;
      const jwtToken = localStorage.getItem('jwt'); // Retrieve JWT from local storage
  
      const response = await fetch(deleteUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jwt: jwtToken // Include JWT token in the body
        }),
      });
  
      const responseData = await response.json();
      if (response.ok) {
        toast.success(responseData.message || 'Asset deleted successfully');
        setAssetToDelete(null);
        navigate(-1);
      } else {
        throw new Error(responseData.error || 'Failed to delete asset');
      }
    } catch (error) {
      console.error('Failed to delete asset:', error.message);
      toast.error('Failed to delete asset');
    }
  };
  
  const closeModal = () => {
    console.log('Closing modal...');
    setModalOpen(false);
    setEditAsset(null);
    setModalType(null);
    setNeedsFetch(true); // This is for refetching data if needed
  };

  const openNotesModal = () => {
    setModalOpen(true); // Set to open modal
    setModalType('notes-asset'); // Set the type of modal if you want to handle it
};

  const openCostsModal = () => {
    setModalOpen(true); // Set to open modal
    setModalType('costs-asset'); // Set the type of modal if you want to handle it
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
      const EditAssetUrl = `${baseUrl}/assets/asset_edit/${asset_id}`; // Use asset_id from useParams
      const response = await fetch(EditAssetUrl, {
        method: 'POST',
        body: formData,
      });
  
      const responseData = await response.json();
      if (!response.ok) {
        throw new Error(responseData.error || 'Failed to update asset');
      }
  
      toast.success(responseData.message || 'Asset updated successfully');
      
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
        <DeleteModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)} // Close modal on cancel
        onConfirm={confirmDelete} // Confirm delete on modal confirm button
      />
      {modalOpen && (
        <GenericModal
          type={modalType}
          mode="add"  
          item={asset_id} // Pass the asset_id
          onClose={closeModal} // Close modal function
        />
      )}
      {modalOpen && (
        <GenericModal
          type={modalType}
          mode="add"  
          item={asset_id} // Pass the asset_id
          onClose={closeModal} // Close modal function
        />
      )}
      <h3>Asset Page - Edit/View</h3>
      <div className="standard-action-zone">
      <h4>Asset Action Zone</h4>
      <button className="standard-btn" onClick={() => handleDownload(asset_id)}>Download</button>
      <button className="standard-btn" onClick={openNotesModal}>Notes</button>
      <button className="standard-btn" onClick={openCostsModal}>Costs</button>
      <button className="standard-del-btn" onClick={() => handleDelete(asset_id)}>Delete</button>
      </div>
      <form onSubmit={handleSubmit}>
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
                style={{ maxWidth: '200px', maxHeight: '200px', border: '3px solid green', marginBottom: '10px' }}
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
        <button type="submit" className="standard-btn" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : 'Save'}
        </button>
        <button type="button" className="standard-del-btn" onClick={() => navigate(-1)}>Back</button>
      </form>
      {errorMessage && <p className="error-message">{errorMessage}</p>}
      <ToastContainer />
    </div>
  );
};

export default AssetEditPage;