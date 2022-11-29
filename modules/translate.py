#!/usr/bin/env python3

import json
import logging
from os import environ
from mqqt_client import MQTTClient

from deep_translator import GoogleTranslator


class TranslateRequest():
    def __init__(self, *args, **kwargs):
        self.source = kwargs["source"]
        self.target = kwargs["target"]
        self.text = kwargs["text"]

    def json(self):
        return json.dumps(
            {
                "source": self.source,
                "target": self.target,
                "text": self.text,
            }
        )


    def translate(self):
        return GoogleTranslator(
            source=self.source,
            target=self.target
        ).translate(self.text)


class TranslateModule(MQTTClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        super()._on_connect(client, userdata, flags, rc)
        client.subscribe("module/translate/request/+")

    def _on_message(self, client, userdata, msg):
        client_id = self.get_client_id(msg.topic)
        j = json.loads(msg.payload)
        try:
            r = TranslateRequest(**j)
        except KeyError:
            logging.error("Invalid request: {}".format(j))
            return
        translated = r.translate()
        if loglevel == logging.DEBUG:
            logging.debug(
                "Got request by client {}, source={}, target={}, text={}, translated={}".format(  # noqa: E501
                    client_id,
                    r.source,
                    r.target,
                    r.text,
                    translated,
                )
            )
        else:
            logging.info("Got request by client {}".format(client_id))
        self.client.publish(
            "module/translate/response/{}".format(client_id),
            json.dumps({"text": translated})
        )


if __name__ == "__main__":
    loglevel = logging.DEBUG if environ.get('DEBUG') else logging.INFO
    logging.basicConfig(level=loglevel)
    module = TranslateModule()
    module.run()
