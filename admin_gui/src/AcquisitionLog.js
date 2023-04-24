import React, { useEffect, useState } from 'react';
import axios from "axios";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Chip,
  Alert
} from '@mui/material';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import AttachFileIcon from '@mui/icons-material/AttachFile';

function AcquisitionLog() {
  const [acqs, setAcqs] = useState([]);
  const [restError, setRestError] = useState(false);
  const [restErrorText, setRestErrorText] = useState("Unknown")

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

    if (message === "Completed") {
      return "success";
    }

    if (message === "Interrupted") {
      return "warning";
    }

    if (message.startsWith('Error')) {
      return "error";
    }
  }

  return (
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
              <TableCell style={{ width: '50px' }}>Actions</TableCell>
              <TableCell style={{ width: '140px' }}>Stop time</TableCell>
              <TableCell style={{ width: '50px' }}>Images</TableCell>
              <TableCell style={{ width: '50px' }}>Duration</TableCell>
              <TableCell>Message</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {acqs.map((acq, index) => (
              <TableRow key={index}>
               <TableCell style={{ width: '50px' }}>
                  <AttachFileIcon fontSize="small"/>
                  <InfoOutlinedIcon fontSize="small"/>
                </TableCell> <TableCell style={{ width: '140px' }}>{formatTimestamp(acq.stats.stop_time)}</TableCell>
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
  )
}

export default AcquisitionLog;
