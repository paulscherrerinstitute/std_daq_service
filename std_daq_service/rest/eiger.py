from slsdet import Eiger
from slsdet.enums import timingMode, speedLevel, runStatus
from jsonschema import validate, exceptions

def get_eiger_config(det_name):
    response = {}
    try:
        d = Eiger()
    except RuntimeError as e:
        response['response'] = 'Problem connecting to the detector.'
    else:
        response['det_name'] = 'EIGER'
        response['triggers'] = d.triggers
        response['timing'] = str(d.timing)
        response['frames'] = d.frames
        response['period'] = d.period
        response['exptime'] = d.exptime
        response['dr'] = d.dr
        response['tengiga'] = d.tengiga
        response['speed'] = str(d.speed)
        response['threshold'] = d.threshold
    return response

def is_valid_detector_config(config):
    try:
        validate(instance=config, schema=eiger_schema)
    except exceptions.ValidationError as err:
        return False
    return True

def set_eiger_config(config):
    response = {'response': 'request_success'}
    # verify if it's a valid config
    if not is_valid_detector_config(config):
        response = {'response': 'Detector configuration not valid.'}
    if config['det_name'].upper() == "EIGER":
        try:
            d = Eiger()
        except RuntimeError as e:
            response['response'] = 'Problem connecting to the detector.'
        else:
            eiger_config = config['config']
            not_good_params = []
            for param in eiger_config:
                if not validate_det_param(param):
                    not_good_params.append(param)
                if param == "triggers":
                    d.triggers = eiger_config[param]
                if param == "timing":
                    # [Eiger] AUTO_TIMING, TRIGGER_EXPOSURE, GATED, BURST_TRIGGER
                    if eiger_config[param].upper() == "AUTO_TIMING":
                        d.timing = timingMode.AUTO_TIMING
                    if eiger_config[param].upper() == "TRIGGER_EXPOSURE":
                        d.timing = timingMode.TRIGGER_EXPOSURE
                    if eiger_config[param].upper() == "GATED":
                        d.timing = timingMode.GATED
                    if eiger_config[param].upper() == "BURST_TRIGGER":
                        d.timing = timingMode.BURST_TRIGGER
                if param == "frames":
                    d.frames = eiger_config[param]
                if param == "tengiga":
                    d.tengiga = eiger_config[param]
                if param == "speed":
                    # [Eiger] [0 or full_speed|1 or half_speed|2 or quarter_speed]
                    if isinstance(eiger_config[param], int):
                        if eiger_config[param] == 0:
                            d.speed = speedLevel.FULL_SPEED
                        elif eiger_config[param] == 1:
                            d.speed = speedLevel.HALF_SPEED
                        elif eiger_config[param] == 2:
                            d.speed = speedLevel.QUARTER_SPEED
                    elif isinstance(eiger_config[param], str):
                        if eiger_config[param].upper() == "FULL_SPEED":
                            d.speed = speedLevel.FULL_SPEED
                        elif eiger_config[param].upper() == "HALF_SPEED":
                            d.speed = speedLevel.HALF_SPEED
                        elif eiger_config[param].upper() == "QUARTER_SPEED":
                            d.speed = speedLevel.QUARTER_SPEED
                if param == "period":
                    d.period = eiger_config[param]
                if param == "exptime":
                    d.exptime = eiger_config[param]
                if param == "dr":
                    d.dr = eiger_config[param]
            if len(not_good_params) != 0:
                params_str = ""
                for p in not_good_params:
                    params_str += p+" "
                response = {'response': 'Problem with parameters: '+params_str}
    return response

def set_eiger_cmd(cmd):
    response = {'response': 'request_success'}
    try:
        d = Eiger()
    except RuntimeError as e:
        response['response'] = 'Problem connecting to the detector.'
        return response
    if cmd == "START":
        if d.status == runStatus.IDLE:
            d.acquire()
            return response
        else:
            response['response'] = "Not possible to start, the detector is not idle"
            return response
    elif cmd == "STOP":
        if d.status == runStatus.RUNNING:
            d.stop()
            return response
        else:
            response['response'] = "Nothing to do, the detector is not running."
            return response
    response['response'] = f"Unknown problem when communicating with Eiger."
    return response


def validate_det_param(param):
    list_of_eiger_params = ["triggers",
                            "timing", "frames", "period", "exptime",
                            "dr", "speed", "tengiga", "threshold"]
    if param not in list_of_eiger_params:
        return False
    return True

eiger_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "required": ["det_name", "config"],
    "properties": {
        "det_name": {"type": "string"},
        "config": {
            "type": "object",
            "properties": {
                "triggers": {
                    "type": "integer"
                },
                "timing": {
                    "type": "string",
                },
                "speed": {
                    "type": "integer",
                },
                "frames": {
                    "type": "integer"
                },
                "speed": {
                    "anyOf": [
                        {"type": "integer"},
                        {"type": "string"}
                    ]
                },
                "tengiga": {
                    "type": "integer"
                },
                "period": {
                    "type": "number"
                },
                "exptime": {
                    "type": "number"
                },
                "dr": {
                    "type": "integer"
                }
            }
        }
    }
}
