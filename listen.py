#!/usr/bin/env python3

#  Copyright (C) 2022 Sam Steele
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import time, json, sys, signal, logging, colorlog
import paho.mqtt.client as mqtt
from tflite_support.task import audio
from tflite_support.task import core
from tflite_support.task import processor
from config import *

def listen():
    logging.info("Connecting to MQTT host %s:%i", MQTT_HOST, MQTT_PORT)
    client = mqtt.Client()
    client.username_pw_set(username=MQTT_USER, password=MQTT_PASS)
    try:
        client.connect(MQTT_HOST, MQTT_PORT)
    except OSError as err:
        logging.error("Failed to connect to MQTT server: %s", err)
        sys.exit(1)

    logging.debug("Publishing MQTT sensor configuration")
    client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/config", 
            json.dumps({'name': HA_SENSOR_NAME,
                'unique_id': HA_SENSOR_UUID,
                'icon': 'mdi:ear-hearing',
                'state_topic': "homeassistant/sensor/" + HA_SENSOR_UUID + "/state",
                'json_attributes_topic': "homeassistant/sensor/" + HA_SENSOR_UUID + "/attributes",
                'expire_after': 30,
                'availability_mode': 'latest',
                'availability_topic': "homeassistant/sensor/" + HA_SENSOR_UUID + "/available"
                }), retain=True).wait_for_publish()

    logging.info("Loading TensorFlow model")
    base_options = core.BaseOptions(file_name='model/yamnet.tflite', num_threads=TF_NUM_THREADS)
    classification_options = processor.ClassificationOptions(max_results=TF_MAX_RESULTS, score_threshold=TF_SCORE_THRESHOLD)
    options = audio.AudioClassifierOptions(base_options=base_options, classification_options=classification_options)
    classifier = audio.AudioClassifier.create_from_options(options)

    logging.info("Creating audio recorder")
    audio_record = classifier.create_audio_record()
    tensor_audio = classifier.create_input_tensor_audio()

    input_length_in_second = float(len(tensor_audio.buffer)) / tensor_audio.format.sample_rate
    logging.debug("Recording sample length: %f", input_length_in_second)

    audio_record.start_recording()
    logging.info("Listening started")
    client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/available", 'online', retain=True).wait_for_publish()

    try:
        while True:
            logging.debug("Recording")
            time.sleep(input_length_in_second)

            logging.debug("Analyzing audio")
            tensor_audio.load_from_audio_record(audio_record)
            result = classifier.classify(tensor_audio)

            logging.debug("Got %i categories", len(result.classifications[0].categories))
            if len(result.classifications[0].categories) > 0:
                for category in result.classifications[0].categories:
                    if category.category_name == "Silence":
                        logging.warning("No audio detected from microphone")
                        client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/state", None, retain=True).wait_for_publish()
                        client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/attributes", None, retain=True).wait_for_publish()
                    else:
                        logging.info("Prediction: %s (%f)", category.category_name, category.score)
                        client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/state", category.category_name, retain=True).wait_for_publish()
                        client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/attributes", json.dumps({'score': category.score}), retain=True).wait_for_publish()
            else:
                client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/state", None, retain=True).wait_for_publish()
                client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/attributes", None, retain=True).wait_for_publish()

    finally:
        logging.info("Shutting down")
        client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/state", None, retain=True).wait_for_publish()
        client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/attributes", None, retain=True).wait_for_publish()
        client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/available", 'offline', retain=True).wait_for_publish()
        client.disconnect()

if sys.stdout.isatty():
    colorlog.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, log_colors=LOG_COLORS, stream=sys.stdout)
else:
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT.replace(f'%(log_color)s', ''), stream=sys.stdout)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))

def sigterm_handler(_signo, _stack_frame):
    sys.exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)
sys.excepthook = handle_exception

listen()