import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Modal from '@mui/material/Modal';
import AssetAddForm from '../assets/AssetAddForm.jsx';
import AssetEditForm from '../assets/AssetEditForm.jsx';
import ServiceAddForm from '../services/ServiceAddForm.jsx';
import AssetBulkUploadForm from '../assets/AssetBulkUploadForm.jsx';
import NotesForm from '../notes/NotesForm.jsx';
import CostsForm from '../costs/CostsForm.jsx';

const style = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 400,
    maxHeight: '80vh',
    bgcolor: 'background.paper',
    border: '2px solid #000',
    boxShadow: 24,
    p: 4,
    overflowY: 'auto',
};

const GenericModal = ({ type, mode, item, onClose, onSubmit }) => {
    const handleSubmit = async (data) => {
        await onSubmit(data); // Call the passed onSubmit function
        onClose(); // Close the modal
    };

    return (
        <Modal
            open={true}
            onClose={onClose}
            aria-labelledby="modal-modal-title"
            aria-describedby="modal-modal-description"
        >
            <Box sx={style}>
                <Typography id="modal-modal-title" variant="h4" component="h2">
                    {mode === 'edit'
                        ? `Edit ${type.charAt(0).toUpperCase() + type.slice(1)}`
                        : `Add ${type.charAt(0).toUpperCase() + type.slice(1)}`}
                </Typography>

                {/* Handling other forms */}
                {type === 'asset' && mode === 'edit' && (
                    <AssetEditForm asset={item} onSubmit={handleSubmit} onClose={onClose} />
                )}
                {type === 'asset' && mode === 'add' && (
                    <AssetAddForm onClose={onClose} onSubmit={handleSubmit} />
                )}
                {type === 'service' && mode === 'add' && (
                    <ServiceAddForm onClose={onClose} onSubmit={handleSubmit} />
                )}
                {type === 'bulk-upload' && mode === 'add' && (
                    <AssetBulkUploadForm onClose={onClose} onSubmit={handleSubmit} />
                )}

                {/* Notes Form */}
                {type === 'notes-asset' && (
                    <NotesForm asset_Id={item} onClose={onClose} />
                )}

                {/* Notes Form */}
                {type === 'costs-asset' && (
                    <CostsForm asset_Id={item} onClose={onClose} />
                )}

                <button className="standard-del-btn" onClick={onClose}>Close</button>
            </Box>
        </Modal>
    );
};

export default GenericModal;
