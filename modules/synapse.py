#!/usr/bin/env python3

import json
from os import environ
import logging

from mqqt_client import MQTTClient
from translate import TranslateRequest
from tts import TTSRequest
from dialog import DialogRequest


class Synapse(MQTTClient):
    def __init__(self, *args, **kwargs):
        self.input_lang = kwargs.pop("input_lang")
        self.output_lang = kwargs.pop("output_lang")
        super().__init__(*args, **kwargs)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        super()._on_connect(client, userdata, flags, rc)
        client.subscribe("module/microphone/text/+")
        client.subscribe("module/translate/response/+")
        # client.subscribe("module/translate_to/response/+")
        client.subscribe("module/dialog/response/+")

    def _on_message(self, client, userdata, msg):
        client_id = self.get_client_id(msg.topic)
        if msg.topic.startswith("module/microphone/text/"):
            r = TranslateRequest(text=msg.payload.decode(), source=self.input_lang, target="en").json()
            self.client.publish("module/translate/request/input",
            r,
            )
        elif msg.topic.startswith("module/translate/response/input"):
            j = json.loads(msg.payload)
            r = DialogRequest(input=j["text"])
            self.client.publish("module/dialog/request/{}".format(client_id), r.json())
        elif msg.topic.startswith("module/dialog/response/"):
            j = json.loads(msg.payload)
            r = TranslateRequest(text=j["text"], source="en", target=self.output_lang)
            r = TTSRequest(lang=output_lang, text=r.translate())
            self.client.publish("module/tts/request/{}".format(client_id), r.json())


if __name__ == "__main__":
    loglevel = logging.DEBUG if environ.get('DEBUG') else logging.INFO
    logging.basicConfig(level=loglevel)
    input_lang = environ.get("INPUT_LANG", "fr")
    output_lang = environ.get("OUTPUT_LANG", input_lang)
    synapse = Synapse(input_lang=input_lang, output_lang=output_lang)
    synapse.run()
