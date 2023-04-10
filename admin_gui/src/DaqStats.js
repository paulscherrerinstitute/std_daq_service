import React, {useState} from 'react';
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

function DaqStats(props) {
  const { state } = props;

  const n_bytes = 0;
  const n_images = 0;
  const stats_url = "http://www.google.com";

  let status_chip;
  if (n_bytes > 0) {
     status_chip = <Chip variant="contained" label="Streaming" color="success" />;
  } else {
      status_chip = <Chip variant="contained" label="Idle" color="info" />;
  }

  return (
    <Paper sx={{ p: 2 }} elevation={3}>
      <Typography variant="h6" gutterBottom>DAQ stats</Typography>

      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Detector:</Typography></Grid>
        <Grid item> {status_chip} </Grid>
      </Grid>

      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle2">Bandwidth:</Typography></Grid>
        <Grid item> {n_bytes/1024/1024} MB/s </Grid>
      </Grid>
      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle2">Frequency:</Typography></Grid>
        <Grid item> {n_images} Hz </Grid>
      </Grid>

      <a href={stats_url} target="_blank">
        <Button variant="outlined" endIcon={<LaunchIcon />}>Details</Button>
      </a>


    </Paper>
  );
}

export default DaqStats;