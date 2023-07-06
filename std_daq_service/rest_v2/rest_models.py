import re
from enum import Enum
from time import time_ns
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, validator


class WriteRequest(BaseModel):
    n_images: int = Field(..., description="Number of images to acquire", example=100, ge=1)
    output_file: str = Field(..., description="Output file (absolute path or null if no acquisition happened)",
                             example="/tmp/test.h5")
    run_id: int = Field(default_factory=lambda: time_ns(), example=1684930336122153839,
                        description="Run ID (Optional field: if not provided set to request timestamp)")

    @validator('output_file')
    def validate_output_file(cls, output_file):
        if not output_file.startswith('/'):
            raise RuntimeError(f'Invalid output_file={output_file}. Path must be absolute - starts with "/".')

        path_validator = '\/[a-zA-Z0-9_\/-]*\..+[^\/]$'
        if not re.compile(path_validator).match(output_file):
            raise RuntimeError(f'Invalid output_file={output_file}. Must be a valid posix path.')


class AcquisitionStats(BaseModel):
    n_write_completed: int = Field(..., description="Number of completed writes", example=100)
    n_write_requested: int = Field(..., description="Number of requested writers from the driver", example=100)
    start_time: Optional[float] = Field(None, description="Start time of request as seen by writer driver "
                                                          "(Unix timestamp)", example=1684930336.1252322)
    stop_time: Optional[float] = Field(None, description="Stop time of request as seen by writer driver "
                                                         "(Unix timestamp)", example=1684930345.2723851)


class AcquisitionState(str, Enum):
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    WRITING = "WRITING"
    WAITING_IMAGES = "WAITING_IMAGES"
    ACQUIRING_IMAGES = "ACQUIRING_IMAGES"
    FLUSHING_IMAGES = "FLUSHING_IMAGES"


class AcquisitionLog(BaseModel):
    state: AcquisitionState = Field(..., example="FINISHED",
                                    description=(
                                        "State of the acquisition."
                                        "FINISHED: The acquisition has finished successfully. "
                                        "FAILED: The acquisition has failed. "
                                        "WRITING: Currently receiving and writing images. "
                                        "WAITING_IMAGES: Writer is ready and waiting for images. "
                                        "ACQUIRING_IMAGES: DAQ is receiving images but writer is not writing them yet. "
                                        "FLUSHING_IMAGES: All needed images acquired, writer is flushing the buffer.")
                                    )
    message: str = Field(..., description="User displayable message from the writer "
                                          "(Completed., Interrupted., ERROR:...)", example="Completed.")
    info: WriteRequest = Field(..., description="Write request that generated this acquisition")
    stats: AcquisitionStats = Field(..., description="Stats of the acquisition")


class WriterState(str, Enum):
    READY = "READY"
    WRITING = "WRITING"
    UNKNOWN = "UNKNOWN"


class WriterStatus(BaseModel):
    state: WriterState = Field(
        ...,
        description=(
            "State of the writer. "
            "READY: DAQ is ready to start writing. "
            "WRITING: DAQ is writing at the moment. Wait for it to finish or call Stop to interrupt. "
            "UNKNOWN: The DAQ is in an unknown state (usually after reboot). Call Stop to reset."
        )
    )
    acquisition: Optional[AcquisitionLog] = Field(None, description="Stats about the currently running or last "
                                                                    "finished acquisition")


class ApiStatus(str, Enum):
    OK = 'ok'
    ERROR = 'error'


class WriterResponse(BaseModel):
    status: ApiStatus = Field(..., description='Api request status.'
                                               'OK: The request completed without API errors.'
                                               'ERROR: An error occurred in the API. Check message for details.',
                              example='ok')
    message: str = Field(..., description="Human readable result of API action. Exception message in case of ERROR.",
                         example='DAQ configuration changed.')
    writer: WriterStatus = Field(..., description="Status of the writer.")


class SimResponse(BaseModel):
    pass


class ConfigResponse(BaseModel):
    pass


class StreamStats(BaseModel):
    bytes_per_second: float
    images_per_second: float


class DaqStats(BaseModel):
    detector: StreamStats
    writer: StreamStats


class StatsResponse(BaseModel):
    status: ApiStatus = Field(..., description='Api request status.'
                                               'OK: The request completed without API errors.'
                                               'ERROR: An error occurred in the API. Check message for details.',
                              example='ok')
    message: str = Field(..., description="Human readable result of API action. Exception message in case of ERROR.",
                         example='DAQ configuration changed.')
    stats: DaqStats = Field(..., description="DAQ statistics.")


class LogsResponse(BaseModel):
    status: ApiStatus = Field(..., description='Api request status.'
                                               'OK: The request completed without API errors.'
                                               'ERROR: An error occurred in the API. Check message for details.',
                              example='ok')
    message: str = Field(..., description="Human readable result of API action. Exception message in case of ERROR.",
                         example='DAQ configuration changed.')
    logs: List[AcquisitionLog] = Field(..., description="List of logs. The number equals to the requested number."
                                                        "Empty list if no logs exist.")


class DeploymentStatusEnum(str, Enum):
    UNKNOWN = 'UNKNOWN'
    SUCCESS = 'SUCCESS'
    ERROR = 'ERROR'
    RUNNING = 'RUNNING'


class DeploymentStats(BaseModel):
    start_time: float = Field(..., description="Start time of the deployment", example=1685090990.182)
    stop_time: float = Field(..., description="End time of the deployment", example=1685090990.347)


class DeploymentStatus(BaseModel):
    config_id: Optional[str] = Field(None, description="Configuration id -> timestamp of the config change.",
                                     example="1685090990182-0")
    status: DeploymentStatusEnum = Field(..., description="Current status of the deployment.", example="SUCCESS")
    message: str = Field(..., description="User displayable message", example="Deployment successful")
    servers: Optional[Dict[str, str]] = Field(None,
                                              description="Dictionary of server that replied to the config change.",
                                              example={"xbl-daq-28": "Done", "xbl-daq-29": "Done"})
    stats: Optional[DeploymentStats] = Field(None, description="Statistics regarding the deployment")

    class Config:
        description = "If the config_id is None, there are currently no config deployments in the database. " \
                      "Deploy a config file via the admin interface."


class DeploymentStatusResponse(BaseModel):
    status: ApiStatus = Field(..., description='Api request status.'
                                               'OK: The request completed without API errors.'
                                               'ERROR: An error occurred in the API. Check message for details.',
                              example='ok')
    message: str = Field(..., description="Human readable result of API action. Exception message in case of ERROR.",
                         example='DAQ configuration changed.')

    deployment: DeploymentStatus = Field(..., description="Status of the deployment.")


class ConfigRequest(BaseModel):
    pass
