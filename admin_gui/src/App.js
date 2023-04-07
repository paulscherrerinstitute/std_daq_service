import React, { useState, useEffect } from 'react';
import axios from 'axios';

import {
  Chip,
  Grid,
  Stack,
  Alert,
  FormControl,
  FormLabel,
  FormGroup,
  FormControlLabel,
  Checkbox,
  TextField, Paper, Typography
} from '@mui/material';

function App() {
  const [state, setState] = useState('unknown');
  const [isVideoLoaded, setIsVideoLoaded] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      const result = await axios(
        '/status'
      );
      setState(result.data)
    };

    const interval = setInterval(() => {
      fetchData();
    }, 500);

    return () => clearInterval(interval);
  }, []);

  const handleVideoLoadError = () => {
    setIsVideoLoaded(false);
  };

  return (
    <Grid container spacing={2}>
      <Grid item xs={4}>
          <Paper sx={{ p: 2 }}>
            <TextField fullWidth disabled margin="dense" variant="outlined" label="Status" value={state.status}/>
            <TextField fullWidth disabled margin="dense" variant="outlined" label="Message" value={state.status}/>
            <FormControl component="fieldset">
              <FormLabel component="legend">Writer State</FormLabel>
              <FormGroup>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={"A" === "READY"}
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
      </Grid>
      <Grid item xs={8}>
        {isVideoLoaded ? (
          <img
            src="https://example.com/mjpeg-video-stream"
            alt="Live video stream"
            onError={handleVideoLoadError}
          />
        ) : (
          <Alert severity="error">Live stream failed. Try to reload page.</Alert>
        )}
      </Grid>
    </Grid>
  );
}

export default App;
