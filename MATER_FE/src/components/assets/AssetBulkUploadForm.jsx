import React, { useState, useRef } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import '../common/form.css';
import '../common/common.css';

const BulkAssetUploadForm = () => {
  const [file, setFile] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef(null); // Reference for the hidden file input

  // Handle file selection
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      toast.error('Please select a file to upload');
      return;
    }
  
    const formData = new FormData();
    formData.append('bulk_file', file);
  
    // Retrieve the JWT token from localStorage (or cookie)
    const token = localStorage.getItem('jwt');
    if (!token) {
      toast.error('No authentication token found');
      return;
    }
  
    formData.append('jwt', token);
  
    try {
      const baseUrl = import.meta.env.VITE_BASE_URL;
      const uploadUrl = `${baseUrl}/assets/upload_assets`;
  
      const response = await fetch(uploadUrl, {
        method: 'POST',
        body: formData,
      });
  
      const responseData = await response.json();
  
      if (response.ok) {
        toast.success(responseData.message || 'Assets uploaded successfully');
        setFile(null); // Clear the file after successful upload
      } else {
        throw new Error(responseData.error || 'Failed to upload assets');
      }
    } catch (error) {
      console.error('Failed to upload assets:', error.message);
      toast.error('Failed to upload assets');
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
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
    }
  };

  // Trigger file input dialog on drop area click
  const handleDropAreaClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const baseUrl = import.meta.env.VITE_BASE_URL;

  return (
    <div className="form-container">
      <h3>Bulk Asset Upload</h3>
      <form onSubmit={handleSubmit}>
        <p>
          Download the template: <a href={`${baseUrl}/static/templates_csv/template_asset_bulk_upload.csv`} download>Click Here</a>
        </p>
        <label htmlFor="bulk_file">Select CSV File:</label>
        <div
          className={`drop-area ${isDragActive ? 'highlight' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleDropAreaClick} // Trigger file input dialog on click
        >
          <input
            type="file"
            id="bulk_file"
            name="bulk_file"
            accept=".csv"
            onChange={handleFileChange}
            ref={fileInputRef} // Hidden file input reference
            style={{ display: 'none' }} // Hide the file input
          />

          {file ? (
            <p>{file.name}</p> // Show the name of the selected file
          ) : (
            <p>Please click here to choose a file or drag and drop a file here</p>
          )}
        </div>

        <button type="submit" className="standard-btn">Upload Assets</button>
      </form>
      <ToastContainer />
    </div>
  );
};

export default BulkAssetUploadForm;
