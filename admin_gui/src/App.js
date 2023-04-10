import React, { useState, useEffect } from 'react';
import axios from 'axios';
import AcquisitionStatus from './AcquisitionStatus'
import HourglassTopIcon from '@mui/icons-material/HourglassTop';
import EditIcon from '@mui/icons-material/Edit';

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
import WriterControl from "./WriterControl";
import DaqConfig from "./DaqConfig";
import DaqStats from "./DaqStats";

function App() {
  const [state, setState] = useState({
    status: "",
    message: "",
    writer: {
      state: "",
      acquisition: {
        info: {},
        stats: {n_write_completed: 0, n_write_requested: 0, start_time: null, stop_time: null}
      }
    },
    config: { config:{
      detector_type: '', detector_name: '', bit_depth: 0, image_pixel_height: 0, image_pixel_width: 0,
      n_modules: 0, start_udp_port: 0 }}
  });
  const [isVideoLoaded, setIsVideoLoaded] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      const result = await axios(
        'http://localhost:5000/status'
      );

      const result_config = await axios(
        'http://localhost:5000/config'
      );

      let new_data = result.data;
      new_data.config = result_config.data;
      setState(new_data);
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
      <Grid item xs={3}>
        <WriterControl state={state.writer} />
        <AcquisitionStatus state={state.writer.acquisition} />
      </Grid>
      <Grid item xs={6}>
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
      <Grid item xs={3}>
        <DaqStats state={state.config.config} />
        <DaqConfig state={state.config.config} />
      </Grid>
    </Grid>
  );
}

export default App;
