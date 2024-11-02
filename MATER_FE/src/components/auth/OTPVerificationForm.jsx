// src/componenets/auth/OTPVerificationForm.jsx
import React, { useState } from 'react';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import '../common/common.css';
import '../common/Modal.css';

const OTPVerificationForm = ({ username, onVerifySuccess, onClose }) => {
  const [otpCode, setOtpCode] = useState('');

  const handleMfaSubmit = async (e) => {
    e.preventDefault();
    try {
      const baseUrl = import.meta.env.VITE_BASE_URL;
      const mfaUrl = `${baseUrl}/mfa/mfa/verify-otp`;

      const response = await fetch(mfaUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          otp: otpCode,
          username, // Pass the username for verification
        }),
      });

      const responseData = await response.json();

      if (response.ok) {
        // Store JWT from MFA verification
        localStorage.setItem('jwt', responseData.jwt);
        onVerifySuccess(username);
        toast.success('Login successful!');
      } else {
        throw new Error('Invalid OTP or session expired');
      }
    } catch (error) {
      console.error('MFA verification failed:', error.message);
      toast.error('MFA verification failed, please try again.');
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <span className="close" onClick={onClose}>&times;</span>
        <h2>Enter your OTP</h2>
        <form onSubmit={handleMfaSubmit}>
          <input
            type="text"
            value={otpCode}
            onChange={(e) => setOtpCode(e.target.value)}
            placeholder="Enter OTP"
            className="login-input"
            required
          /><br />
          <button type="submit" className="standard-btn">Verify OTP</button>
        </form>
      </div>
    </div>
  );
};

export default OTPVerificationForm;
