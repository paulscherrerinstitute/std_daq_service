import React, { useEffect, useState } from 'react';
import { Box, Grid, Slider, Typography, } from '@mui/material';
import axios from 'axios';
import Button from "@mui/material/Button";
import Modal from "@mui/material/Modal";
import ModuleMapDialog from "./ModuleMapDialog";

const FileViewer = ({ log_id, isOpen, onClose }) => {
  const [imageIndex, setImageIndex] = useState(0);
  const [metadata, setMetadata] = useState(null);
  const [logId, setLogId] = useState(null);
  const [isModuleMapOpen, setIsModuleMapOpen] = useState(false);

  useEffect(() => {
    if (isOpen && log_id) {
      axios.get(`/file/${log_id}`)
        .then(response => {
            setLogId(response.data.file_metadata.log_id)
          setMetadata(response.data.file_metadata);
        });
    }
    setImageIndex(0);
  }, [log_id, isOpen]);

  const handleSliderChange = (event, newValue) => {
    setImageIndex(newValue);
  };
    const showModuleMap = () => {
        setIsModuleMapOpen(true);
  };

    const closeModuleMap = () => {
        setIsModuleMapOpen(false);
  };

  return (
      <div>
          <ModuleMapDialog open={isModuleMapOpen} handleClose={closeModuleMap}
                           log_id={logId} i_image={imageIndex}/>
        <Modal open={isOpen} onClose={onClose}>
          <Box
            sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', bgcolor: 'background.paper',
              boxShadow: 24, p: 4, maxWidth: '90%', maxHeight: '90%', overflow: 'auto', width: '700px' }} >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h5" component="h2"> File viewer </Typography>
            </Box>
              <Box display="flex" flexDirection="column" alignItems="center">
                  {metadata && (
                      <Grid container spacing={1}>
                          <Grid item xs={2}>
                              <Typography variant="body2">log_id</Typography>
                              <Typography variant="body2">filename</Typography>
                              <Typography variant="body2">file_size</Typography>
                              <Typography variant="body2">dataset_name</Typography>
                          </Grid>
                          <Grid item xs={6}>
                              <Typography variant="body2">{metadata.log_id}</Typography>
                              <Typography variant="body2">{metadata.filename}</Typography>
                              <Typography variant="body2">{(metadata.file_size/1024/1024).toFixed(2)} MB</Typography>
                              <Typography variant="body2">{metadata.dataset_name}</Typography>
                          </Grid>
                          <Grid item xs={2}>
                              <Typography variant="body2">n_images</Typography>
                              <Typography variant="body2">height</Typography>
                              <Typography variant="body2">width</Typography>
                              <Typography variant="body2">dtype</Typography>
                          </Grid>
                          <Grid item xs={2}>
                              <Typography variant="body2">{metadata.n_images}</Typography>
                              <Typography variant="body2">{metadata.image_pixel_height}</Typography>
                              <Typography variant="body2">{metadata.image_pixel_width}</Typography>
                              <Typography variant="body2">{metadata.dtype}</Typography>
                          </Grid>
                        </Grid>
                  )}
                  <Slider defaultValue={0} step={1} marks min={0} max={metadata ? metadata.n_images-1 : 0}
                          value={imageIndex} onChange={handleSliderChange} />
                  <Typography>i_image={imageIndex}</Typography>
                  <img src={`/file/${log_id}/${imageIndex}`} alt={`Image ${imageIndex}`} style={{ width: '100%', height: 'auto' }} />
              </Box>
            <Box mt={4}>
                <Button variant="contained" color="primary" onClick={showModuleMap} sx={{ ml: 2 }} >Overlay module map</Button>
              <Button variant="contained" color="error" onClick={onClose} sx={{ ml: 2 }} > Close </Button>
            </Box>
          </Box>
        </Modal>
      </div>
  );
};

export default FileViewer;
