/* src/components/assets/common/ImageDragDrop.jsx */

import React, { useState, useRef } from 'react';
import '../../common/common.css';
import '../../common/form.css';
import { toast } from 'react-toastify';

const ImageDragDrop = ({ imagePreview, setImagePreview, setImage }) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const validTypes = ['image/jpeg', 'image/png'];
  const maxSize = 5 * 1024 * 1024; // 5MB

  // File validation logic
  const validateFile = (file) => {
    if (!validTypes.includes(file.type)) {
      toast.error('Invalid file type. Only JPEG and PNG are allowed.');
      return false;
    }
    if (file.size > maxSize) {
      toast.error('File is too large. Maximum allowed size is 5MB.');
      return false;
    }
    return true;
  };

  // Handle drag events
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
    if (file && validateFile(file)) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  // Trigger file input dialog on click
  const handleDropAreaClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // Handle file selection via input
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && validateFile(file)) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  // Remove selected image
  const handleRemoveImage = (e) => {
    e.stopPropagation(); // Prevent triggering file input
    setImage(null);
    setImagePreview(null);
  };

  return (
    <div
      className={`drop-area ${isDragActive ? 'highlight' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleDropAreaClick}
    >
      <input
        type="file"
        className="form-input"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept=".jpeg, .jpg, .png"
        style={{ display: 'none' }}
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
        <p>Please click here to choose a file or drag and drop a file here</p>
      )}
    </div>
  );
};

export default ImageDragDrop;
