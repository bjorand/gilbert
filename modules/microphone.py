#!/usr/bin/env python3

import json
import os
import sys
import asyncio
import websockets
import logging
import sounddevice as sd
import argparse
import paho.mqtt.client as mqtt
import time

from translate import TranslateRequest
from states import SpeakingState


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    loop.call_soon_threadsafe(audio_queue.put_nowait, bytes(indata))

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    client.subscribe("status/speaking/+")

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe("$SYS/#")


def on_message(client, userdata, msg):
    global pause_recording
    print(msg.topic+" "+str(msg.payload))
    if msg.topic.startswith('status/speaking'):
        j = json.loads(msg.payload)
        try:
            r = SpeakingState(**j)
        except KeyError:
            logging.error("Invalid request: {}".format(j))
            return
        if r.speaking is True:
            pause_recording = True
        elif r.speaking is False:
            pause_recording = False
        else:
            print("Unknown payload on {} {}".format(msg.topic, msg.payload))


async def run_test():
    mqtt_address = os.environ.get('MQTT_ADDRESS') or "localhost"
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect_async(mqtt_address)
    client.loop_start()


    with sd.RawInputStream(samplerate=args.samplerate, blocksize = 4000, device=args.device, dtype='int16',
                           channels=1, callback=callback) as device:

        async with websockets.connect(args.uri) as websocket:
            await websocket.send('{ "config" : { "sample_rate" : %d } }' % (device.samplerate))
            while True:
                data = await audio_queue.get()
                if not pause_recording:
                    await websocket.send(data)
                    response = await websocket.recv()
                    # print(response)
                    j = json.loads(response)
                    if "text" in j and j["text"] != "":
                        client.publish(
                            "module/microphone/text/{}".format(os.getpid()),
                            j["text"]
                        )


            await websocket.send('{"eof" : 1}')
            print (await websocket.recv())

async def main():

    global args
    global loop
    global audio_queue
    global pause_recording

    pause_recording = False

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-l', '--list-devices', action='store_true',
                        help='show list of audio devices and exit')
    args, remaining = parser.parse_known_args()
    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)
    parser = argparse.ArgumentParser(description="ASR Server",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     parents=[parser])
    parser.add_argument('-u', '--uri', type=str, metavar='URL',
                        help='Server URL', default='ws://localhost:2700')
    parser.add_argument('-d', '--device', type=int_or_str,
                        help='input device (numeric ID or substring)')
    parser.add_argument('-r', '--samplerate', type=int, help='sampling rate', default=16000)
    args = parser.parse_args(remaining)
    loop = asyncio.get_running_loop()
    audio_queue = asyncio.Queue()

    logging.basicConfig(level=logging.INFO)
    await run_test()

if __name__ == '__main__':
    asyncio.run(main())
