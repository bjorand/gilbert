#!/usr/bin/env python3

from io import BytesIO
import json
from os import environ
import logging
import time

from gtts import gTTS
from pygame import mixer

from mqqt_client import MQTTClient
from states import SpeakingState


class TTSRequest():
    def __init__(self, *args, **kwargs):
        self.text = kwargs["text"]
        self.lang = kwargs["lang"]

    def json(self):
        return json.dumps({"text": self.text, "lang": self.lang})

    def speak(self, wait=True):
        mp3_fp = BytesIO()
        tts = gTTS(self.text, lang=self.lang)
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        mixer.music.load(mp3_fp, "mp3")
        mixer.music.play()
        if wait is True:
            while mixer.music.get_busy() is True:
                continue


class TTSModule(MQTTClient):
    def __init__(self, *args, **kwargs):
        self.status = kwargs.pop("status")
        super().__init__(*args, **kwargs)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        super()._on_connect(client, userdata, flags, rc)
        client.subscribe("module/tts/request/+")

    def _on_message(self, client, userdata, msg):
        client_id = self.get_client_id(msg.topic)
        j = json.loads(msg.payload)
        try:
            r = TTSRequest(**j)
        except KeyError:
            logging.error("Invalid request: {}".format(j))
            return
        self.status.publish(
            "status/speaking/{}".format(client_id),
            SpeakingState(speaking=True).json(),
        )
        r.speak()
        time.sleep(0.2)
        self.status.publish(
            "status/speaking/{}".format(client_id),
            SpeakingState(speaking=False).json(),
        )


if __name__ == "__main__":
    loglevel = logging.DEBUG if environ.get('DEBUG') else logging.INFO
    logging.basicConfig(level=loglevel)
    mixer.init()
    status = MQTTClient()
    status.start()
    tts = TTSModule(status=status)
    tts.run()
