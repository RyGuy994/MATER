import React, { useEffect, useState } from 'react';
import './settingsShared.css';
import '../common/common.css';
import DeleteModal from '../common/DeleteModal';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Function to generate a random password
const generateRandomPassword = (length = 12) => {
  const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+[]{}|;:,.<>?";
  let password = "";
  for (let i = 0; i < length; i++) {
    const randomIndex = Math.floor(Math.random() * charset.length);
    password += charset[randomIndex];
  }
  return password;
};

const SettingsUser = () => {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState('');
  const [editMode, setEditMode] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [newUser, setNewUser] = useState({ username: '', email: '', password: '', is_admin: false });
  const [generatedPassword, setGeneratedPassword] = useState('');
  const baseUrl = import.meta.env.VITE_BASE_URL;

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const userUrl = `${baseUrl}/auth/users/all`;
        const jwtToken = localStorage.getItem('jwt');

        if (!jwtToken) {
          setError('JWT token is missing');
          return;
        }

        const response = await fetch(userUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ jwt: jwtToken }), // Include token in the body
        });

        if (response.ok) {
          const data = await response.json();
          setUsers(data.users);
        } else {
          const errMessage = await response.json();
          setError(`Failed to fetch users: ${errMessage.error}`);
        }
      } catch (err) {
        setError('An error occurred');
      }
    };

    fetchUsers();
  }, [baseUrl]);

  const handleEdit = async (userId) => {
    try {
      const jwtToken = localStorage.getItem('jwt');
      const updateUrl = `${baseUrl}/auth/reset_password/${userId}`;
      const response = await fetch(updateUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password: generatedPassword || editValue, jwt: jwtToken }), // Use generated password if available
      });

      if (response.ok) {
        setEditMode(null);
        setEditValue('');
        setGeneratedPassword(''); // Clear generated password
        toast.success('Password updated successfully');
      } else {
        const errMessage = await response.json();
        setError(`Failed to update password: ${errMessage.error}`);
        toast.error(`Failed to update password: ${errMessage.error}`);
      }
    } catch (err) {
      setError('An error occurred');
      toast.error('An error occurred');
    }
  };

  const handleGeneratePassword = () => {
    const newPassword = generateRandomPassword();
    setGeneratedPassword(newPassword);
    toast.info('Generated a new random password');
  };

  const handleCopyPassword = () => {
    navigator.clipboard.writeText(generatedPassword)
      .then(() => toast.success('Password copied to clipboard'))
      .catch(err => toast.error('Failed to copy password'));
  };

  const handleDelete = (userId) => {
    setUserToDelete(userId);
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    setShowDeleteModal(false);
    try {
      const jwtToken = localStorage.getItem('jwt');
      const deleteUrl = `${baseUrl}/auth/delete_user/${userToDelete}`;

      const response = await fetch(deleteUrl, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ jwt: jwtToken }), // Pass JWT in the body
      });

      if (response.ok) {
        setUsers(prevUsers => prevUsers.filter(user => user.id !== userToDelete));
        toast.success('User deleted successfully');
      } else {
        const errMessage = await response.json();
        setError(`Failed to delete user: ${errMessage.error}`);
        toast.error(`Failed to delete user: ${errMessage.error}`);
      }
    } catch (err) {
      setError('An error occurred');
      toast.error('An error occurred');
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    try {
      const jwtToken = localStorage.getItem('jwt');

      if (!jwtToken) {
        setError('JWT token is missing');
        toast.error('JWT token is missing');
        return;
      }

      const addUrl = `${baseUrl}/auth/create_user`;

      const response = await fetch(addUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...newUser, jwt: jwtToken }), // Pass JWT in the body
      });

      if (response.ok) {
        const newAddedUser = await response.json();
        setUsers([...users, newAddedUser]);
        setNewUser({ username: '', email: '', password: '', is_admin: false });
        toast.success('User added successfully');
      } else {
        const errMessage = await response.json();
        setError(`Failed to add user: ${errMessage.error}`);
        toast.error(`Failed to add user: ${errMessage.error}`);
      }
    } catch (err) {
      setError('An error occurred');
      toast.error('An error occurred');
    }
  };

  return (
    <div className="scrollable-container">
      <h1>User Management Page</h1>
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleAddUser} className="add-user-form">
        <label>
          Username: 
          <input
            type="text"
            value={newUser.username}
            onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
          />
        </label>
        <br />
        <label>
          Email: 
          <input
            type="email"
            value={newUser.email}
            onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
          />
        </label>
        <br />
        <label>
          Password: 
          <input
            type="password"
            value={newUser.password}
            onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
          />
        </label>
        <br />
        <label>
          Admin: 
          <input
            type="checkbox"
            checked={newUser.is_admin}
            onChange={(e) => setNewUser({ ...newUser, is_admin: e.target.checked })}
          />
        </label>
        <br />
        <button className="standard-btn" type="submit">Add User</button>
      </form>
      <table>
        <thead>
          <tr>
            <th>Username</th>
            <th>Email</th>
            <th>Admin</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map(user => (
            <tr key={user.id}>
              <td>{user.username}</td>
              <td>{user.email}</td>
              <td>{user.is_admin ? 'Yes' : 'No'}</td>
              <td>
                <button className="standard-btn" onClick={() => { setEditMode(user.id); setEditValue(''); }}>Reset Password</button>
                <button className="standard-del-btn" onClick={() => handleDelete(user.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {editMode && (
        <div className="reset-password-modal">
          <button className="standard-btn" onClick={handleGeneratePassword}>Generate Random Password</button>
          {generatedPassword && (
            <div>
              <p>Generated Password: {generatedPassword}</p>
              <button className="standard-btn" onClick={handleCopyPassword}>Copy to Clipboard</button>
            </div>
          )}
          <button className="standard-btn" onClick={() => handleEdit(editMode)}>Reset Password</button>
        </div>
      )}
      <DeleteModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={confirmDelete}
      />
      <ToastContainer />
    </div>
  );
};

export default SettingsUser;
