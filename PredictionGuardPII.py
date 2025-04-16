import json

import requests
from langflow.base.io.text import TextComponent
from langflow.io import MultilineInput, Output
from langflow.schema.message import Message


class TextInputComponent(TextComponent):
    display_name = "PII Guardrail"
    description = "Check text inputs for PII."
    icon = "type"
    name = "PredictionGuardPII"

    inputs = [
        MultilineInput(
            name="input_value",
            display_name="Text",
            info="Text to be checked for PII",
        ),
        SecretStrInput(
            name="api_key",
            display_name="Prediction Guard API Key",
            info="The Prediction Guard API Key to use.",
            advanced=False,
            required=True,
        ),
        BoolInput(
            name="replace",
            display_name="Replace",
            info="Whether to replace PII if it is present."
        ),
        StrInput(
            name="replace_method",
            display_name="PII Replace Method",
            info="What method to replace present PII with. Possible values are 'category', 'fake', 'mask', and 'random'."
        ),
    ]
    outputs = [
        Output(display_name="Message", name="text", method="text_response"),
    ]

    def text_response(self) -> Message:
        prompt = self.input_value
        predictionguard_api_key = self.api_key
        replace = self.replace
        replace_method = self.replace_method

        url = "https://api.predictionguard.com/PII"
        headers = {
            "Authorization": "Bearer " + predictionguard_api_key,
            "Content-Type": "application/json"
        }

        data = {
            "prompt": prompt,
            "replace": replace,
            "replace_method": replace_method
        }

        response = requests.request(
            "POST", url, headers=headers, data=json.dumps(data)
        )

        if response.status_code == 200:
            ret = response.json()

            if "new_prompt" in ret["checks"][0].keys():
                checked_text = ret["checks"][0]["new_prompt"]
            elif "types_and_positions" in ret["checks"][0].keys():
                checked_text = ret["checks"][0]["types_and_positions"]
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
            msg = "Could not check PII. " + err
            raise ValueError(msg)

        return Message(
            text=checked_text,
        )