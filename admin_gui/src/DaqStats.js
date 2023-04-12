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

function DaqStats() {
  const [ state, setState ] = useState({bytes_per_second: 0, images_per_second: 0});

  const n_mbytes = state.bytes_per_second / 1024 / 1024;
  const bandwidth_text = `${n_mbytes.toFixed(2)} MB/s`;

  const n_images = state.images_per_second;
  const frequency_text = `${n_images.toFixed(2)} Hz`;
  const stats_url = "http://localhost:5000/stats";

  let status_chip;
  if (n_mbytes > 0) {
     status_chip = <Chip variant="contained" label="Streaming" color="success" />;
  } else {
      status_chip = <Chip variant="contained" label="Idle" color="info" />;
  }

  useEffect(() => {
    const fetchData = async () => {
      const result = await axios(stats_url);
      setState(result.data.stats);
    };

    const interval = setInterval(() => {
      fetchData();
    }, 500);

    return () => clearInterval(interval);
  }, []);

  return (
    <Paper sx={{ p: 2 }} elevation={3}>
      <Typography variant="h6" gutterBottom>DAQ stats</Typography>

      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Detector:</Typography></Grid>
        <Grid item> {status_chip} </Grid>
      </Grid>

      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle2">Bandwidth:</Typography></Grid>
        <Grid item> {bandwidth_text} </Grid>
      </Grid>
      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle2">Frequency:</Typography></Grid>
        <Grid item> {frequency_text} </Grid>
      </Grid>

      <a href={stats_url} target="_blank">
        <Button variant="outlined" endIcon={<LaunchIcon />}>Details</Button>
      </a>


    </Paper>
  );
}

export default DaqStats;