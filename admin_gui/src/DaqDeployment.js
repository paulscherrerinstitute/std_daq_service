import React, {useEffect, useState} from 'react';
import LaunchIcon from '@material-ui/icons/Launch';
import SettingsIcon from '@material-ui/icons/Settings'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import {
  Chip,
  Grid,
  Paper,
  Typography,
    Accordion,
  AccordionDetails,
  AccordionSummary,
    TextField,
    Button
} from '@mui/material';
import axios from "axios";

function DaqDeployment() {
  const [ state, setState ] = useState(
      {status: '...', message: '...', deployment_id: '...', stats: {start_time: 0, end_time: 0}});
  const deployment_url = "http://localhost:5000/deployment";

  let status_chip;
  switch (state.status) {
    case 'SUCCESS':
      status_chip = <Chip variant="inlined" label="Success" color="success" />;
      break;
    case 'RUNNING':
      status_chip = <Chip variant="inlined" label="Running" color="info" />;
      break;
    case 'ERROR':
      status_chip = <Chip variant="inlined" label="Error" color="error" />;
      break;
    default:
      status_chip = <Chip variant="inlined" label="..." color="error" />;
      break;
  };

  function formatTimestamp(unixTimestamp) {
    if (!unixTimestamp) {
      return "N/A";
    }
    const date = new Date(unixTimestamp * 1000);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    const second = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
  }

   const get_n_seconds = (start_time, stop_time) => {
    if (!start_time) {
      return 0;
    }
    const now = stop_time || Math.floor(Date.now() / 1000);
    const diff = (now - start_time).toFixed(0);
    if (diff <= -0) {
      return 0;
    }
    return diff;
  };
  let n_seconds = get_n_seconds(state.stats.start_time, state.stats.stop_time);


  useEffect(() => {
    const fetchData = async () => {
      const result = await axios(deployment_url);
      setState(result.data.deployment);
    };

    const interval = setInterval(() => {
      fetchData();
    }, 500);

    return () => clearInterval(interval);
  }, []);

  return (
    <Paper sx={{ p: 2 }} elevation={3}>
      <Typography variant="h6" gutterBottom>DAQ deployment</Typography>

      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Status:</Typography></Grid>
        <Grid item> {status_chip} </Grid>
      </Grid>

      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle2">Message:</Typography></Grid>
        <Grid item> {state.message} </Grid>
      </Grid>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />} aria-controls="status-content" id="status-header">
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Info:</Typography></Grid>
            <Grid item> <Typography variant="subtitle2" >{n_seconds} seconds</Typography></Grid>
          </Grid>
        </AccordionSummary>
          <AccordionDetails>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Start time:</Typography></Grid>
            <Grid item> {formatTimestamp(state.stats.start_time) || 'N/A'} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Stop time:</Typography></Grid>
            <Grid item> {formatTimestamp(state.stats.stop_time) || 'N/A'} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Run ID:</Typography></Grid>
            <Grid item> {state.deployment_id || 'N/A'} </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>
    </Paper>
  );
}

export default DaqDeployment;