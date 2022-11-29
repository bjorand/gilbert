from os import environ
import logging

import paho.mqtt.client as mqtt


class MQTTClient():
    def __init__(self):
        self.mqtt_address = environ.get('MQTT_ADDRESS') or "localhost"
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def run(self):
        self.client.connect(self.mqtt_address)
        self.client.loop_forever()

    def publish(self, *args, **kwargs):
        self.client.publish(*args, **kwargs)

    def start(self):
        self.client.connect(self.mqtt_address)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        logging.info('Connected to mqtt server {}'.format(self.mqtt_address))

    def get_client_id(self, topic):
        return topic.split('/')[-1]

    def _on_message(self, client, userdata, msg):
        pass
