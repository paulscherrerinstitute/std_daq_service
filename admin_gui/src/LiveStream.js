import React, {useState} from 'react';
import LaunchIcon from '@material-ui/icons/Launch';
import SettingsIcon from '@material-ui/icons/Settings'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import {
  Chip,
  Grid,
  Paper,
  Typography,
  Accordion,
  AccordionDetails,
  AccordionSummary,
  TextField,
  Button, Alert
} from '@mui/material';

function DaqStats(props) {
  const { state } = props;
  const [isVideoLoaded, setIsVideoLoaded] = useState(true);

  const handleVideoLoadError = () => {
    setIsVideoLoaded(false);
  };

  return (
    <Paper sx={{ p: 2 }} elevation={3}>
      <Typography variant="h6" gutterBottom>Live stream</Typography>
      {isVideoLoaded ? (
        <img src="http://127.0.0.1:5001/live" alt="Live video stream"
             onError={handleVideoLoadError}
            style={{top: 0, left: 0, width: '100%', height: 'auto' }} />

        ) : (
          <Alert severity="error">Live stream failed. Try to reload page.</Alert>
        )}

    </Paper>
  );
}

export default DaqStats;