import React, { useState, useEffect } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import '../common/common.css';
import '../common/form.css';
import DeleteModal from '../common/DeleteModal.jsx';

const NotesForm = ({ asset_Id, jwtToken }) => {
  const [noteData, setNoteData] = useState({ note_date: '', note_data: '' });
  const [notes, setNotes] = useState([]);
  const [editingNoteId, setEditingNoteId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [noteToDelete, setNoteToDelete] = useState(null);
  const [searchTerm, setSearchTerm] = useState(''); // Add a state for search term

  const baseUrl = import.meta.env.VITE_BASE_URL;
  jwtToken = localStorage.getItem('jwt');

  useEffect(() => {
    const today = new Date().toISOString().split('T')[0]; // Get today's date in YYYY-MM-DD format
    fetchNotes();
    setNoteData((prevData) => ({
      ...prevData,
      note_date: today,
    }))
  }, [asset_Id]);

  const fetchNotes = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${baseUrl}/notes/notes?type=asset&type_id=${asset_Id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${jwtToken}`,
        },
      });
      const data = await response.json();
      setNotes(data.notes || []);
    } catch (error) {
      console.error('Error fetching notes:', error);
      toast.error('Failed to fetch notes');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNoteData((prevData) => ({ ...prevData, [name]: value }));
  };

  const handleEditClick = (note) => {
    setNoteData({ note_date: note.note_date, note_data: note.note_data });
    setEditingNoteId(note.id);
  };

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const trimmedDate = noteData.note_date.trim();
    const trimmedData = noteData.note_data.trim();

    if (!asset_Id) {
      toast.error('Asset ID is required to save the note.');
      setLoading(false);
      return;
    }

    if (!trimmedDate || !trimmedData) {
      toast.error('Both date and note data are required.');
      setLoading(false);
      return;
    }

    const url = editingNoteId
      ? `${baseUrl}/notes/notes/${editingNoteId}`
      : `${baseUrl}/notes/notes`;

    const method = editingNoteId ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${jwtToken}`,
        },
        body: JSON.stringify({
          type: 'asset',
          type_id: asset_Id,
          note_date: trimmedDate,
          note_data: trimmedData,
          jwt: jwtToken,
        }),
      });

      if (response.ok) {
        toast.success('Note saved successfully!');
        fetchNotes();
        const today = new Date().toISOString().split('T')[0]; // Get today's date in YYYY-MM-DD format
        setNoteData({ note_date: today, note_data: '' });
        setEditingNoteId(null);
      } else {
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.error || 'Failed to save note';
        toast.error(errorMessage);
      }
    } catch (error) {
      console.error('Error saving note:', error);
      toast.error('Failed to save note');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (noteId) => {
    setNoteToDelete(noteId);
    setDeleteModalOpen(true);
  };

  const confirmDelete = async () => {
    const jwtToken = localStorage.getItem('jwt');
    console.log('JWT Token:', jwtToken);
    setLoading(true);
    try {
      const response = await fetch(`${baseUrl}/notes/notes/${noteToDelete}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${jwtToken}`,
        },
      });
      if (response.ok) {
        toast.success('Note deleted successfully!');
        fetchNotes();
      } else {
        const errorData = await response.json();
        toast.error(errorData.error || 'Failed to delete note');
      }
    } catch (error) {
      console.error('Error deleting note:', error);
      toast.error('Failed to delete note');
    } finally {
      setLoading(false);
      setDeleteModalOpen(false);
      setNoteToDelete(null);
    }
  };

  // Filter notes based on search term
  const filteredNotes = notes.filter(
    (note) =>
      note.note_data.toLowerCase().includes(searchTerm.toLowerCase()) ||
      note.note_date.includes(searchTerm)
  );

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="note_date">
            Note Date:
            <span className="tooltip" data-tooltip="Date of the note.">
            ⓘ
            </span>
          </label>
          <input
            type="date"
            id="note_date"
            name="note_date"
            className="form-input"
            value={noteData.note_date}
            onChange={handleInputChange}
            required
          />
        </div>
        <br />
        <div>
          <label htmlFor="note_data">
            Note:
            <span className="tooltip" data-tooltip="Content of the note.">
            ⓘ
            </span>
          </label>
          <textarea
            id="note_data"
            name="note_data"
            className="form-input"
            value={noteData.note_data}
            onChange={handleInputChange}
            placeholder="Enter your note here..."
            required
          />
        </div>
        <br />
        <button type="submit" className="standard-btn" disabled={loading}>
          {editingNoteId ? 'Update Note' : '+ Add New Note'}
        </button>
      </form>
      {loading && <p>Loading...</p>}
      <div className="notes-history">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h4>History of Notes:</h4>
          <input
            type="text"
            placeholder="Search notes..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="form-input"
            style={{ marginLeft: '10px' }}
          />
        </div>
        {filteredNotes.length > 0 ? (
          <ul>
            {filteredNotes
              .sort((a, b) => new Date(b.note_date) - new Date(a.note_date))
              .map((note) => (
                <li key={note.id}>
                  <span>{note.note_date}: {note.note_data}</span>
                  <br />
                  <button className="standard-btn" onClick={() => handleEditClick(note)}>Edit</button>
                  <button className="standard-del-btn" onClick={() => handleDeleteClick(note.id)}>Delete</button>
                </li>
              ))}
          </ul>
        ) : (
          <p>No notes available.</p>
        )}
      </div>
      <ToastContainer />
      <DeleteModal 
        isOpen={deleteModalOpen} 
        onClose={() => setDeleteModalOpen(false)} 
        onConfirm={confirmDelete} 
      />
    </div>
  );  
};

export default NotesForm;