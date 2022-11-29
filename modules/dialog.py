#!/usr/bin/env python3

import json
import logging
from os import environ

# from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLMn, AutoTokenizer
# import torch


from mqqt_client import MQTTClient
from dialog_models.blenderbot import BlenderBot

class DialogRequest():
    def __init__(self, *args, **kwargs):
        self.input = kwargs["input"]

    def json(self):
        return json.dumps(
            {
                "input": self.input,
            }
        )



class DialogModule(MQTTClient):
    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop("model")
        super().__init__(*args, **kwargs)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        super()._on_connect(client, userdata, flags, rc)
        client.subscribe("module/dialog/request/+")

    def _on_message(self, client, userdata, msg):
        client_id = self.get_client_id(msg.topic)
        j = json.loads(msg.payload)
        try:
            r = DialogRequest(**j)
        except KeyError:
            logging.error("Invalid request: {}".format(j))
            return
        if loglevel == logging.DEBUG:
            logging.debug(
                "Got request by client {}, text={}".format(
                    client_id,
                    r.input,
                )
            )

        output = model.add_input(r.input)
        self.client.publish(
            "module/dialog/response/{}".format(client_id),
            json.dumps({"text": output})
        )

if __name__ == "__main__":
    loglevel = logging.DEBUG if environ.get('DEBUG') else logging.INFO
    logging.basicConfig(level=loglevel)
    logging.info("Loading model...")
    model = BlenderBot()
    dialog = DialogModule(
        model=model,
    )
    dialog.run()