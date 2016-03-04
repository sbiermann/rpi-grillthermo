#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import os
import urllib

import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

HIGH = True  # HIGH-Pegel
LOW = False  # LOW-Pegel
BEEPER = 17  # Piepser
Channel_State = ['no', 'no', 'no', 'no', 'no', 'no', 'no', 'no']
Prev_State = ['no', 'no', 'no', 'no', 'no', 'no', 'no', 'no']
GPIO.setup(BEEPER, GPIO.OUT)
with open('config.json', 'r') as f:
    Config = json.load(f)


def playSound():
    GPIO.output(BEEPER, HIGH)
    time.sleep(0.2)
    GPIO.output(BEEPER, LOW)
    time.sleep(0.2)
    GPIO.output(BEEPER, HIGH)
    time.sleep(0.2)
    GPIO.output(BEEPER, LOW)
    time.sleep(0.2)
    GPIO.output(BEEPER, HIGH)
    time.sleep(0.2)
    GPIO.output(BEEPER, LOW)


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("bbq/temperature/+")
    GPIO.output(BEEPER, HIGH)
    time.sleep(1)
    GPIO.output(BEEPER, LOW)


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = str(msg.payload)
    channel_nr = int(topic[-1:])
    print("Received message for topic:" + topic + " with payload:" + payload)
    try:
        jsonPayload = json.loads(payload)
        min = int(Config['Sensoren']['ch' + str(channel_nr)]['min'])
        max = int(Config['Sensoren']['ch' + str(channel_nr)]['max'])
        temp = jsonPayload['value'];
        if (min != 0 and temp < min):
            Channel_State[channel_nr] = 'lo'
        elif (max != 0 and temp > max):
            Channel_State[channel_nr] = 'hi'
        else:
            Channel_State[channel_nr] = 'no'
            Prev_State[channel_nr] = 'no'
        if (Channel_State[channel_nr] != 'no'):
            if (bool(Config['Sensoren']['beeper'])):
                playSound()
            if(Prev_State[channel_nr] == 'no'):
                Prev_State[channel_nr] = Channel_State[channel_nr]
                human_chan = channel_nr + 1
                msgVal = 'Übertemperatur'
                if (Channel_State[channel_nr] == 'lo'):
                   msgVal = 'Untertemperatur'
                msg = 'Kanal S{0} hat {1}: {2}°C'.format(human_chan, msgVal, temp)
                    # if Email_alert: #wenn konfiguriert, email schicken
                    #     alarm_email(Email_server,Email_user,Email_password, Email_STARTTLS, Email_from, Email_to, Email_subject, Alarm_message)
                    #
                    # if WhatsApp_alert: #wenn konfiguriert, Alarm per WhatsApp schicken
                    #     cmd="/usr/sbin/sende_whatsapp.sh " + WhatsApp_number + " '" + Alarm_message + "'"
                    #     os.system(cmd)
                if bool(Config['Alarm']['push']['active']):
                        Alarm_message2 = urllib.quote(msg)
                        push_cmd = Config['Alarm']['push']['cmd'].replace('messagetext', Alarm_message2)
                        push_cmd = 'wget -q -O - ' + push_cmd
                        os.popen(push_cmd)
                jsonString = dict(value=msg,typ="warning")
                barray = bytearray(json.dumps(jsonString))
                mqttClient.publish("bbq/message", barray,0,True)
    except Exception, err:
        print Exception, err


mqttClient = mqtt.Client("alarmhandler")
mqttClient.on_connect = on_connect
mqttClient.on_message = on_message
mqttClient.connect("localhost", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
try:
    mqttClient.loop_forever()
except:
    mqttClient.disconnect()
