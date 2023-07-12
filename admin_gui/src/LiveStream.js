import React, {useState} from 'react';
import { Paper, Typography, Alert } from '@mui/material';

function DaqStats() {
  const [isVideoLoaded, setIsVideoLoaded] = useState(true);

  const handleVideoLoadError = () => {
    setIsVideoLoaded(false);
  };

  return (
    <Paper sx={{ p: 2 }} elevation={3}>
      <Typography variant="h6" gutterBottom>Live stream</Typography>
      {isVideoLoaded ? (
        <img src="/daq/live" alt="Live video stream"
             onError={handleVideoLoadError}
            style={{top: 0, left: 0, width: '100%', height: 'auto' }} />

        ) : (
          <Alert severity="error">Live stream failed. Try to reload page.</Alert>
        )}

    </Paper>
  );
}

export default DaqStats;