import React, { useState, useEffect } from 'react';
import Modal from '@mui/material/Modal';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';

const EditDaqConfigModal = ({ isOpen, onClose, init_config }) => {
  const [config, setConfig] = useState({});

  useEffect(() => {
    setConfig(init_config);
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setConfig(prevState => ({
      ...prevState,
      [name]: value
    }));
  };

  const handleSaveAndDeploy = () => {
    // Perform save and deploy logic here
    console.log('Saving and deploying daq config:', config);
  };

  return (
    <Modal open={isOpen} onClose={onClose}>
      <Box
        sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', bgcolor: 'background.paper',
          boxShadow: 24, p: 4, maxWidth: '90%', maxHeight: '90%', overflow: 'auto' }} >
        <Typography variant="h5" component="h2" mb={2}> Edit DAQ Config </Typography>
        {/* Render form fields for editing daq config */}
        <TextField
          label="Detector Type"
          name="detector_type" value={config.detector_type || ''} onChange={handleChange} fullWidth margin="normal"
        />
        <TextField label="Detector Name" name="detector_name" value={config.detector_name || ''} onChange={handleChange}
          fullWidth margin="normal"
        />
        {/* Add more form fields as needed */}
        <Box mt={4}>
          <Button variant="contained" color="primary" onClick={handleSaveAndDeploy} > Save and Deploy </Button>
          <Button variant="contained" color="error" onClick={onClose} sx={{ ml: 2 }} > Close </Button>
        </Box>
      </Box>
    </Modal>
  );
};

export default EditDaqConfigModal;
