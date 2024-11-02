import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './Login.css';
import '../common/common.css';
import '../common/Modal.css';
import materImage from '../static/MATER.png';
import OTPVerificationForm from './OTPVerificationForm';

const Login = ({ handleLogin }) => {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [rememberMe, setRememberMe] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [showText, setShowText] = useState(false);
  const [showMfaModal, setShowMfaModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowText(true);
    }, 300);
    return () => clearTimeout(timer);
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleRememberMeChange = () => {
    setRememberMe(!rememberMe);
  };

  const handleSubmit = async (e) => {
    toast.info('Processing... Give it a little bit!');
    e.preventDefault();
    try {
      const baseUrl = import.meta.env.VITE_BASE_URL;
      if (!baseUrl) {
        throw new Error('VITE_BASE_URL is not defined');
      }
      const loginUrl = `${baseUrl}/auth/login`;

      const response = await fetch(loginUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const responseData = await response.json();

      if (response.ok) {
        // Check if MFA is required
        console.log('Response Data:', responseData); // Check the response data
        if (responseData.mfaRequired) {
          setShowMfaModal(true); // Show MFA modal
          toast.info('MFA Required.');
        } else {
          // No MFA, save JWT and navigate
          localStorage.setItem('jwt', responseData.jwt);
          localStorage.setItem('username', formData.username);
          navigate('/home');
          toast.success('Login successful!');
        }
      } else {
        // Show the error message from the backend
        toast.error(responseData.message || 'Login failed');
      }
    } catch (error) {
      console.error('Login failed:', error.message);
      toast.error('An error occurred while logging in');
    }
  };

  const handleMfaSuccess = (username) => {
    handleLogin(username);
    navigate('/home');
    setShowMfaModal(false);
  };

  const handleMfaModalClose = () => {
    setShowMfaModal(false);
  };

  const materLetters = "MATER".split('');

  return (
    <div>
      {/* Background Words */}
      <div className="background-word word-maintenance">Maintenance.</div>
      <div className="background-word word-asset">Asset.</div>
      <div className="background-word word-tracking">Tracking.</div>
      <div className="background-word word-equipment">Equipment.</div>
      <div className="background-word word-registry">Registry.</div>

      <div className="login">
        <ToastContainer position="top-right" autoClose={5000} hideProgressBar={false} />
        <h2 className="cool-text">
          {materLetters.map((letter, index) => (
            <span className="letter" key={index}>{letter}</span>
          ))}
        </h2>
        <div className="cool-text-subtitle">
          <span className="word">Maintenance. </span>
          <span className="word">Asset. </span>
          <span className="word">Tracking. </span>
          <span className="word">Equipment. </span>
          <span className="word">Registry.</span>
        </div>
        <img src={materImage} alt="MATER" className="center" />
        <h3>Login</h3>
        <form onSubmit={handleSubmit} className="login-form">
          <input
            type="text"
            name="username"
            value={formData.username}
            onChange={handleChange}
            placeholder="Username or Email"
            className="login-input"
          /><br />
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Password"
            className="login-input"
          /><br />
          <div className="remember-me-container">
            <label className="switch">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={handleRememberMeChange}
              />
              <span className="slider"></span>
            </label>
            <label htmlFor="rememberMe">Remember Me</label>
          </div>
          <button type="submit" className="standard-btn">Login</button>
        </form>
        <Link to="/signup" className="standard-btn signup-btn">Signup</Link>
      </div>
        {/* MFA Modal */}
        {showMfaModal && (
          <OTPVerificationForm
            username={formData.username}
            onVerifySuccess={handleMfaSuccess}
            onClose={handleMfaModalClose}
          />
        )}
    </div>
  );
};

export default Login;
