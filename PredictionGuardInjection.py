import json

import requests
from langflow.field_typing.range_spec import RangeSpec
from langflow.base.io.text import TextComponent
from langflow.io import MultilineInput, SecretStrInput, FloatInput, Output
from langflow.schema.message import Message


class TextInputComponent(TextComponent):
    display_name = "Prompt Injection Guardrail"
    description = "Check text inputs for Prompt Injection."
    icon = "type"
    name = "PredictionGuardInjection"

    inputs = [
        MultilineInput(
            name="input_value",
            display_name="Text",
            info="Text to be checked for prompt injection.",
        ),
        SecretStrInput(
            name="api_key",
            display_name="Prediction Guard API Key",
            info="The Prediction Guard API Key to use.",
            required=True,
        ),
        FloatInput(
            name="threshold",
            display_name="Threshold",
            info="The threshold to block prompt injections at.",
            range_spec=RangeSpec(min=0.0, max=1.0),
        ),
    ]
    outputs = [
        Output(display_name="Message", name="text", method="text_response"),
    ]

    def text_response(self) -> Message:
        prompt = self.input_value
        predictionguard_api_key = self.api_key
        threshold = self.threshold


        url = "https://api.predictionguard.com/injection"

        headers = {
            "Authorization": "Bearer " + predictionguard_api_key,
            "Content-Type": "application/json"
        }

        data = {
            "prompt": prompt,
            "detect": True
        }

        response = requests.request(
            "POST", url, headers=headers, data=json.dumps(data)
        )

        if response.status_code == 200:
            ret = response.json()
            if ret["checks"][0]["probability"] < threshold:
                checked_text = prompt
            elif ret["checks"][0]["probability"] >= threshold:
                msg = "error: prompt injection detected."
                raise ValueError(msg)
        elif response.status_code == 429:
            checked_text = """
            Could not connect to Prediction Guard API.
            Too many requests, rate limit or quota exceeded.
            """
        else:
            # Check if there is a json body in the response. Read that in,
            # print out the error field in the json body, and raise an exception.
            err = ""
            try:
                err = response.json()["error"]
            except Exception:
                pass
            msg = "Could not check prompt injection. " + err
            raise ValueError(msg)

        return Message(
            text=checked_text,
        )