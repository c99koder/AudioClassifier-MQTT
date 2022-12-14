# syntax=docker/dockerfile:1

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

FROM python:3.9-slim-buster
WORKDIR /app
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y install libusb-1.0 libportaudio2
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*
COPY . .
RUN pip3 install -r requirements.txt
ENTRYPOINT [ "python3", "listen.py"]
