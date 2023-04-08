import React, {useState} from 'react';
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

function DaqConfig(props) {
  const { state } = props;

  return (
    <Paper sx={{ p: 2 }} elevation={3}>
      <Typography variant="h6" gutterBottom>DAQ config</Typography>

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

      <Button variant="outlined" >Edit</Button>

    </Paper>
  );
}

export default DaqConfig;