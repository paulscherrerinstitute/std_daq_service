import React from 'react';
import {
  Alert,
  Checkbox,
  Chip,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormLabel,
  Grid,
  Paper,
  TextField
} from '@mui/material';

function WriterStatus(props) {
  const { state } = props;
  let icon;

  switch (state.status) {
    case 'READY':
      icon = <Chip label="Ready" color="success" />;
      break;
    case 'FINISHED':
      icon = <Chip label="Finished" color="warning" />;
      break;
    default:
      icon = <Chip label="Unknown" color="error" />;
      break;
  };

  return (
    <Paper sx={{ p: 2 }}>
      <TextField fullWidth disabled margin="dense" variant="outlined" label="Status" value={state.status}/>
      <TextField fullWidth disabled margin="dense" variant="outlined" label="Message" value={state.message}/>
      <FormControl component="fieldset">
        <FormLabel component="legend">Writer State</FormLabel>
        <FormGroup>
          <FormControlLabel
              control={
                <Checkbox
                    checked={state.status === "READY"}
                    disabled
                />
              }
              label="Ready"
          />
        </FormGroup>
      </FormControl>
      {/*<FormControl component="fieldset">*/}
      {/*  <FormLabel component="legend">Acquisition</FormLabel>*/}
      {/*  <FormGroup>*/}
      {/*    <FormControlLabel*/}
      {/*      control={*/}
      {/*        <Checkbox*/}
      {/*          checked={response.writer.acquisition.state === "FINISHED"}*/}
      {/*          disabled*/}
      {/*        />*/}
      {/*      }*/}
      {/*      label="Finished"*/}
      {/*    />*/}
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

export default WriterStatus;