import React, { useState, useEffect } from 'react';
import axios from 'axios';
import WriterStatus from './WriterStatus'
import HourglassTopIcon from '@mui/icons-material/HourglassTop';

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
  const [state, setState] = useState({
    status: "",
    message: ""
  });
  const [isVideoLoaded, setIsVideoLoaded] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      const result = await axios(
        'http://localhost:5000/status'
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
        <WriterStatus state={state} />
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
