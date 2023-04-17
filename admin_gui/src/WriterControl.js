import React from 'react';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import axios from 'axios';

import {
  Chip,
  Grid,
  Paper,
  Typography,
    Accordion,
  AccordionDetails,
  AccordionSummary,
    TextField,
    Button,
    Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions
} from '@mui/material';

function WriterControl(props) {
  const { state } = props;
  const [numImages, setNumImages] = React.useState(100);
  const [outputFolder, setOutputFolder] = React.useState('/tmp/');
  const [open, setOpen] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState('');
  const [filename_suffix, setFilenameSuffix] = React.useState('eiger');
  const [filename_example, setFilenameExample] = React.useState(generate_filename(generate_run_id(), filename_suffix));

  let status_chip;


  let start_button_disabled = true;
  let stop_button_disabled = true;

  switch (state.state) {
    case 'READY':
      status_chip = <Chip variant="outlined" label="Ready" color="success" />;
      start_button_disabled = false;
      break;
    case 'WRITING':
      status_chip = <Chip variant="outlined" label="Writing" color="info" />;
      stop_button_disabled = false;
      break;
    default:
      status_chip = <Chip variant="outlined" label="..." color="error" />;
      break;
  };

  function generate_run_id() {
    const now = new Date();
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, '0');
    const day = now.getDate().toString().padStart(2, '0');
    const hour = now.getHours().toString().padStart(2, '0');
    const minute = now.getMinutes().toString().padStart(2, '0');
    const second = now.getSeconds().toString().padStart(2, '0');
    const millisecond = now.getMilliseconds().toString().padStart(3, '0');
    const timestamp = `${year}${month}${day}_${hour}${minute}${second}.${millisecond}`;
    return timestamp;
  }

  function generate_filename(run_id, suffix) {
    return `${run_id}_${suffix}.h5`;
  }

  const handleStartClick = () => {
    const run_id = generate_run_id();

    axios.post('http://localhost:5000/writer/write_async', {
      n_images: numImages,
      run_id: run_id,
      output_file: (outputFolder.endsWith("/") ? outputFolder.slice(0, -1) : outputFolder) + '/' + generate_filename(run_id, filename_suffix),
    }).then(response => {
        if (response.data.status === "error") {
          setErrorMessage(response.data.message);
          setOpen(true);
        }
      })
      .catch(error => {
        setErrorMessage(error.response.data.message);
        setOpen(true);
      });
  };

  const handleCloseErrorDialog = () => {
    setOpen(false);
  };

  const handleStopClick = () => {
    axios.post('http://localhost:5000/stop')
      .then(response => {
        if (response.data.status === "error") {
          setErrorMessage(response.data.message);
          setOpen(true);
        }
      })
      .catch(error => {
        setErrorMessage(error.response.data.message);
        setOpen(true);
      });
  };

  const handleNumImagesChange = (event) => {
    setNumImages(event.target.value);
  };

  const handleFilenameSuffixChange = (event) => {
    setFilenameSuffix(event.target.value);
    setFilenameExample(generate_filename(generate_run_id(), event.target.value));
  }

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

      <Grid item sx={{ my: 2 }}>
        <TextField label="Filename suffix" type="text" defaultValue={filename_suffix} fullWidth onChange={handleFilenameSuffixChange}/>
        <Typography variant="caption" color="textSecondary">Example: {filename_example}</Typography>
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


      <Dialog open={open} onClose={handleCloseErrorDialog}>
        <DialogTitle>Error</DialogTitle>
        <DialogContent>
          <DialogContentText>{errorMessage}</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseErrorDialog}>Close</Button>
        </DialogActions>
      </Dialog>

    </Paper>
  );
}

export default WriterControl;