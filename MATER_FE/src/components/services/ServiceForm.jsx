import React, { useState, useEffect } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import '../common/common.css';
import '../common/form.css';
import DeleteModal from '../common/DeleteModal.jsx';

const ServiceForm = ({ asset_Id, jwtToken }) => {
  const [serviceData, setServiceData] = useState({ service_date: '', service_type: '', service_status: '' });
  const [services, setServices] = useState([]);
  const [editingServiceId, setEditingServiceId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [serviceToDelete, setServiceToDelete] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const baseUrl = import.meta.env.VITE_BASE_URL;
  jwtToken = localStorage.getItem('jwt');

  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    fetchServices();
    setServiceData((prevData) => ({
      ...prevData,
      service_date: today,
    }));
  }, [asset_Id]);

  const fetchServices = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${baseUrl}/services/services?asset_id=${asset_Id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${jwtToken}`,
        },
      });
      const data = await response.json();
      setServices(data.services || []);
    } catch (error) {
      console.error('Error fetching services:', error);
      toast.error('Failed to fetch services');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setServiceData((prevData) => ({ ...prevData, [name]: value }));
  };

  const handleEditClick = (service) => {
    setServiceData({
      service_date: service.service_date,
      service_type: service.service_type,
      service_status: service.service_status,
    });
    setEditingServiceId(service.id);
  };

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const trimmedDate = serviceData.service_date.trim();
    const trimmedType = serviceData.service_type.trim();
    const trimmedStatus = serviceData.service_status.trim();

    if (!asset_Id) {
      toast.error('Asset ID is required to save the service.');
      setLoading(false);
      return;
    }

    if (!trimmedDate || !trimmedType || !trimmedStatus) {
      toast.error('All fields are required.');
      setLoading(false);
      return;
    }

    const url = editingServiceId
      ? `${baseUrl}/services/services/${editingServiceId}`
      : `${baseUrl}/services/services`;

    const method = editingServiceId ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${jwtToken}`,
        },
        body: JSON.stringify({
          asset_id: asset_Id,
          service_date: trimmedDate,
          service_type: trimmedType,
          service_status: trimmedStatus,
        }),
      });

      if (response.ok) {
        toast.success('Service saved successfully!');
        fetchServices();
        const today = new Date().toISOString().split('T')[0];
        setServiceData({ service_date: today, service_type: '', service_status: '' });
        setEditingServiceId(null);
      } else {
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.error || 'Failed to save service';
        toast.error(errorMessage);
      }
    } catch (error) {
      console.error('Error saving service:', error);
      toast.error('Failed to save service');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (serviceId) => {
    setServiceToDelete(serviceId);
    setDeleteModalOpen(true);
  };

  const confirmDelete = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${baseUrl}/services/services/${serviceToDelete}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${jwtToken}`,
        },
      });
      if (response.ok) {
        toast.success('Service deleted successfully!');
        fetchServices();
      } else {
        const errorData = await response.json();
        toast.error(errorData.error || 'Failed to delete service');
      }
    } catch (error) {
      console.error('Error deleting service:', error);
      toast.error('Failed to delete service');
    } finally {
      setLoading(false);
      setDeleteModalOpen(false);
      setServiceToDelete(null);
    }
  };

  const filteredServices = services.filter(
    (service) =>
      service.service_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      service.service_date.includes(searchTerm) ||
      service.service_status.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="service_date">
            Service Date:
            <span className="tooltip" data-tooltip="Date of the service.">
              ⓘ
            </span>
          </label>
          <input
            type="date"
            id="service_date"
            name="service_date"
            className="form-input"
            value={serviceData.service_date}
            onChange={handleInputChange}
            required
          />
        </div>
        <br />
        <div>
          <label htmlFor="service_type">
            Service Type:
            <span className="tooltip" data-tooltip="Type of the service.">
              ⓘ
            </span>
          </label>
          <input
            type="text"
            id="service_type"
            name="service_type"
            className="form-input"
            value={serviceData.service_type}
            onChange={handleInputChange}
            placeholder="Enter service type"
            required
          />
        </div>
        <br />
        <div>
          <label htmlFor="service_status">
            Status:
            <span className="tooltip" data-tooltip="Status of the service.">
              ⓘ
            </span>
          </label>
          <input
            type="text"
            id="service_status"
            name="service_status"
            className="form-input"
            value={serviceData.service_status}
            onChange={handleInputChange}
            placeholder="Enter service status"
            required
          />
        </div>
        <br />
        <button type="submit" className="standard-btn" disabled={loading}>
          {editingServiceId ? 'Update Service' : '+ Add New Service'}
        </button>
      </form>
      {loading && <p>Loading...</p>}
      <div className="services-history">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h4>History of Services:</h4>
          <input
            type="text"
            placeholder="Search services..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="form-input"
            style={{ marginLeft: '10px' }}
          />
        </div>
        {filteredServices.length > 0 ? (
          <ul>
            {filteredServices
              .sort((a, b) => new Date(b.service_date) - new Date(a.service_date))
              .map((service) => (
                <li key={service.id}>
                  <span>{service.service_date}: {service.service_type} - {service.service_status}</span>
                  <br />
                  <button className="standard-btn" onClick={() => handleEditClick(service)}>Edit</button>
                  <button className="standard-del-btn" onClick={() => handleDeleteClick(service.id)}>Delete</button>
                </li>
              ))}
          </ul>
        ) : (
          <p>No services available.</p>
        )}
      </div>
      <ToastContainer />
      <DeleteModal 
        isOpen={deleteModalOpen} 
        onClose={() => setDeleteModalOpen(false)} 
        onConfirm={confirmDelete} 
      />
    </div>
  );
};

export default ServiceForm;
