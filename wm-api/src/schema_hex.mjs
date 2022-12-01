export default {
    "$id": "https://westmarches.ishtanzar.net/hex.schema.json",
    "title": "Hex",
    "description": "A Hex of the West Marches",
    "type": "object",
    "anyOf": [
        {
            "properties": {
                "hexmap": { "$ref": "#/$defs/hexmap" }
            },
            "required": [ "hexmap" ]
        },
        { "$ref": "#/$defs/hex" }
    ],
    "$defs": {
        "hex": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "integer"
                },
                "y": {
                    "type": "integer"
                },
                "charted": {
                    "description": "Has the Hex been charted",
                    "type": "boolean"
                }
            },
            "required": [ "x", "y", "charted" ]
        },
        "hexmap": {
            "type": "array",
            "items": { "$ref": "#/$defs/hex" }
        }
    }
}