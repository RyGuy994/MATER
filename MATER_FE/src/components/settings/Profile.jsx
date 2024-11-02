// Profile.jsx
import React from 'react';
import PasswordForm from './PasswordForm';
import ColorPickerForm from './ColorPickerForm';
import UserMFAForm from './UserMFAForm';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import '../common/common.css';

const Profile = () => {
  const baseUrl = import.meta.env.VITE_BASE_URL;

  return (
    <div className="profile-container">
      <PasswordForm baseUrl={baseUrl} />
      <UserMFAForm baseurl={baseUrl} />
      <ColorPickerForm />
      <ToastContainer />
    </div>
  );
};

export default Profile;
