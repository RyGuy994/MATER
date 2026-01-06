// filepath: MATER_FE/src/pages/AssetsPage.jsx
import { useState } from 'react';
import AssetsManager from '../components/assets/AssetsManager';

export default function AssetsPage() {
  return (
    <div className="assets-page">
      <div className="assets-page-header">
        <h1>Asset Management</h1>
        <p>Create and manage asset templates and instances</p>
      </div>
      <AssetsManager />
    </div>
  );
}
