import React from 'react';
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
    Button
} from '@mui/material';

function WriterControl(props) {
  const { state } = props;
  const [numImages, setNumImages] = React.useState(100);
  const [outputFolder, setOutputFolder] = React.useState('/tmp/');
  let status_chip;

  let start_button_disabled = true;
  let stop_button_disabled = true;

  switch (state.state) {
    case 'READY':
      status_chip = <Chip variant="outlined" label="Ready" color="success" />;
      start_button_disabled = false;
      break;
    case 'WRITING':
      status_chip = <Chip variant="outlined" label="Writing" color="error" />;
      stop_button_disabled = false;
      break;
    default:
      status_chip = <Chip variant="outlined" label="Unknown" color="error" />;
      break;
  };



  const handleStartClick = () => {
    // Send JSON request to REST API with numImages and outputFolder values
    console.log('Start button clicked!');
    console.log('Num Images: ', numImages);
    console.log('Output Folder: ', outputFolder);
  };

  const handleStopClick = () => {
    // Send JSON request to REST API to stop writing process
    console.log('Stop button clicked!');
  };

  const handleNumImagesChange = (event) => {
    setNumImages(event.target.value);
  };

  const handleOutputFolderChange = (event) => {
    setOutputFolder(event.target.value);
  };

  return (
    <Paper sx={{ p: 2 }} elevation={3}>
      <Typography variant="h6" gutterBottom>Writer control</Typography>

      <Grid container alignItems="center" spacing={1}>
        <Grid item> <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Status:</Typography></Grid>
        <Grid item> {status_chip} </Grid>
        <Grid item>
          <Button
            variant="contained"
            onClick={handleStartClick}
            disabled={start_button_disabled}
            sx={{ ml: 2, bgcolor: 'success.main', color: 'white' }}
          >
            Start
          </Button>
          <Button
            variant="contained"
            onClick={handleStopClick}
            disabled={stop_button_disabled}
            sx={{ ml: 2, bgcolor: 'error.main', color: 'white' }}
          >
            Stop
          </Button>
        </Grid>
      </Grid>

      <Accordion sx={{ mt: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />} aria-controls="status-content" id="status-header">
          <Grid container alignItems="center" spacing={1}>
            <Grid item> <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Settings:</Typography></Grid>
            <Grid item> <Typography variant="subtitle2">{numImages} images</Typography></Grid>
          </Grid>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Number of Images"
                type="number"
                value={numImages}
                onChange={handleNumImagesChange}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} md={12}>
              <TextField
                label="Output Folder"
                type="text"
                value={outputFolder}
                onChange={handleOutputFolderChange}
                fullWidth
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

    </Paper>
  );
}

export default WriterControl;