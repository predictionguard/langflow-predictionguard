import json

import requests
from langflow.field_typing.range_spec import RangeSpec
from langflow.base.io.text import TextComponent
from langflow.io import MultilineInput, Output
from langflow.schema.message import Message


class TextOutputComponent(TextComponent):
    display_name = "Toxicity Guardrail"
    description = "Check text outputs for toxicity."
    icon = "type"
    name = "PredictionGuardToxicity"

    inputs = [
        MultilineInput(
            name="input_value",
            display_name="Text",
            info="Text to be checked for toxicity.",
        ),
        SecretStrInput(
            name="api_key",
            display_name="Prediction Guard API Key",
            info="The Prediction Guard API Key to use.",
            advanced=False,
            required=True,
        ),
        FloatInput(
            name="threshold",
            display_name="Threshold",
            info="The threshold to toxic outputs at.",
            range_spec=RangeSpec(min=0.0, max=1.0),
        ),
    ]
    outputs = [
        Output(display_name="Message", name="text", method="text_response"),
    ]

    def text_response(self) -> Message:
        text = self.input_value
        predictionguard_api_key = self.api_key
        threshold = self.threshold

        url = "https://api.predictionguard.com/toxicity"
        headers = {
            "Authorization": "Bearer " + predictionguard_api_key,
            "Content-Type": "application/json"
        }

        data = {
            "text": text,
        }

        response = requests.request(
            "POST", url, headers=headers, data=json.dumps(data)
        )

        if response.status_code == 200:
            ret = response.json()
            if ret["checks"][0]["score"] < threshold:
                checked_text = text
            elif ret["checks"][0]["score"] >= threshold:
                msg = "error: toxic output detected."
                raise ValueError(msg)
        elif response.status_code == 429:
            msg = """
            Could not connect to Prediction Guard API.
            Too many requests, rate limit or quota exceeded.
            """
            raise ValueError(msg)
        else:
            # Check if there is a json body in the response. Read that in,
            # print out the error field in the json body, and raise an exception.
            err = ""
            try:
                err = response.json()["error"]
            except Exception:
                pass
            msg = "Could not check for toxicity. " + err
            raise ValueError(msg)

        message = Message(
            text=checked_text,
        )

        return message