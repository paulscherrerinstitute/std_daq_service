import React, { useEffect, useState } from 'react';
import {
    Box, Slider, Typography,
} from '@mui/material';
import axios from 'axios';
import Button from "@mui/material/Button";
import Modal from "@mui/material/Modal";

const FileViewer = ({ log_id, isOpen, onClose }) => {
  const [imageIndex, setImageIndex] = useState(0);
  const [metadata, setMetadata] = useState(null);

  useEffect(() => {
    if (isOpen && log_id) {
      axios.get(`/file/${log_id}`)
        .then(response => {
          setMetadata(response.data.file_metadata);
        });
    }
  }, [log_id, isOpen]);

  const handleSliderChange = (event, newValue) => {
    setImageIndex(newValue);
  };

  return (
      <div>
        <Modal open={isOpen} onClose={onClose}>
          <Box
            sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', bgcolor: 'background.paper',
              boxShadow: 24, p: 4, maxWidth: '90%', maxHeight: '90%', overflow: 'auto', width: '700px' }} >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h5" component="h2"> File viewer </Typography>
            </Box>
              <Box display="flex" flexDirection="column" alignItems="center">
                  {metadata && (
                      <Box>
                          <Typography variant="body1">Log ID: {metadata.log_id}</Typography>
                          <Typography variant="body1">File name: {metadata.file_name}</Typography>
                          <Typography variant="body1">File size: {metadata.file_size}</Typography>
                          <Typography variant="body1">Dataset name: {metadata.dataset_name}</Typography>
                          <Typography variant="body1">Number of images: {metadata.n_images}</Typography>
                          <Typography variant="body1">Image height: {metadata.image_pixel_height}</Typography>
                          <Typography variant="body1">Image width: {metadata.image_pixel_width}</Typography>
                          <Typography variant="body1">Data type: {metadata.dtype}</Typography>
                      </Box>
                  )}
                  <Slider defaultValue={0} step={1} marks min={0} max={metadata ? metadata.n_images : 0}
                          value={imageIndex} onChange={handleSliderChange} />
                  <img src={`/file/${log_id}/image/${imageIndex}`} alt={`Image ${imageIndex}`} style={{ width: '100%', height: 'auto' }} />
              </Box>
            <Box mt={4}>
              <Button variant="contained" color="error" onClick={onClose} sx={{ ml: 2 }} > Close </Button>
            </Box>
          </Box>
        </Modal>
      </div>
  );
};

export default FileViewer;
