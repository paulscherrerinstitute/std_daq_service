import React, {useEffect, useState} from 'react';
import LaunchIcon from '@material-ui/icons/Launch';
import { Chip, Grid, Paper, Typography, Button } from '@mui/material';
import axios from "axios";

function DaqStats() {
  const [ state, setState ] = useState({
    detector: {bytes_per_second: 0, images_per_second: 0},
    writer: {bytes_per_second: 0, images_per_second: 0}
  });

  const n_mbytes_detector = state.detector.bytes_per_second / 1024 / 1024;
  const bandwidth_text_detector = `${n_mbytes_detector.toFixed(2)} MB/s`;
  const n_images_detector = state.detector.images_per_second;
  const frequency_text_detector = `${n_images_detector.toFixed(2)} Hz`;

  const n_mbytes_writer = state.writer.bytes_per_second / 1024 / 1024;
  const bandwidth_text_writer = `${n_mbytes_writer.toFixed(2)} MB/s`;
  const n_images_writer = state.writer.images_per_second;
  const frequency_text_writer = `${n_images_writer.toFixed(2)} Hz`;

  const stats_url = "/daq/stats";

  let status_chip_detector;
  if (n_mbytes_detector > 0) {
     status_chip_detector = <Chip variant="contained" label="Streaming" color="success" />;
  } else {
      status_chip_detector = <Chip variant="contained" label="Idle" color="info" />;
  }

  let status_chip_writer;
  if (n_mbytes_writer > 0) {
      status_chip_writer = <Chip variant="contained" label="Writing" color="success" />;
  } else {
      status_chip_writer = <Chip variant="contained" label="Idle" color="info" />;
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
        <Grid item> {status_chip_detector} </Grid>
      </Grid>

      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle2">Bandwidth:</Typography></Grid>
        <Grid item> {bandwidth_text_detector} </Grid>
      </Grid>
      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle2">Frequency:</Typography></Grid>
        <Grid item> {frequency_text_detector} </Grid>
      </Grid>

      <Grid container alignItems="center" spacing={1}>
          <Grid item> <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Writer:</Typography></Grid>
          <Grid item> {status_chip_writer} </Grid>
      </Grid>

      <Grid container alignItems="center" spacing={1}>
          <Grid item> <Typography variant="subtitle2">Bandwidth:</Typography></Grid>
          <Grid item> {bandwidth_text_writer} </Grid>
      </Grid>
      <Grid container alignItems="center" spacing={1}>
          <Grid item> <Typography variant="subtitle2">Frequency:</Typography></Grid>
          <Grid item> {frequency_text_writer} </Grid>
      </Grid>

      <a href={stats_url} target="_blank">
        <Button variant="outlined" endIcon={<LaunchIcon />}>Details</Button>
      </a>


    </Paper>
  );
}

export default DaqStats;