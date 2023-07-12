import React, { useEffect, useState } from 'react';
import SettingsIcon from '@material-ui/icons/Settings'
import EditDaqConfigModal from './DaqConfigEdit';
import {Grid, Paper, Typography, Button, Alert} from '@mui/material';
import axios from "axios";

function DaqConfig() {
  const [daqConfig, setDaqConfig] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
     const fetchData = async () => {
       try {
         const result = await axios.get('/daq/config');

         if (result.data.status === 'ok') {
           setDaqConfig(result.data.config);
         } else {
             setDaqConfig(null);
           console.log("[DaqConfig:fetchData]", result.data);
         }

       } catch (error) {
         setDaqConfig(null);
         console.log("[DaqConfig:fetchData]", error);
       }
     }

     const interval = setInterval(() => {
       fetchData();
     }, 500);

     return () => clearInterval(interval);
   }, []);

  const handleEditButtonClick = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  let no_config = !daqConfig

  return (
    <Paper sx={{ p: 2 }} elevation={3}>
        <EditDaqConfigModal isOpen={isModalOpen} onClose={handleCloseModal} init_config={daqConfig} />
      <Typography variant="h6" gutterBottom>DAQ config</Typography>
        {no_config ? (
           <Alert severity="error">No config available. Create one by using the Edit button below.</Alert>
          ) : (
          <div>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Detector type:</Typography></Grid>
            <Grid item> {daqConfig.detector_type} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Detector name:</Typography></Grid>
            <Grid item> {daqConfig.detector_name} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Image shape:</Typography></Grid>
            <Grid item> [{daqConfig.image_pixel_height}, {daqConfig.image_pixel_width}] (height, width)</Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Bit depth:</Typography></Grid>
            <Grid item> {daqConfig.bit_depth} bits/pixel </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Number of modules:</Typography></Grid>
            <Grid item> {daqConfig.n_modules} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Start UDP port:</Typography></Grid>
            <Grid item> {daqConfig.start_udp_port} </Grid>
          </Grid>
        </div>
            )}

      <Button variant="contained" onClick={handleEditButtonClick} endIcon={<SettingsIcon/>}>Edit</Button>

    </Paper>
  );
}

export default DaqConfig;