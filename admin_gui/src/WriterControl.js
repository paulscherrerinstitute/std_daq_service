import React from 'react';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import RotateLeftIcon from '@mui/icons-material/RotateLeft'; 
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
    Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions,
    InputAdornment, IconButton,
    Switch, FormControlLabel
} from '@mui/material';

function WriterControl(props) {
  const { state } = props;
  const [numImages, setNumImages] = React.useState(100);
  const [outputFolder, setOutputFolder] = React.useState('/tmp/');
  const [open, setOpen] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState('');
  const [filename_suffix, setFilenameSuffix] = React.useState('eiger');
  const [filename_example, setFilenameExample] = React.useState(generate_filename(filename_suffix));
  const [enablePrefix, setEnablePrefix] = React.useState(true);

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
      stop_button_disabled = false;
      break;
  };

  function generate_filename_prefix() {
    const now = new Date();
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, '0');
    const day = now.getDate().toString().padStart(2, '0');
    const hour = now.getHours().toString().padStart(2, '0');
    const minute = now.getMinutes().toString().padStart(2, '0');
    const second = now.getSeconds().toString().padStart(2, '0');
    const millisecond = now.getMilliseconds().toString().padStart(3, '0');
    const timestamp = `${year}${month}${day}_${hour}${minute}${second}.${millisecond}_`;
    return timestamp;
  }

  function generate_filename(suffix) {
    let prefix = "";   
      if (enablePrefix) {
        prefix = generate_filename_prefix();
    }     
    return `${prefix}${suffix}.h5`;
  }

  const handleStartClick = () => {
    axios.post('/writer/write_async', {
      n_images: numImages,
      output_file: (outputFolder.endsWith("/") ? outputFolder.slice(0, -1) : outputFolder) + '/' +
          generate_filename(filename_suffix),
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
    axios.post('/writer/stop')
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
    setFilenameExample(generate_filename(event.target.value));
  }

  const handleOutputFolderChange = (event) => {
    setOutputFolder(event.target.value);
  };

  const handleCopyOutputFolder = () => {
  if (props.state.acquisition && props.state.acquisition.info) {
      if (props.state.acquisition.info.output_file) {
            const fullPath = props.state.acquisition.info.output_file;
            const lastSlashIndex = fullPath.lastIndexOf('/');
            const folderPath = fullPath.substring(0, lastSlashIndex + 1);

            setOutputFolder(folderPath);
            return;
          };
        };
    };

    const handlePrefixToggle = (event) => {
            const newEnablePrefix = event.target.checked;
            setEnablePrefix(newEnablePrefix);
            setFilenameExample(generate_filename(filename_suffix));
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
                InputProps={{ 
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton onClick={handleCopyOutputFolder} title="Load last used output folder">
                            <RotateLeftIcon />
                        </IconButton>
                    </InputAdornment>),}}
              />
      <FormControlLabel
                  control={
                                    <Switch
                                      checked={enablePrefix}
                                      onChange={handlePrefixToggle}
                                      color="primary"
                                    />
                                  }
                  label="Prefix filename with timestamp"
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
