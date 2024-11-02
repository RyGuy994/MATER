// src/common/DeleteModal.jsx

import React, { useState } from 'react';
import './Modal.css';
import './common.css'

const DeleteModal = ({ isOpen, onClose, onConfirm }) => {
  const [confirmText, setConfirmText] = useState('');

  const confirmDelete = () => {
    if (confirmText === 'del') {
      onConfirm();
    } else {
      alert('You must type "del" to confirm.');
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h4>Confirm Deletion</h4>
        <p>Please type "del" to confirm the deletion:</p>
        <input
          type="text"
          value={confirmText}
          onChange={(e) => setConfirmText(e.target.value)}
        />
        <div className="modal-actions">
          <button className="standard-del-btn" onClick={confirmDelete}>Delete</button>
          <button className="standard-btn" onClick={onClose}>Cancel</button>
        </div>
      </div>
    </div>
  );
};

export default DeleteModal;
