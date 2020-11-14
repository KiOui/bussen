import json


def decode_message(message):
    """Decode a message from json."""
    text = message.get("text", None)
    if text is not None:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}
    else:
        return {}
