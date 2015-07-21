#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("bbq/temperature/+")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = str(msg.payload)
    print("Received message for topic:" + topic + " with payload:" + payload)
    try:
        jsonPayload = json.loads(payload)
        json_body = [
            {
                "measurement": "bbq_temperature",
                "tags": {
                    "sensorname": jsonPayload['name'],
                    "channel": topic[-2:]
                },
                "fields": {
                    "value": jsonPayload['value']
                }
            }
        ]
        dbclient.write_points(json_body)
    except Exception, err:
        print Exception, err

mqttClient = mqtt.Client("influxdbwriter")
mqttClient.on_connect = on_connect
mqttClient.on_message = on_message
mqttClient.connect("localhost", 1883, 60)

user = 'root'
password = 'root'
dbname = 'bbq'
host = 'localhost'
port = 8086
dbclient = InfluxDBClient(host, port, user, password, dbname)


# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
try:
    mqttClient.loop_forever()
except:
    mqttClient.disconnect()
