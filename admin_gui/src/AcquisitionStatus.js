import {useEffect, useState} from "react";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import {Chip, Grid, Paper, LinearProgress, Typography, Accordion, AccordionDetails, AccordionSummary,} from '@mui/material';
import axios from "axios";

function AcquisitionStatus() {
  const [acqState, setAcqState] = useState(null);

  useEffect(() => {
     const fetchData = async () => {
       try {
         const result = await axios.get('/writer/status');
         if (result.data.status === 'ok') {
           setAcqState(result.data.acquisition);
         } else {
           setAcqState(null);
           console.log("[DaqConfig:fetchData]", result.data);
         }

       } catch (error) {
         setAcqState(null);
         console.log("[AcquisitionStatus:fetchData]", error);
       }
     }
     const interval = setInterval(() => { fetchData();}, 500);
     return () => clearInterval(interval);
   }, []);

  const defaultState = {
    stats: {
      n_write_completed: 0,
      start_time: 0,
      stop_time: 0,
      n_write_requested: 0,
    },
    info: {
      n_images: 0,
      output_file: null,
      run_id: null,
    },
    message: "...",
    state: "..."
  };

  const state = acqState || defaultState;

  let progress = (state.stats.n_write_completed / state.info.n_images) * 100;
  if (!progress) {
    progress = 0;
  }
  let progress_text = state.stats.n_write_completed + "/" + state.info.n_images;

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

  let status_chip;
  switch (state.state) {
    case 'WAITING_IMAGES':
      status_chip = <Chip label="Waiting for detector" color="warning" />;
      break;
    case 'ACQUIRING_IMAGES':
      status_chip = <Chip label="Acquiring" color="info" />;
      break;
    case 'FLUSHING_IMAGES':
      status_chip = <Chip label="Flushing" color="info" />;
      break;
    case 'FINISHED':
       status_chip = <Chip label="Finished" color="success" />;
        break;
    case 'FAILED':
      status_chip = <Chip label="Failed" color="error" />;
      break;
    default:
      status_chip = <Chip label="..." color="error" />;
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
        <Grid item> <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Message:</Typography></Grid>
        <Grid item> {state.message} </Grid>
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
            <Grid item> {formatTimestamp(state.stats.start_time) || 'N/A'} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Stop time:</Typography></Grid>
            <Grid item> {formatTimestamp(state.stats.stop_time) || 'N/A'} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={0}>
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