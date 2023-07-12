import React, { useEffect, useState } from "react";
import axios from 'axios';
import { Box, Dialog, DialogTitle, IconButton, Typography, LinearProgress } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

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
    <Dialog open={open} fullScreen>
      <DialogTitle>
        <b>Module map </b> i_image={i_image}
        <IconButton edge="end" color="inherit" onClick={handleClose} aria-label="close">
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      {!loaded ?
        <LinearProgressWithLabel value={progress} />
        :
        <img src={buffer} style={{ objectFit: "contain", maxHeight: "calc(100% - 128px)", maxWidth: "100%" }} alt="Module Map" />
      }
    </Dialog>
  );
}
