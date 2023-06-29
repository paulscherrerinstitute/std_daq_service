import React, { useState, useEffect } from 'react';
import axios from 'axios';
import AcquisitionStatus from './AcquisitionStatus'

import {
  Grid
} from '@mui/material';
import WriterControl from "./WriterControl";
import DaqConfig from "./DaqConfig";
import DaqStats from "./DaqStats";
import LiveStream from "./LiveStream";
import AcquisitionLog from "./AcquisitionLog";
import DaqDeployment from "./DaqDeployment";
import SimulatorControl from "./SimulatorControl";
import FileViewer from "./FileViewer";

function App() {
  const [state, setState] = useState({
    status: "...",
    message: "...",
    writer: {
      state: "...",
      acquisition: {
        info: {n_images: 0, output_file: "...", run_id: "..."},
        stats: {n_write_completed: 0, n_write_requested: 0, start_time: null, stop_time: null}
      }
    },
    config: { config:{
      detector_type: 'eiger', detector_name: '...', bit_depth: 0, image_pixel_height: 0, image_pixel_width: 0,
      n_modules: 0, writer_user_id: 0, start_udp_port: 0, module_positions: {} }}
  });


  useEffect(() => {
    const fetchData = async () => {
      const result = await axios(
        '/writer/status'
      );

      const result_config = await axios(
        '/daq/config'
      );

      let new_data = result.data;
      new_data.config = result_config.data;
      setState(new_data);
    };

    const interval = setInterval(() => {
      fetchData();
    }, 500);

    return () => clearInterval(interval);
  }, []);

  return (
    <Grid container spacing={2}>
      <Grid item xs={3}>
        <WriterControl state={state.writer} />
        <AcquisitionStatus state={state.writer.acquisition} />
      </Grid>
      <Grid item xs={6}>
        <LiveStream state={state.config.config} />
        <AcquisitionLog />
      </Grid>
      <Grid item xs={3}>
        <DaqStats state={state.config.config} />
        <DaqConfig state={state.config.config} />
        <DaqDeployment/>
        <SimulatorControl/>
      </Grid>
    </Grid>
  );
}

export default App;
