import React, { useState, useEffect } from 'react';
import Modal from '@mui/material/Modal';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import RefreshIcon from '@mui/icons-material/Refresh';
import { Paper, } from '@mui/material';

import MenuItem from '@mui/material/MenuItem';
import axios from "axios";

const EditDaqConfigModal = ({ isOpen, onClose, init_config }) => {
  const [config, setConfig] = useState({});

  const set_config_with_default = (new_config) => {
   if (!init_config) {
      setConfig({});
    } else {
      setConfig(init_config);
    }
  }

  useEffect(() => {
    set_config_with_default(init_config);
  }, [isOpen]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setConfig({ ...config, [name]: value });
  };

  const handleRefresh = () => {
    set_config_with_default(init_config);
  }

  const handleSaveAndDeploy = () => {
    // Perform save and deploy logic here
    console.log('Saving and deploying daq config:', config);

    axios.post('/daq/config', config).then(response => {
        if (response.data.status === "error") {
          console.log(response.data.message);
        }
      })
      .catch(error => {
        console.log(error.response.data.message);
      });

    onClose();
  };

  return (
    <Modal open={isOpen} onClose={onClose}>
      <Box
        sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', bgcolor: 'background.paper',
          boxShadow: 24, p: 4, maxWidth: '90%', maxHeight: '90%', overflow: 'auto' }} >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h5" component="h2"> Edit DAQ Config </Typography>
            <Button variant="outlined" color="info" onClick={handleRefresh} startIcon={<RefreshIcon />}> Refresh </Button>
          </Box>
        <Paper sx={{ p: 2 }} elevation={3}>
          <Typography variant="h6" gutterBottom>Detector</Typography>
          <TextField
            label="Type" name="detector_type" value={config.detector_type || 'eiger'} onChange={handleChange}
            fullWidth margin="normal" select >
            <MenuItem value="eiger">Eiger</MenuItem>
            <MenuItem value="gigafrost">Gigafrost</MenuItem>
            <MenuItem value="jungfrau">Jungfrau</MenuItem>
            <MenuItem value="bsread">bsread</MenuItem>
          </TextField>
          <TextField label="Name" name="detector_name" value={config.detector_name || ''} onChange={handleChange}
            fullWidth margin="normal"
          />
        </Paper>

        <Paper sx={{ p: 2 }} elevation={3}>
          <Typography variant="h6" gutterBottom>Image</Typography>

          <Box sx={{ display: 'flex', gap: '16px' }}>
            <TextField label="Height" name="image_pixel_height" value={config.image_pixel_height || 0} onChange={handleChange}
                       fullWidth margin="normal" />
            <TextField label="Width" name="image_pixel_width" value={config.image_pixel_width || 0} onChange={handleChange}
              fullWidth margin="normal" />
            <TextField label="Bit depth" name="bit_depth" value={config.bit_depth || 16} onChange={handleChange}
            fullWidth margin="normal" select >
            <MenuItem value="4">4</MenuItem>
            <MenuItem value="8">8</MenuItem>
            <MenuItem value="16">16</MenuItem>
            <MenuItem value="32">32</MenuItem>
          </TextField>
          </Box>
        </Paper>
        <Paper sx={{ p: 2 }} elevation={3}>
          <Typography variant="h6" gutterBottom>Network</Typography>

          <Box sx={{ display: 'flex', gap: '16px' }}>
            <TextField label="Number of modules" name="n_modules" value={config.n_modules || 0}
              onChange={handleChange} fullWidth margin="normal" />
            <TextField label="Start UDP port" name="start_udp_port" value={config.start_udp_port || 0}
              onChange={handleChange} fullWidth margin="normal" />
          </Box>
        </Paper>


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
