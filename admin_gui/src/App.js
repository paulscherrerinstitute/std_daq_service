import AcquisitionStatus from './AcquisitionStatus'

import { Grid } from '@mui/material';
import WriterControl from "./WriterControl";
import DaqConfig from "./DaqConfig";
import DaqStats from "./DaqStats";
import LiveStream from "./LiveStream";
import AcquisitionLog from "./AcquisitionLog";
import DaqDeployment from "./DaqDeployment";
import SimulatorControl from "./SimulatorControl";

function App() {
  return (
    <Grid container spacing={2}>
      <Grid item xs={3}>
        <WriterControl/>
        <AcquisitionStatus/>
      </Grid>
      <Grid item xs={6}>
        <LiveStream />
        <AcquisitionLog />
      </Grid>
      <Grid item xs={3}>
        <DaqStats />
        <DaqConfig />
        <DaqDeployment/>
        <SimulatorControl/>
      </Grid>
    </Grid>
  );
}

export default App;
