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