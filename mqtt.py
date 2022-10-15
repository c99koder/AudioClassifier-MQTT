# Copyright 2022 Sam Steele
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json, sys
import paho.mqtt.client as mqtt
from config import *

LISTENING_ENABLED = False
audio_record = None

def mqtt_listening_enabled():
    return LISTENING_ENABLED

def mqtt_init(audio):
    global audio_record
    audio_record = audio
    logging.info("Connecting to MQTT host %s:%i", MQTT_HOST, MQTT_PORT)
    client = mqtt.Client()
    client.enable_logger(logging)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.message_callback_add("homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/set", on_switch_set)
    client.message_callback_add("homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/state", on_switch_state)
    client.message_callback_add("homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/config", on_switch_config)
    client.username_pw_set(username=MQTT_USER, password=MQTT_PASS)
    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=MQTT_KEEPALIVE)
    except OSError as err:
        logging.error("Failed to connect to MQTT server: %s", err)
        sys.exit(1)

    client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/available", 'online', retain=True)
    client.publish("homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/available", 'online', retain=True)

    return client

def mqtt_stop(client):
    client.publish("homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/available", 'offline', retain=True).wait_for_publish()
    client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/state", None, retain=True).wait_for_publish()
    client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/attributes", None, retain=True).wait_for_publish()
    client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/available", 'offline', retain=True).wait_for_publish()
    client.disconnect()

def mqtt_publish_state(client, category, score):
    client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/state", category, retain=True)
    client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/attributes", json.dumps({'score': score}), retain=True)

def on_connect(client, userdata, flags, rc):
    logging.info("Publishing MQTT sensor configuration")
    client.subscribe("homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/set")
    client.subscribe("homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/state")
    client.subscribe("homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/config")

    client.publish("homeassistant/sensor/" + HA_SENSOR_UUID + "/config", 
            json.dumps({'name': HA_SENSOR_NAME,
                'unique_id': HA_SENSOR_UUID,
                'icon': 'mdi:ear-hearing',
                'state_topic': "homeassistant/sensor/" + HA_SENSOR_UUID + "/state",
                'json_attributes_topic': "homeassistant/sensor/" + HA_SENSOR_UUID + "/attributes",
                'expire_after': HA_SENSOR_EXPIRE_AFTER,
                'availability_mode': 'latest',
                'availability_topic': "homeassistant/sensor/" + HA_SENSOR_UUID + "/available"
                }), retain=True)

    client.publish("homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/config", 
            json.dumps({'name': HA_SENSOR_NAME + " Enabled",
                'unique_id': HA_SENSOR_UUID + "_enabled",
                'icon': 'mdi:ear-hearing',
                'state_topic': "homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/state",
                'command_topic': "homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/set",
                'availability_mode': 'latest',
                'availability_topic': "homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/available"
                }), retain=True)

def on_disconnect(client, userdata, rc):
    client.unsubscribe("homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/set")
    client.unsubscribe("homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/state")
    client.unsubscribe("homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/config")
    if rc != 0:
        logging.error("Disconnected from MQTT server")

def on_switch_set(client, userdata, message):
    logging.debug("Received message %s on topic %s QoS %i", message.payload, message.topic, message.qos)
    client.publish("homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/state", message.payload, retain=True)

def on_switch_state(client, userdata, message):
    global LISTENING_ENABLED, audio_record
    logging.debug("Received message %s on topic %s QoS %i", message.payload, message.topic, message.qos)
    if message.payload == b'ON':
        if LISTENING_ENABLED != True:
            LISTENING_ENABLED = True
            audio_record.start_recording()
            logging.info("Listening started")
    else:
        if LISTENING_ENABLED != False:
            LISTENING_ENABLED = False
            audio_record.start_recording()
            logging.info("Listening stopped")

def on_switch_config(client, userdata, message):
    global LISTENING_ENABLED
    logging.debug("Received message %s on topic %s QoS %i", message.payload, message.topic, message.qos)
    if LISTENING_ENABLED:
        client.publish("homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/set", "ON")
    else:
        client.publish("homeassistant/switch/" + HA_SENSOR_UUID + "_enabled/set", "OFF")
