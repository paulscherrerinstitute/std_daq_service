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
  let status_chip;
  let progress = state.stats.n_write_completed / state.stats.n_write_requested;

  switch (state.state) {
    case 'READY':
      status_chip = <Chip label="Ready" color="warning" />;
      break;
    case 'ACQUIRING_IMAGES':
      status_chip = <Chip label="Finished" color="warning" />;
      break;
      case 'FINISHED':
         status_chip = <Chip label="Finished" color="success" />;
          break;
    case 'FAILED':
      status_chip = <Chip label="Failed" color="error" />;
      break;
      // WAITING_FOR_IMAGESu

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
        <Grid item> {progress} </Grid>
      </Grid>

      <LinearProgress variant="determinate" value={progress} />

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />} aria-controls="status-content" id="status-header">
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Info</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">N requested images:</Typography></Grid>
            <Grid item> {state.info.n_images || 'N/A'} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Output file:</Typography></Grid>
            <Grid item> {state.info.output_file || 'N/A'} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Run ID:</Typography></Grid>
            <Grid item> {state.info.run_id || 'N/A'} </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />} aria-controls="status-content" id="status-header">
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Stats</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Start time:</Typography></Grid>
            <Grid item> {state.stats.start_time || 'N/A'} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">End time:</Typography></Grid>
            <Grid item> {state.stats.end_time || 'N/A'} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Number of received images:</Typography></Grid>
            <Grid item> {state.stats.n_write_requested || 'N/A'} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2">Number of written images:</Typography></Grid>
            <Grid item> {state.stats.n_write_completed || 'N/A'} </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>
    </Paper>
  );
}

export default AcquisitionStatus;