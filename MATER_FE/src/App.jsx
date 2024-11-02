import React, { useState, useEffect } from 'react'; 
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom'; 
import Header from './components/common/Header'; 
import Home from './components/Home'; 
import Login from './components/auth/Login'; 
import AssetEditPage from './components/assets/AssetEditPage'; 
import AssetViewAll from './components/assets/AssetViewAll'; 
import Signup from './components/auth/Signup'; 
import ServiceViewAll from './components/services/ServiceViewAll'; 
import SettingsGlobal from './components/settings/SettingsGlobal'; 
import SettingsLocal from './components/settings/SettingsLocal'; 
import UsersManagement from './components/settings/SettingsUser'; 
import Profile from './components/settings/Profile'; 
import './App.css';

// Adjust the color brightness/darkness
function adjustColor(color, amount) {
  let usePound = false;

  if (color[0] === "#") {
    color = color.slice(1);
    usePound = true;
  }

  let num = parseInt(color, 16);
  let r = (num >> 16) + amount;
  let b = ((num >> 8) & 0x00FF) + amount;
  let g = (num & 0x0000FF) + amount;

  const newColor = (
    (usePound ? "#" : "") +
    (
      0x1000000 +
      (r < 255 ? (r < 1 ? 0 : r) : 255) * 0x10000 +
      (b < 255 ? (b < 1 ? 0 : b) : 255) * 0x100 +
      (g < 255 ? (g < 1 ? 0 : g) : 255)
    )
    .toString(16)
    .slice(1)
  );

  return newColor;
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false); 
  const [username, setUsername] = useState(''); 
  const [error, setError] = useState(''); 

  useEffect(() => {
    const token = localStorage.getItem('jwt'); 
    if (token) {
      setIsLoggedIn(true); 
      setUsername(localStorage.getItem('username') || ''); 
    }

    const backgroundColor = localStorage.getItem('backgroundColor') || '#c9d3e2';
    const secondaryColor = localStorage.getItem('secondaryColor') || '#ffffff';
    const isGradient = JSON.parse(localStorage.getItem('isGradient')) || true;

    const backgroundStyle = isGradient
      ? `linear-gradient(135deg, ${secondaryColor} 0%, ${backgroundColor} 100%)`
      : backgroundColor;

    document.body.style.background = backgroundStyle;

    const savedColor = localStorage.getItem('primaryColor') || '#4CAF50';
    document.documentElement.style.setProperty('--primary-color', savedColor);

    const hoverColor = localStorage.getItem('primaryColorHover') || '#388E3C';
    document.documentElement.style.setProperty('--primary-color-hover', hoverColor);
    console.log('Primary Color:', savedColor);
    console.log('Primary Color Hover:', hoverColor);

  }, []);

  const handleLogin = (username) => {
    setIsLoggedIn(true); 
    setUsername(username); 
    setError(''); 
    localStorage.setItem('username', username); 
  };

  const handleLogout = () => {
    setIsLoggedIn(false); 
    setUsername(''); 
    localStorage.removeItem('jwt'); 
    localStorage.removeItem('username'); 
  };

  return (
    <Router> 
      <div className="App">
        <Header 
          isLoggedIn={isLoggedIn} 
          handleLogout={handleLogout} 
        />
        <Routes>
          <Route path="/home" element={isLoggedIn ? <Home username={username} /> : <Navigate to="/" />} />
          <Route path="/asset-edit/:asset_id" element={<AssetEditPage />} />
          <Route path="/assets-view-all" element={<AssetViewAll />} />
          <Route path="/services-view-all" element={<ServiceViewAll />} />
          <Route path="/login" element={<Login handleLogin={handleLogin} setError={setError} />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/settings-global" element={isLoggedIn ? <SettingsGlobal /> : <Navigate to="/" />} />
          <Route path="/settings-local" element={isLoggedIn ? <SettingsLocal /> : <Navigate to="/" />} />
          <Route path="/settings-user" element={isLoggedIn ? <UsersManagement /> : <Navigate to="/" />} />
          <Route path="/profile" element={isLoggedIn ? <Profile /> : <Navigate to="/" />} />
          <Route path="/" element={<Login handleLogin={handleLogin} setError={setError} />} />
        </Routes>
        {error && <div className="error">{error}</div>}
      </div>
    </Router>
  );
}

export default App;
