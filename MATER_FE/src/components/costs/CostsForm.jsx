import React, { useState, useEffect } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import '../common/common.css';
import '../common/form.css';
import DeleteModal from '../common/DeleteModal.jsx';

const CostsForm = ({ asset_Id, jwtToken }) => {
  const [costData, setCostData] = useState({ cost_date: '', cost_why: '', cost_data: '' });
  const [costs, setCosts] = useState([]);
  const [totalCost, setTotalCost] = useState(0); // State for total cost
  const [editingCostId, setEditingCostId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [costToDelete, setCostToDelete] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const baseUrl = import.meta.env.VITE_BASE_URL;
  jwtToken = localStorage.getItem('jwt');

  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    fetchCosts();
    setCostData((prevData) => ({
      ...prevData,
      cost_date: today,
    }));
  }, [asset_Id]);

  useEffect(() => {
    // Calculate total cost whenever costs change
    const total = costs.reduce((acc, cost) => acc + parseFloat(cost.cost_data || 0), 0);
    setTotalCost(total);
  }, [costs]);

  const fetchCosts = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${baseUrl}/costs/costs?type=asset&type_id=${asset_Id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${jwtToken}`,
        },
      });
      const data = await response.json();
      setCosts(data.costs || []);
    } catch (error) {
      console.error('Error fetching costs:', error);
      toast.error('Failed to fetch costs');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCostData((prevData) => ({ ...prevData, [name]: value }));
  };

  const handleEditClick = (cost) => {
    setCostData({ cost_date: cost.cost_date, cost_why: cost.cost_why, cost_data: cost.cost_data });
    setEditingCostId(cost.id);
  };

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const trimmedDate = costData.cost_date.trim();
    const trimmedWhy = costData.cost_why.trim();
    const trimmedData = costData.cost_data.trim();

    if (!asset_Id) {
      toast.error('Asset ID is required to save the cost.');
      setLoading(false);
      return;
    }

    if (!trimmedDate || !trimmedData) {
      toast.error('Both date and cost data are required.');
      setLoading(false);
      return;
    }

    const url = editingCostId
      ? `${baseUrl}/costs/costs/${editingCostId}`
      : `${baseUrl}/costs/costs`;

    const method = editingCostId ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${jwtToken}`,
        },
        body: JSON.stringify({
          type: 'asset',
          type_id: asset_Id,
          cost_date: trimmedDate,
          cost_why: trimmedWhy,
          cost_data: parseFloat(trimmedData),
          jwt: jwtToken,
        }),
      });

      if (response.ok) {
        toast.success('Cost saved successfully!');
        fetchCosts();
        const today = new Date().toISOString().split('T')[0];
        setCostData({ cost_date: today, cost_why: '', cost_data: '' });
        setEditingCostId(null);
      } else {
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.error || 'Failed to save cost';
        toast.error(errorMessage);
      }
    } catch (error) {
      console.error('Error saving cost:', error);
      toast.error('Failed to save cost');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (costId) => {
    setCostToDelete(costId);
    setDeleteModalOpen(true);
  };

  const confirmDelete = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${baseUrl}/costs/costs/${costToDelete}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${jwtToken}`,
        },
      });
      if (response.ok) {
        toast.success('Cost deleted successfully!');
        fetchCosts();
      } else {
        const errorData = await response.json();
        toast.error(errorData.error || 'Failed to delete cost');
      }
    } catch (error) {
      console.error('Error deleting cost:', error);
      toast.error('Failed to delete cost');
    } finally {
      setLoading(false);
      setDeleteModalOpen(false);
      setCostToDelete(null);
    }
  };

  const filteredCosts = costs.filter(
    (cost) =>
      cost.cost_why.toLowerCase().includes(searchTerm.toLowerCase()) ||
      cost.cost_date.includes(searchTerm)
  );

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="cost_date">
            Cost Date:
            <span className="tooltip" data-tooltip="Date of the cost.">
              ⓘ
            </span>
          </label>
          <input
            type="date"
            id="cost_date"
            name="cost_date"
            className="form-input"
            value={costData.cost_date}
            onChange={handleInputChange}
            required
          />
        </div>
        <br />
        <div>
          <label htmlFor="cost_why">
            Cost Reason:
            <span className="tooltip" data-tooltip="Reason for the cost.">
              ⓘ
            </span>
          </label>
          <textarea
            id="cost_why"
            name="cost_why"
            className="form-input"
            value={costData.cost_why}
            onChange={handleInputChange}
            placeholder="Enter reason for the cost..."
          />
        </div>
        <br />
        <div>
          <label htmlFor="cost_data">
            Cost Amount:
            <span className="tooltip" data-tooltip="Amount of the cost.">
              ⓘ
            </span>
          </label>
          <input
            type="number"
            id="cost_data"
            name="cost_data"
            className="form-input"
            value={costData.cost_data}
            onChange={handleInputChange}
            placeholder="Enter cost amount..."
            required
          />
        </div>
        <br />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button type="submit" className="standard-btn" disabled={loading}>
            {editingCostId ? 'Update Cost' : '+ Add New Cost'}
          </button>
          <span>Total: ${totalCost.toFixed(2)}</span>
        </div>
      </form>
      {loading && <p>Loading...</p>}
      <div className="costs-history">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h4>History of Costs:</h4>
          <input
            type="text"
            placeholder="Search costs..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="form-input"
            style={{ marginLeft: '10px' }}
          />
        </div>
        {filteredCosts.length > 0 ? (
          <ul>
            {filteredCosts
              .sort((a, b) => new Date(b.cost_date) - new Date(a.cost_date))
              .map((cost) => (
                <li key={cost.id}>
                  <span>{cost.cost_date}: {cost.cost_why} - ${cost.cost_data}</span>
                  <br />
                  <button className="standard-btn" onClick={() => handleEditClick(cost)}>Edit</button>
                  <button className="standard-del-btn" onClick={() => handleDeleteClick(cost.id)}>Delete</button>
                </li>
              ))}
          </ul>
        ) : (
          <p>No costs available.</p>
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

export default CostsForm;
