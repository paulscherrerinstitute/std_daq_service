import React, {useEffect, useState} from 'react';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import axios from 'axios';

import {
  Chip,
  Grid,
  Paper,
  Typography,
  Accordion,
  AccordionDetails,
  AccordionSummary,
  TextField,
  Button,
  Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Alert
} from '@mui/material';

function SimulatorControl(props) {
  const [state, setState] = React.useState({stats: {bytes_per_second: 0, images_per_second:0}});
  const [open, setOpen] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState('');
  const [restError, setRestError] = useState(false);
  const [restErrorText, setRestErrorText] = useState("Unknown")
  let status_chip;

  let start_button_disabled = true;
  let stop_button_disabled = true;
  let mb_per_s = state.stats.bytes_per_second / 1024 / 1024;
  let bandwidth_text = `${mb_per_s.toFixed(2)} MB/s`;
  let frequency_text = `${state.stats.images_per_second.toFixed(2)} Hz`;

   useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await axios.get('/simulation/status');

        if (result.data.status === 'ok') {
          setState(result.data.simulator);
          setRestError(false);
        } else {
          setRestError(true);
          setRestErrorText(result.data.message);
          console.log(result.data);
        }

      } catch (error) {
        setRestError(true);
        setRestErrorText(error.message);
        console.log(error);
      }
    }

    const interval = setInterval(() => {
      fetchData();
    }, 500);

    return () => clearInterval(interval);
  }, []);

  switch (state.status) {
    case 'READY':
      status_chip = <Chip variant="outlined" label="Ready" color="success" />;
      start_button_disabled = false;
      break;
    case 'STREAMING':
      status_chip = <Chip variant="outlined" label="Sending" color="warning" />;
      stop_button_disabled = false;
      break;
    default:
      status_chip = <Chip variant="outlined" label="..." color="error" />;
      break;
  }

  const handleStartClick = () => {
    axios.post('/simulation/start').then(response => {
        if (response.data.status === "error") {
          setErrorMessage(response.data.message);
          setOpen(true);
        }
      })
      .catch(error => {
        setErrorMessage(error.response.data.message);
        setOpen(true);
      });
  };

  const handleCloseErrorDialog = () => {
    setOpen(false);
  };

  const handleStopClick = () => {
    axios.post('/simulation/stop')
      .then(response => {
        if (response.data.status === "error") {
          setErrorMessage(response.data.message);
          setOpen(true);
        }
      })
      .catch(error => {
        setErrorMessage(error.response.data.message);
        setOpen(true);
      });
  };

  return (
    <Paper sx={{ p: 2 }} elevation={3}>
      <Typography variant="h6" gutterBottom>Detector UDP simulator</Typography>

      {restError ? (
           <Alert severity="error">Simulator loading failed. Error message: {restErrorText}</Alert>
          ) : (
              <div>
      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Status:</Typography></Grid>
        <Grid item> {status_chip} </Grid>
        <Grid item>
          <Button variant="contained" onClick={handleStartClick} disabled={start_button_disabled}
                  sx={{ ml: 2, bgcolor: 'success.main', color: 'white' }} > Start </Button>
          <Button variant="contained" onClick={handleStopClick} disabled={stop_button_disabled}
            sx={{ ml: 2, bgcolor: 'error.main', color: 'white' }} > Stop </Button>
        </Grid>
      </Grid>

      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle2">Bandwidth:</Typography></Grid>
        <Grid item> {bandwidth_text} </Grid>
      </Grid>
      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle2">Frequency:</Typography></Grid>
        <Grid item> {frequency_text} </Grid>
      </Grid>
</div>
          )}
      <Dialog open={open} onClose={handleCloseErrorDialog}>
        <DialogTitle>Error</DialogTitle>
        <DialogContent>
          <DialogContentText>{errorMessage}</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseErrorDialog}>Close</Button>
        </DialogActions>
      </Dialog>

    </Paper>
  );
}

export default SimulatorControl;