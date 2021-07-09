eiger_schema = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "required": [ "det_name", "config"],
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
        "n_frames": {
          "type": "integer"
        },
        "period": {
          "type": "integer"
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