import React, {useState} from 'react';
import SettingsIcon from '@material-ui/icons/Settings'
import EditDaqConfigModal from './DaqConfigEdit';
import {Grid, Paper, Typography, Button, Alert} from '@mui/material';

function DaqConfig(props) {
  const { state } = props;
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleEditButtonClick = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  let no_config = typeof state === 'undefined'

  return (
    <Paper sx={{ p: 2 }} elevation={3}>
        <EditDaqConfigModal isOpen={isModalOpen} onClose={handleCloseModal} init_config={state} />
      <Typography variant="h6" gutterBottom>DAQ config</Typography>
        {no_config ? (
           <Alert severity="error">No config available. Create one by using the Edit button below.</Alert>
          ) : (
          <div>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Detector type:</Typography></Grid>
            <Grid item> {state.detector_type} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Detector name:</Typography></Grid>
            <Grid item> {state.detector_name} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Image shape:</Typography></Grid>
            <Grid item> [{state.image_pixel_height}, {state.image_pixel_width}] (height, width)</Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Bit depth:</Typography></Grid>
            <Grid item> {state.bit_depth} bits/pixel </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Number of modules:</Typography></Grid>
            <Grid item> {state.n_modules} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Start UDP port:</Typography></Grid>
            <Grid item> {state.start_udp_port} </Grid>
          </Grid>
        </div>
            )}

      <Button variant="contained" onClick={handleEditButtonClick} endIcon={<SettingsIcon/>}>Edit</Button>

    </Paper>
  );
}

export default DaqConfig;