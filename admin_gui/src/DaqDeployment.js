import React, {useEffect, useState} from 'react';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { Chip, Grid, Paper, Typography, Accordion, AccordionDetails, AccordionSummary, Alert, } from '@mui/material';
import axios from "axios";

function DaqDeployment() {
  const [ state, setState ] = useState(
      {status: '...', message: '...', deployment_id: 'N/A', stats: {start_time: 0, end_time: 0}});
  const deployment_url = "/daq/deployment";
  const [restError, setRestError] = useState(false);
  const [restErrorText, setRestErrorText] = useState("Unknown")

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await axios.get(deployment_url);

        if (result.data.status === 'ok') {
          setState(result.data.deployment);
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



  return (
    <Paper sx={{ p: 2 }} elevation={3}>
      <Typography variant="h6" gutterBottom>DAQ deployment</Typography>

      {restError ? (
           <Alert severity="error">Log loading failed. Error message: {restErrorText}</Alert>
          ) : (
      <div>
      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Status:</Typography></Grid>
        <Grid item> {status_chip} </Grid>
      </Grid>

      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Message:</Typography></Grid>
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
            <Grid item> {formatTimestamp(state.stats.start_time)} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Stop time:</Typography></Grid>
            <Grid item> {formatTimestamp(state.stats.stop_time)} </Grid>
          </Grid>
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Deployment ID:</Typography></Grid>
            <Grid item> {state.deployment_id} </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>
      </div>
          )}
    </Paper>
  );
}

export default DaqDeployment;