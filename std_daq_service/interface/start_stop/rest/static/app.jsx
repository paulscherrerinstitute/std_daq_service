import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactDOM from 'react-dom';
import { Chip, Grid, Stack, Alert } from '@mui/material';

function App() {
  const [state, setState] = useState('unknown');
  const [isVideoLoaded, setIsVideoLoaded] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      const result = await axios(
        'status'
      );
      setState(result.data.state);
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
        <Stack direction="row" spacing={0.5}>
          <Chip label={state} />
        </Stack>
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

ReactDOM.render(<App />, document.getElementById('root'));
//export default App;
