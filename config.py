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

import logging, hashlib

MQTT_HOST = "homeassistant.local"
MQTT_PORT = 1883
MQTT_USER = None
MQTT_PASS = None
MQTT_KEEPALIVE = 60

HA_SENSOR_NAME = "Sound Detected"
HA_SENSOR_UUID = hashlib.md5(HA_SENSOR_NAME.encode('utf-8')).hexdigest()
HA_SENSOR_EXPIRE_AFTER = 10

TF_MODEL = "model/yamnet.tflite"
TF_NUM_THREADS = 2
TF_SCORE_THRESHOLD = 0.8
TF_MAX_RESULTS = 5
TF_IGNORED_CATEGORIES = ["Silence", "White noise", "Noise"]

LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s %(log_color)s%(message)s'
LOG_COLORS = {
    'WARNING':  'yellow',
    'ERROR':    'red',
    'CRITICAL': 'red',
	}
