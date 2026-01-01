EXPERIMENT_SCHEMA = {
    "type": "object",
    "required": ["name", "procedure", "claims"],
    "additionalProperties": False,
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1
        },
        "procedure": {
            "type": "object",
            "required": ["entrypoint"],
            "additionalProperties": False,
            "properties": {
                "entrypoint": {
                    "type": "string",
                    "minLength": 1
                }
            }
        },
        "claims": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["metric", "operator", "value"],
                "additionalProperties": False,
                "properties": {
                    "metric": {
                        "type": "string",
                        "minLength": 1
                    },
                    "operator": {
                        "type": "string",
                        "enum": [">=", "<=", "=="]
                    },
                    "value": {
                        "type": "number"
                    }
                }
            }
        }
    }
}
