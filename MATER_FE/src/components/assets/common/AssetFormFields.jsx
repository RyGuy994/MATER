/* src/components/assets/AssetFormFields.jsx */
import React from 'react';
import ImageDragDrop from './ImageDragDrop';

const AssetFormFields = ({
  assetData,
  setAssetData,
  statusOptions,
  imagePreview,
  setImagePreview,
  setImage,
  isSubmitting
}) => (
  <div>
    <label htmlFor="name" className="required-field">Asset Name:</label>
    <input
      type="text"
      id="name"
      name="name"
      className="form-input"
      placeholder="Asset Name"
      value={assetData.name}
      onChange={(e) => setAssetData({ ...assetData, name: e.target.value })}
      required
    />
    <br />
    <label htmlFor="asset_sn" className="required-field">Asset Serial Number:</label>
    <input
      type="text"
      id="asset_sn"
      name="asset_sn"
      className="form-input"
      placeholder="Asset Serial Number"
      value={assetData.asset_sn}
      onChange={(e) => setAssetData({ ...assetData, asset_sn: e.target.value })}
      required
    />
    <br />
    <label htmlFor="description">Asset Description:</label>
    <input
      type="text"
      id="description"
      name="description"
      className="form-input"
      placeholder="Asset Description"
      value={assetData.description}
      onChange={(e) => setAssetData({ ...assetData, description: e.target.value })}
    />
    <br />
    <label htmlFor="acquired_date" className="required-field">Acquired Date:</label>
    <input
      type="date"
      id="acquired_date"
      name="acquired_date"
      className="form-input"
      value={assetData.acquired_date}
      onChange={(e) => setAssetData({ ...assetData, acquired_date: e.target.value })}
      required
    />
    <br />
    <label htmlFor="asset_status" className="required-field">Asset Status:</label>
    <select
      id="asset_status"
      name="asset_status"
      className="form-input"
      value={assetData.asset_status}
      onChange={(e) => setAssetData({ ...assetData, asset_status: e.target.value })}
      required
    >
      {statusOptions.map((status, index) => (
        <option key={index} value={status}>
          {status}
        </option>
      ))}
    </select>
    <br />
    <label htmlFor="image">Asset Image:</label>
    <ImageDragDrop
      imagePreview={imagePreview}
      setImagePreview={setImagePreview}
      setImage={setImage}
    />
    <br />
  </div>
);

export default AssetFormFields;
