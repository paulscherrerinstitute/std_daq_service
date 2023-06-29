import React, { useEffect, useState } from 'react';
import { Box, Slider, Typography, Paper } from '@mui/material';
import axios from 'axios';

const FileViewer = ({ fileId }) => {
  const [imageIndex, setImageIndex] = useState(0);
  const [metadata, setMetadata] = useState(null);

  useEffect(() => {
    axios.get(`/file/${fileId}`)
      .then(response => {
        setMetadata(response.data);
      });
  }, [fileId]);

  const handleSliderChange = (event, newValue) => {
    setImageIndex(newValue);
  };

  return (
    <Paper sx={{ p: 2 }} elevation={3}>
      <Typography variant="h6" gutterBottom>File viewer</Typography>
      <Box display="flex" flexDirection="column" alignItems="center">
        {metadata && (
          <Box>
            <Typography variant="body1">Number of images: {metadata.n_images}</Typography>
            <Typography variant="body1">Image height: {metadata.image_height}</Typography>
            <Typography variant="body1">Image width: {metadata.image_width}</Typography>
            <Typography variant="body1">Data type: {metadata.dtype}</Typography>
          </Box>
        )}
        <Slider
          defaultValue={0}
          step={1}
          marks
          min={0}
          max={metadata ? metadata.n_images : 0}
          value={imageIndex}
          onChange={handleSliderChange}
        />
        <img src={`/file_view/${fileId}/image/${imageIndex}`} alt={`Image ${imageIndex}`} style={{ width: '100%', height: 'auto' }} />
      </Box>
    </Paper>
  );
};

export default FileViewer;
