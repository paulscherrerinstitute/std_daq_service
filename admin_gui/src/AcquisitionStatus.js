import React from 'react';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import {
  Chip,
  Grid,
  Paper,
  LinearProgress,
  Typography,
    Accordion,
  AccordionDetails,
  AccordionSummary,
} from '@mui/material';

function AcquisitionStatus(props) {
  const { state } = props;

  function secondsSinceUnixTimestamp(unixTimestamp) {
  const now = Math.floor(Date.now() / 1000); // current Unix timestamp in seconds
  const diff = now - unixTimestamp; // difference in seconds
  return Math.round(diff); // round to nearest second
}


  let status_chip;
  let progress = (state.stats.n_write_completed / state.info.n_images) * 100;
  let progress_text = state.stats.n_write_completed + "/" + state.info.n_images;

  const get_n_seconds = (start_time, stop_time) => {
    const now = stop_time || Math.floor(Date.now() / 1000);
    const diff = (now - start_time).toFixed(0);
    if (diff <= -0) {
      return 0;
    }
    return diff;
  };
  let n_seconds = get_n_seconds(state.stats.start_time, state.stats.stop_time);

  function formatTimestamp(unixTimestamp) {
    const date = new Date(unixTimestamp * 1000);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    const second = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
  }

  switch (state.state) {
    case 'WAITING_FOR_IMAGES':
      status_chip = <Chip label="Waiting for detector" color="warning" />;
      break;
    case 'ACQUIRING_IMAGES':
      status_chip = <Chip label="Acquiring" color="info" />;
      break;
    case 'FINISHED':
       status_chip = <Chip label="Finished" color="success" />;
        break;
    case 'FAILED':
      status_chip = <Chip label="Failed" color="error" />;
      break;
    default:
      status_chip = <Chip label="Unknown" color="error" />;
      break;
  };

  return (
    <Paper sx={{ p: 2 }} elevation={3}>
      <Typography variant="h6" gutterBottom>Last acquisition</Typography>

      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Status:</Typography></Grid>
        <Grid item> {status_chip} </Grid>
      </Grid>

      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Acquisition progress:</Typography></Grid>
        <Grid item> {progress.toFixed(2) || 0}% </Grid>
      </Grid>

      <LinearProgress variant="determinate" value={progress} />

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
            <Grid item> {state.stats.start_time || 'N/A'} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Stop time:</Typography></Grid>
            <Grid item> {state.stats.stop_time || 'N/A'} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Output file:</Typography></Grid>
            <Grid item> {state.info.output_file || 'N/A'} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Run ID:</Typography></Grid>
            <Grid item> {state.info.run_id || 'N/A'} </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />} aria-controls="status-content" id="status-header">
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Stats:</Typography></Grid>
            <Grid item> <Typography variant="subtitle2">{progress_text} images</Typography></Grid>
          </Grid>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Requested images:</Typography></Grid>
            <Grid item> {state.info.n_images || 'N/A'} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Buffered images:</Typography></Grid>
            <Grid item> {state.stats.n_write_requested || 'N/A'} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Written images:</Typography></Grid>
            <Grid item> {state.stats.n_write_completed || 'N/A'} </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>
    </Paper>
  );
}

export default AcquisitionStatus;