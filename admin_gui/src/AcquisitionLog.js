import React, { useEffect, useState } from 'react';
import axios from "axios";
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Typography, Chip, Alert, Tooltip,
    Modal, Box
} from '@mui/material';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import AssessmentIcon from '@mui/icons-material/Assessment';
import Button from "@mui/material/Button";
import FileViewer from "./FileViewer";



function AcquisitionLog() {
  const [acqs, setAcqs] = useState([]);
  const [restError, setRestError] = useState(false);
  const [restErrorText, setRestErrorText] = useState("Unknown")
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isFileViewerOpen, setIsFileViewerOpen] = useState(false);
  const [currentAcquisitionId, setCurrentAcquisitionId] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await axios.get('/daq/logs/5');

        if (result.data.status === 'ok') {
          setAcqs(result.data.logs);
          setRestError(false);
        } else {
          setRestError(true);
          setRestErrorText(result.data.message);
          console.log(result.data);
        }

      } catch (error) {
        setRestError(true);
        setRestErrorText(error.message);
        console.log(error);
      }
    }

    const interval = setInterval(() => {
      fetchData();
    }, 500);

    return () => clearInterval(interval);
  }, []);

  function formatTimestamp(unixTimestamp) {
    if (unixTimestamp === null) {
      return "N/A";
    }
    const date = new Date(unixTimestamp * 1000);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    const second = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
  }

  function get_duration(acq) {
    return acq.stats.stop_time - acq.stats.start_time;
  }

  function get_color_for_message(message) {
    if (!message) {
      return "error";
    }

    if (message === "Completed.") {
      return "success";
    }

    if (message === "Interrupted.") {
      return "warning";
    }

    if (message.startsWith('ERROR:')) {
      return "error";
    }
  }

  const onClose = () => {
    setIsModalOpen(false);
  }

  const openFileViewer = (acquisition_id) => {
    setCurrentAcquisitionId(acquisition_id);
    setIsFileViewerOpen(true);
  }

  const closeFileViewer = () => {
    setIsFileViewerOpen(false);
  }

  return (
      <div>
    <Paper sx={{ p: 2 }} elevation={3}>
      <Typography variant="h6" gutterBottom>Acquisition Log</Typography>
      {restError ? (
           <Alert severity="error">Log loading failed. Error message: {restErrorText}</Alert>
          ) : (
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              {/*<TableCell style={{ width: '50px' }}></TableCell>*/}
              <TableCell style={{ width: '60px' }}>Actions</TableCell>
              <TableCell style={{ width: '140px' }}>Stop time</TableCell>
              <TableCell style={{ width: '50px' }}>Images</TableCell>
              <TableCell style={{ width: '50px' }}>Duration</TableCell>
              <TableCell>Message</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(acqs).map(([log_id, acq]) => (
              <TableRow key={log_id}>
               <TableCell style={{ width: '50px' }}>
                  <Tooltip title={<Typography variant="body2">Open file</Typography>}>
                    <AttachFileIcon fontSize="small" style={{cursor: 'pointer'}}
                                    onClick={() => openFileViewer(log_id)}/>
                  </Tooltip>
                 <Tooltip title={
                   <div>
                    <Typography variant="body2">Output file: {acq.info.output_file}</Typography>
                    <Typography variant="body2">Run ID: {acq.info.run_id}</Typography>
                    <Typography variant="body2">Requested images: {acq.stats.n_write_requested}</Typography>
                    <Typography variant="body2">Written images: {acq.stats.n_write_completed}</Typography>
                  </div>
                 }>
                    <InfoOutlinedIcon fontSize="small" sx={{ color: 'primary.main' }}/>
                 </Tooltip>
                 <Tooltip title={<Typography variant="body2">
                   {acq.reports.length > 0 ? "Show details" : "Show details"}</Typography>}>
                   <AssessmentIcon fontSize="small" onClick={() => setIsModalOpen(true)} sx={{ cursor: 'pointer',
                     color: acq.reports.length > 0 ? 'success.main': '' }} />
                 </Tooltip>
               </TableCell>
                <TableCell style={{ width: '140px' }}>{formatTimestamp(acq.stats.stop_time)}</TableCell>
                <TableCell align="right" style={{ width: '50px' }}>{acq.info.n_images}</TableCell>
                <TableCell align="right" style={{ width: '50px' }}>{get_duration(acq).toFixed(2)}s</TableCell>
                <TableCell>
                  <Chip label={acq.message || "N/A"} color={get_color_for_message(acq.message)} size="small" />
                  </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
          )}
    </Paper>

    <Modal open={isModalOpen} onClose={onClose}>
          <Box
            sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', bgcolor: 'background.paper',
              boxShadow: 24, p: 4, maxWidth: '90%', maxHeight: '90%', overflow: 'auto', width: '480px' }} >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h5" component="h2">Acquisition details</Typography>
            </Box>
            <Paper sx={{ p: 2 }} elevation={3}>
              <Typography variant="h6" gutterBottom>Status</Typography>
            </Paper>
            <Paper sx={{ p: 2 }} elevation={3}>
              <Typography variant="h6" gutterBottom>Request info</Typography>
            </Paper>
            <Paper sx={{ p: 2 }} elevation={3}>
              <Typography variant="h6" gutterBottom>Reports</Typography>
            </Paper>
            <Paper sx={{ p: 2 }} elevation={3}>
              <Typography variant="h6" gutterBottom>Stats</Typography>
            </Paper>

            <Box mt={4}>
              <Button variant="contained" color="primary" onClick={onClose} sx={{ ml: 2 }} > Close </Button>
            </Box>
          </Box>
        </Modal>

        <FileViewer acquisition_id={currentAcquisitionId} isOpen={isFileViewerOpen} onClose={closeFileViewer} />
        </div>
  )
}

export default AcquisitionLog;
