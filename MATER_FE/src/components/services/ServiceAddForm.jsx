import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../common/common.css';
import '../common/form.css';
import ConfirmationModal from '../common/ConfirmationModal';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const ServiceAddForm = ({ onClose }) => {
  const currentDate = new Date().toISOString().split('T')[0];
  const [assets, setAssets] = useState([]);
  const [filteredAssets, setFilteredAssets] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusOptions, setStatusOptions] = useState([]);
  const [serviceTypeOptions, setServiceTypeOptions] = useState([]);
  const [serviceData, setServiceData] = useState({
    asset_id: '',
    service_type: '',
    service_date: currentDate,
    service_status: '',
    service_add_again_check: false,
    service_add_again_days_cal: '',
    attachments: [],
  });
  const [errorMessage, setErrorMessage] = useState('');
  const [attachmentsPreview, setAttachmentsPreview] = useState([]);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const navigate = useNavigate();

  // Fetch status options
  useEffect(() => {
    const fetchStatusOptions = async () => {
      try {
        const jwtToken = localStorage.getItem('jwt');
        const baseUrl = import.meta.env.VITE_BASE_URL;
        const statusUrl = `${baseUrl}/settings/appsettings/services/status`;

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

  // Fetch service type options
  useEffect(() => {
    const fetchServiceTypeOptions = async () => {
      try {
        const jwtToken = localStorage.getItem('jwt');
        const baseUrl = import.meta.env.VITE_BASE_URL;
        const serviceTypeUrl = `${baseUrl}/settings/appsettings/services/type`;

        const response = await fetch(serviceTypeUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ jwt: jwtToken }),
        });

        if (response.ok) {
          const data = await response.json();
          setServiceTypeOptions(data.map(setting => setting.value));
        } else {
          const errMessage = await response.json();
          setErrorMessage(`Failed to fetch service type options: ${errMessage.error}`);
          toast.error(`Failed to fetch service type options: ${errMessage.error}`);
        }
      } catch (err) {
        setErrorMessage('An error occurred while fetching service type options');
        toast.error('An error occurred while fetching service type options');
      }
    };

    fetchServiceTypeOptions();
  }, []);

  // Fetch assets
  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const jwtToken = localStorage.getItem('jwt');
        const response = await fetch(`${import.meta.env.VITE_BASE_URL}/assets/asset_all`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ jwt: jwtToken }),
        });
  
        if (!response.ok) {
          const errorResponse = await response.json();
          console.error('Error fetching assets:', errorResponse);
          return;
        }
  
        const assetsData = await response.json();
        console.log('Assets data:', assetsData);
  
        const assetsArray = assetsData.assets;
        if (Array.isArray(assetsArray)) {
          setAssets(assetsArray);
          setFilteredAssets(assetsArray);
        } else {
          console.error('Assets data is not an array:', assetsArray);
          setAssets([]);
        }
      } catch (error) {
        console.error('Error during fetch operation:', error);
      }
    };
    fetchAssets();
  }, []);  

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : value;
    setServiceData({ ...serviceData, [name]: newValue });
  };

  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearchTerm(value);

    const filtered = assets.filter(asset => 
      asset.name.toLowerCase().includes(value.toLowerCase())
    );
    setFilteredAssets(filtered);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const jwtToken = localStorage.getItem('jwt');
    const formData = new FormData();

    for (const key in serviceData) {
      if (key !== 'attachments') {
        formData.append(key, serviceData[key]);
      }
    }
    
    serviceData.attachments.forEach(file => {
      formData.append('attachments', file);
    });

    formData.append('jwt', jwtToken);

    try {
      const baseUrl = import.meta.env.VITE_BASE_URL;
      const AddServiceUrl = `${baseUrl}/services/service_add`;

      const response = await fetch(AddServiceUrl, {
        method: 'POST',
        body: formData,
      });

      const responseData = await response.json();

      if (response.ok) {
        toast.success(responseData.message || 'Service added successfully');
        setShowConfirmation(true);
      } else {
        throw new Error(responseData.error || 'Failed to add service');
      }
    } catch (error) {
      console.error('Failed to add service:', error.message);
      setErrorMessage('Failed to add service');
    }
  };

  const handleConfirm = () => {
    setShowConfirmation(false);
    setServiceData({
      asset_id: '',
      service_type: '',
      service_date: currentDate,
      service_status: '',
      service_add_again_check: false,
      service_add_again_days_cal: '',
      attachments: [],
    });
    setAttachmentsPreview([]);
  };

  const handleCancel = () => {
    setShowConfirmation(false);
    onClose();
    navigate('/services-view-all');
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    setServiceData(prevData => ({
      ...prevData,
      attachments: [...prevData.attachments, ...files],
    }));

    const previews = files.map(file => URL.createObjectURL(file));
    setAttachmentsPreview(prev => [...prev, ...previews]);
  };

  const handleRemoveAttachment = (index) => {
    const newAttachments = serviceData.attachments.filter((_, i) => i !== index);
    const newPreviews = attachmentsPreview.filter((_, i) => i !== index);
    URL.revokeObjectURL(attachmentsPreview[index]); // Revoke the object URL for cleanup
    setServiceData(prevData => ({ ...prevData, attachments: newAttachments }));
    setAttachmentsPreview(newPreviews);
  };

  const handleAssetSelect = (assetId) => {
    setServiceData({ ...serviceData, asset_id: assetId });
    const selectedAsset = assets.find(asset => asset.id === assetId);
    setSearchTerm(selectedAsset ? selectedAsset.name : '');
    setFilteredAssets([]);
  };

  return (
    <div className="form-container">
      <h3>Add New Service</h3>
      <form onSubmit={handleSubmit}>
        <label htmlFor="asset_id" className="required-field">
          Asset Name:
          <span className="tooltip" data-tooltip="The Asset that the service is for. Start typing to filter the assets.">
            ⓘ
          </span>
        </label>
        <input
          type="text"
          id="asset_search"
          name="asset_search"
          className="form-input"
          placeholder="Search Asset Name"
          value={searchTerm}
          onChange={handleSearchChange}
        />
        {searchTerm && filteredAssets.length > 0 && (
          <ul className="asset-dropdown-list">
            {filteredAssets.map(asset => (
              <li
                key={asset.id}
                className="asset-dropdown-list-item"
                onClick={() => handleAssetSelect(asset.id)}
              >
                {asset.name}
              </li>
            ))}
          </ul>
        )}
        <br />
        <label htmlFor="service_type" className="required-field">
          Service Type:
          <span className="tooltip" data-tooltip="Type of Service. To make/edit global settings, please go to Settings > Global Settings. To make/edit local settings, go to Settings > Local Settings.">
            ⓘ
          </span>
        </label>
        <select
          id="service_type"
          name="service_type"
          className="form-input"
          value={serviceData.service_type}
          onChange={handleChange}
          required
        >
          <option value="">Select Service Type</option>
          {serviceTypeOptions.map((type, index) => (
            <option key={index} value={type}>{type}</option>
          ))}
        </select><br />
        <label htmlFor="service_date" className="required-field">
          Service Date:
        <span className="tooltip" data-tooltip="Date the Service accured">
            ⓘ
        </span>
        </label>
        <input
          type="date"
          id="service_date"
          name="service_date"
          className="form-input"
          value={serviceData.service_date}
          onChange={handleChange}
          required
        />
        <br />
        <label htmlFor="service_status" className="required-field">
          Service Status: 
          <span className="tooltip" data-tooltip="Status of Service. To make/edit global settings, please go to Settings > Global Settings. To make/edit local settings, go to Settings > Local Settings.">
            ⓘ
          </span>
        </label>
        <select
          id="service_status"
          name="service_status"
          className="form-input"
          value={serviceData.service_status}
          onChange={handleChange}
          required
        >
          <option value="">Select Service Status</option>
          {statusOptions.map((status, index) => (
            <option key={index} value={status}>{status}</option>
          ))}
        </select><br />
        <label htmlFor="attachments" className="required-field">
          Attachments:
          <span className="tooltip" data-tooltip="This is for Attachments that go with this service.">
            ⓘ
          </span>
        </label>
        <div
          className="drop-area"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => document.getElementById('attachments').click()}
        >
          <p>Drag & drop files here, or click to select files</p>
          <input
            type="file"
            id="attachments"
            name="attachments"
            className="form-input"
            onChange={(e) => {
              const files = Array.from(e.target.files);
              setServiceData(prevData => ({
                ...prevData,
                attachments: [...prevData.attachments, ...files],
              }));

              const previews = files.map(file => URL.createObjectURL(file));
              setAttachmentsPreview(prev => [...prev, ...previews]);
            }}
            multiple
            style={{ display: 'none' }} // Hide the default input
          />
        </div>
        <br />
        {attachmentsPreview.map((preview, index) => (
          <div key={index} className="attachment-preview-container">
            <img
              src={preview}
              alt={`Attachment preview ${index}`}
              className="attachment-preview"
            />
            <button
              type="button"
              className="remove-attachment-btn"
              onClick={() => handleRemoveAttachment(index)}
            >
              X
            </button>
          </div>
        ))}
        <br />
        <button type="submit" className="standard-btn">Add Service</button>
        {errorMessage && <p className="error-message">{errorMessage}</p>}
      </form>
      <ToastContainer />
      {showConfirmation && (
        <ConfirmationModal
          title="Service Added"
          message="Service has been added successfully."
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      )}
    </div>
  );
};

export default ServiceAddForm;
