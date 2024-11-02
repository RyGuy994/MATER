// Import React and necessary hooks
import React, { useState } from 'react';
// Import Link and useLocation from React Router
import { Link, useLocation } from 'react-router-dom';
// Import CSS file for styling
import './Header.css';
// Import Mater image
import materImage from '../static/favicon-16x16.png';
// Import Modal component
import Modal from '../common/Modal';

// Header component
const Header = ({ isLoggedIn, handleLogout }) => {
  // Get current location
  const location = useLocation();

  // State to manage modal visibility and type
  const [modalOpen, setModalOpen] = useState(false);
  const [modalType, setModalType] = useState(null); // 'asset', 'service', or 'bulk-upload'

  // Open Add Asset modal
  const openAddAssetModal = () => {
    setModalType('asset');
    setModalOpen(true);
  };

  // Open Add Service modal
  const openAddServiceModal = () => {
    setModalType('service');
    setModalOpen(true);
  };

  // Open Bulk Upload Assets modal
  const openBulkUploadModal = () => {
    setModalType('bulk-upload'); // Set type to 'bulk-upload'
    setModalOpen(true);
  };

  // Close modal
  const handleCloseModal = () => {
    setModalOpen(false);
    setModalType(null);
  };

  // Render nothing if the current path is '/' or '/login'
  if (location.pathname === '/' || location.pathname === '/login') {
    return null; // Do not render the header
  }

  return (
    <div className="header-container">
      <nav>
        {isLoggedIn ? (
          <ul>
            <li>
              <Link to="/home" className="icon-link">
                <div className="icon-container">
                  <img src={materImage} alt="Home" className="icon" />
                  <span>Home</span>
                </div>
              </Link>
            </li>
            <li className="dropdown">
              <span>Assets</span>
              <div className="dropdown-content">
                <span onClick={openAddAssetModal}>Add Asset</span>
                <span onClick={openBulkUploadModal}>Bulk Upload Assets</span>
                <Link to="/assets-view-all">View All Assets</Link>
              </div>
            </li>
            <li className="dropdown">
              <span>Services</span>
              <div className="dropdown-content">
                <span onClick={openAddServiceModal}>Add Service</span>
                <Link to="/services-view-all">View All Services</Link>
              </div>
            </li>
            <li className="dropdown">
              <span>Settings</span>
              <div className="dropdown-content">
                <Link to="/profile">My Profile</Link>
                <Link to="/settings-global">Global Settings</Link>
                <Link to="/settings-local">Local Settings</Link>
                <Link to="/settings-user">Add/Edit Users</Link>
              </div>
            </li>
            <li>
              <span onClick={handleLogout}>Logout</span>
            </li>
          </ul>
        ) : (
          <ul>
            <li>
              <Link to="/" className="icon-link">
                <div className="icon-container">
                  <img src={materImage} alt="Home" className="icon" />
                  <span>Login</span>
                </div>
              </Link>
            </li>
          </ul>
        )}
      </nav>

      {/* Conditionally render the Modal component */}
      {modalOpen && (
        <Modal
          type={modalType} // Pass the modal type (asset, service, or bulk)
          mode="add"
          onClose={handleCloseModal}
          onSubmit={() => {
            // Define what happens after form submission
            handleCloseModal();
          }}
        />
      )}
    </div>
  );
};

// Export the Header component
export default Header;
