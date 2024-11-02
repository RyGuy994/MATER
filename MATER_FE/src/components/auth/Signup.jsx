import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './Login.css';
import '../common/common.css';
import materImage from '../static/MATER.png';

const Signup = () => {
  const [formData, setFormData] = useState({ username: '', email: '', password: '', confirmPassword: '' });
  const [errorMessage, setErrorMessage] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Check if passwords match
      if (formData.password !== formData.confirmPassword) {
        throw new Error('Passwords do not match');
      }

      const baseUrl = import.meta.env.VITE_BASE_URL;
      const signupUrl = `${baseUrl}/auth/signup`;

      const response = await fetch(signupUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: formData.username,
          email: formData.email,  // Include the email in the request
          password: formData.password,
        }),
      });

      const responseData = await response.json();

      if (response.ok) {
        navigate('/login');
      } else {
        throw new Error(responseData.error || 'Signup failed');
      }
    } catch (error) {
      console.error('Signup failed:', error.message);
      toast.error(error.message); // Display the error as a toast
    }
  };

  return (
    <div className="login">
      <ToastContainer position="top-right" autoClose={5000} hideProgressBar={false} />
      <h2 className="cool-text" data-text="MATER">
        MATER
      </h2>
      <div className="cool-text-subtitle">
        <span className="word">Hello! You must be new here. </span>
      </div>
      <img src={materImage} alt="MATER" className="center" />
      <h3>Signup</h3>
      <form onSubmit={handleSubmit} className="login-form">
        <input
          type="text"
          name="username"
          value={formData.username}
          onChange={handleChange}
          placeholder="Username"
          className="login-input"
        />
        <br />
        <input
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          placeholder="Email"
          className="login-input"
        />
        <br />
        <input
          type="password"
          name="password"
          value={formData.password}
          onChange={handleChange}
          placeholder="Password"
          className="login-input"
        />
        <br />
        <input
          type="password"
          name="confirmPassword"
          value={formData.confirmPassword}
          onChange={handleChange}
          placeholder="Confirm Password"
          className="login-input"
        />
        <br />
        <button type="submit" className="standard-btn">
          Signup
        </button>
      </form>
      <Link to="/login" className="standard-btn signup-btn">
        Go to Login
      </Link>
    </div>
  );
};

export default Signup;