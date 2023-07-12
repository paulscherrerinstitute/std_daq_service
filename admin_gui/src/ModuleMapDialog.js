import React, { useEffect, useState } from "react";
import axios from 'axios';
import {Box, Typography, LinearProgress, Modal, Paper} from "@mui/material";
import Button from "@mui/material/Button";

function LinearProgressWithLabel(props) {
  return (
    <Box display="flex" alignItems="center">
      <Box width="100%" mr={1}>
        <LinearProgress variant="determinate" {...props} />
      </Box>
      <Box minWidth={35}>
        <Typography variant="body2" color="text.primary">{`${Math.round(
          props.value,
        )}%`}</Typography>
      </Box>
    </Box>
  );
}

export default function ModuleMapDialog({ open, handleClose, log_id, i_image }) {
  const [buffer, setBuffer] = useState(null);
  const [loaded, setLoaded] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (open) {
      axios({
        method: 'get',
        url: `/file/${log_id}/${i_image}?module_map=1`,
        responseType: 'arraybuffer',
        onDownloadProgress: function (progressEvent) {
          setProgress((progressEvent.loaded / progressEvent.total) * 100);
        },
      }).then(function (response) {
        let blob = new Blob([response.data], { type: response.headers['content-type'] });
        let url = URL.createObjectURL(blob);
        setBuffer(url);
        setLoaded(true);
      });
    }
  }, [open]);

  return (
      <Modal open={open} onClose={handleClose}>
        <Box
            sx={{bgcolor: 'background.paper', position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
              boxShadow: 24, p: 4, maxWidth: '100%', maxHeight: '100%', overflow: 'auto'}} >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h5" component="h2"> Module map </Typography>
                <Typography variant="body2" component="body2"> i_image={i_image} </Typography>
              </Box>
          <Paper sx={{ p: 2 }} elevation={3}>
              {!loaded ?
                  <LinearProgressWithLabel value={progress} />
                  :
                  <img src={buffer} style={{ objectFit: "contain", maxHeight: "600px", maxWidth: "1000px" }} alt="Module Map" />
              }
          </Paper>
            <Box mt={4}>
              <Button variant="contained" color="error" onClick={handleClose} sx={{ ml: 2 }} > Close </Button>
            </Box>
        </Box>
        </Modal>
  );
}
