// src/components/common/ConfirmationModal.jsx

// Import React library
import React from 'react';

// Import CSS file for styling
import './ConfirmationModal.css';

// Functional component for Confirmation Modal
const ConfirmationModal = ({ message, onConfirm, onCancel }) => {
  return (
    // Modal overlay covering the entire viewport
    <div className="modal-overlay">
      {/* Modal container */}
      <div className="modal">
        {/* Message to display */}
        <p>{message}</p>
        {/* Line break */}
        <br></br>
        {/* Button for confirming action */}
        <button onClick={onConfirm} className="standard-btn">Yes</button>
        {/* Button for canceling action */}
        <button onClick={onCancel} className="standard-btn">No</button>
      </div>
    </div>
  );
};

// Export the ConfirmationModal component
export default ConfirmationModal;
