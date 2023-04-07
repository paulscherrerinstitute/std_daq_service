import React from 'react';

import {
  Chip,
  Grid,
  Paper,
  LinearProgress,
  Typography
} from '@mui/material';

function AcquisitionStatus(props) {
  const { state } = props;
  let status_chip;
  let progress = state.writer.acquisition.stats.n_write_completed / state.writer.acquisition.stats.n_write_requested;

  switch (state.writer.acquisition.state) {
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
        <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Start time:</Typography></Grid>
        <Grid item> {state.writer.acquisition.start_time || 'N/A'} </Grid>
      </Grid>
      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>End time:</Typography></Grid>
        <Grid item> {state.writer.acquisition.end_time || 'N/A'} </Grid>
      </Grid>

      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Number of received images:</Typography></Grid>
        <Grid item> {state.writer.acquisition.stats.n_write_requested || 'N/A'} </Grid>
      </Grid>
      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Number of written images:</Typography></Grid>
        <Grid item> {state.writer.acquisition.stats.n_write_completed || 'N/A'} </Grid>
      </Grid>

      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Acquistion progress:</Typography></Grid>
        <Grid item> {progress || 100}% </Grid>
      </Grid>

      <LinearProgress variant="determinate" value={progress} />
      {/*    <TextField*/}
      {/*      label="Number of Images"*/}
      {/*      value={response.writer.acquisition.info.n_images}*/}
      {/*      disabled*/}
      {/*      margin="dense"*/}
      {/*      variant="outlined"*/}
      {/*    />*/}
      {/*    <TextField*/}
      {/*      label="Output File"*/}
      {/*      value={response.writer.acquisition.info.output_file}*/}
      {/*      disabled*/}
      {/*      fullWidth*/}
      {/*      margin="dense"*/}
      {/*      variant="outlined"*/}
      {/*    />*/}
      {/*    <TextField*/}
      {/*      label="Number of Completed Image Writes"*/}
      {/*      value={response.writer.acquisition.stats.n_write_completed}*/}
      {/*      disabled*/}
      {/*      margin="dense"*/}
      {/*      variant="outlined"*/}
      {/*    />*/}
      {/*    <TextField*/}
      {/*      label="Number of Requested Image Writes"*/}
      {/*      value={response.writer.acquisition.stats.n_write_requested}*/}
      {/*      disabled*/}
      {/*      margin="dense"*/}
      {/*      variant="outlined"*/}
      {/*    />*/}
      {/*    <TextField*/}
      {/*      label="Start Time"*/}
      {/*      value={new Date(*/}
      {/*        response.writer.acquisition.stats.start_time * 1000*/}
      {/*      ).toLocaleString()}*/}
      {/*      disabled*/}
      {/*      margin="dense"*/}
      {/*      variant="outlined"*/}
      {/*    />*/}
      {/*    <TextField*/}
      {/*      label="Stop Time"*/}
      {/*      value={new Date(*/}
      {/*        response.writer.acquisition.stats.stop_time * 1000*/}
      {/*      ).toLocaleString()}*/}
      {/*      disabled*/}
      {/*      margin="dense"*/}
      {/*      variant="outlined"*/}
      {/*    />*/}
      {/*  </FormGroup>*/}
      {/*</FormControl>*/}
    </Paper>
  );
}

export default AcquisitionStatus;