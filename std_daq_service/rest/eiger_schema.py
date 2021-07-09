eiger_schema = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "required": [ "det_name", "config"],
  "properties": {
    "det_name": {"type": "string"},
    "config": {
      "type": "object",
      "properties": {
        "n_cycles": {
          "type": "integer"
        },
        "triggers": {
          "type": "integer"
        },
        "timing": {
          "type": "string"
        },
        "n_frames": {
          "type": "integer"
        },
        "period": {
          "type": "integer"
        },
        "exposure_time": {
          "type": "integer"
        },
        "dynamic_range": {
            "type": "array",
            "items": {
                "type": "number",
                "enum": [8, 16, 32],
                "maxItems": 1
            }
        }
      }
    }
  }
}