import React, { useEffect, useState } from 'react';
import axios from "axios";
import {Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Typography, Chip} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';

function AcquisitionLog() {
  const [acqs, setAcqs] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await axios.get('http://localhost:5000/logs');
        setAcqs(result.data.stats);
      } catch (error) {
        console.error('Error fetching acquisition log:', error);
      }
    };

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

  return (
    <Paper sx={{ p: 2 }} elevation={3}>
      <Typography variant="h6" gutterBottom>Acquisition Log</Typography>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell style={{ width: '50px' }}></TableCell>
              <TableCell style={{ width: '140px' }}>Stop time</TableCell>
              <TableCell style={{ width: '50px' }}>Images</TableCell>
              <TableCell>Message</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {acqs.map((acq, index) => (
              <TableRow key={index}>
                <TableCell style={{ width: '50px' }}><Chip label="Success" color='success' size="small" /></TableCell>
                <TableCell style={{ width: '140px' }}>{formatTimestamp(acq.stats.stop_time)}</TableCell>
                <TableCell style={{ width: '50px' }}>{acq.info.n_images}</TableCell>
                <TableCell>{acq.message || "N/A"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}

export default AcquisitionLog;
