#!/usr/bin/env python
# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
import struct

mqttc = mqtt.Client("python_pub")
mqttc.connect("localhost", 1883)
payload = bytearray("{'S1':'42.2','S2':'234.34'}", "utf-8") 
mqttc.publish("bbq/temperature", payload)
mqttc.loop(2) #timeout = 2s
mqttc.disconnect()

