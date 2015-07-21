#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import required modules
import time
import math
import json

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

HIGH = True  # HIGH-Pegel
LOW  = False # LOW-Pegel
# Variablendefinition und GPIO Pin-Definition
ADC_Channel = 0  # Analog/Digital-Channel
#GPIO START
SCLK        = 11 # Serial-Clock
MOSI        = 10 # Master-Out-Slave-In
MISO        = 9  # Master-In-Slave-Out
CS          = 8  # Chip-Select

mqttc = mqtt.Client("sensorreader")
with open('sensor_config.json', 'r') as f:
    Config_Sensor = json.load(f)

def readAnalogData(adcChannel, SCLKPin, MOSIPin, MISOPin, CSPin):
    # Pegel vorbereiten
    GPIO.output(CSPin,   HIGH)
    GPIO.output(CSPin,   LOW)
    GPIO.output(SCLKPin, LOW)

    sendcmd = adcChannel
    sendcmd |= 0b00011000 # Entspricht 0x18 (1:Startbit, 1:Single/ended)

    # Senden der Bitkombination (Es finden nur 5 Bits Beruecksichtigung)
    for i in range(5):
        if (sendcmd & 0x10): # (Bit an Position 4 pruefen. Zaehlung beginnt bei 0)
            GPIO.output(MOSIPin, HIGH)
        else:
            GPIO.output(MOSIPin, LOW)
        # Negative Flanke des Clocksignals generieren
        GPIO.output(SCLKPin, HIGH)
        GPIO.output(SCLKPin, LOW)
        sendcmd <<= 1 # Bitfolge eine Position nach links schieben

    # Empfangen der Daten des ADC
    adcvalue = 0 # Ruecksetzen des gelesenen Wertes
    for i in range(13):
        GPIO.output(SCLKPin, HIGH)
        GPIO.output(SCLKPin, LOW)
        # print GPIO.input(MISOPin)
        adcvalue <<= 1 # 1 Postition nach links schieben
        if(GPIO.input(MISOPin)):
            adcvalue |= 0x01
    #time.sleep(0.1)
    return adcvalue

def temperatur_sensor (Rt, typ): #Ermittelt die Temperatur
    name = Config_Sensor[typ]['name']

    if (name != 'PT100') and (name != 'PT1000'):
        a = Config_Sensor[typ]['a']
        b = Config_Sensor[typ]['b']
        c = Config_Sensor[typ]['c']
        Rn = Config_Sensor[typ]['Rn']

        try:
            v = math.log(Rt/Rn)
            T = (1/(a + b*v + c*v*v)) - 273
        except: #bei unsinnigen Werten (z.B. ein- ausstecken des Sensors im Betrieb) Wert 999.9
            T = 999.9
    else:
        Rkomp = Config_Sensor[typ]['Rkomp']
        Rt = Rt - Rkomp
        if name == 'PT100':
            Rpt=0.1
        else:
            Rpt=1
        try:
            T = (-1)*math.sqrt( Rt/(Rpt*-0.0000005775) + (0.0039083**2)/(4*((-0.0000005775)**2)) - 1/(-0.0000005775)) - 0.0039083/(2*-0.0000005775)
        except:
            T = 999.9
    return T

def readAndInitProperties():
    global Sensornummer_typ, iterations, delay, messwiderstand
    with open('config.json', 'r') as f:
        Config = json.load(f)
    #read config values
    Sensornummer_typ = range(8)
    Sensornummer_typ[0] =  Config['Sensoren']['ch0']['typ']
    Sensornummer_typ[1] =  Config['Sensoren']['ch1']['typ']
    Sensornummer_typ[2] =  Config['Sensoren']['ch2']['typ']
    Sensornummer_typ[3] =  Config['Sensoren']['ch3']['typ']
    Sensornummer_typ[4] =  Config['Sensoren']['ch4']['typ']
    Sensornummer_typ[5] =  Config['Sensoren']['ch5']['typ']
    Sensornummer_typ[6] =  Config['Sensoren']['ch6']['typ']
    Sensornummer_typ[7] =  Config['Sensoren']['ch7']['typ']
    iterations = Config['Messen']['iterations']
    delay = Config['Messen']['delay']
    messwiderstand = range(8)
    messwiderstand[0] = Config['Messen']['messwiderstand0']
    messwiderstand[1] = Config['Messen']['messwiderstand1']
    messwiderstand[2] = Config['Messen']['messwiderstand2']
    messwiderstand[3] = Config['Messen']['messwiderstand3']
    messwiderstand[4] = Config['Messen']['messwiderstand4']
    messwiderstand[5] = Config['Messen']['messwiderstand5']
    messwiderstand[6] = Config['Messen']['messwiderstand6']
    messwiderstand[7] = Config['Messen']['messwiderstand7']


def main():
    while True:
        readAndInitProperties()
        for kanal in range (8):
            sensortyp = Sensornummer_typ[kanal]
            sensorname = Config_Sensor[sensortyp]['name']

            Temp = 0
            gute = 0
            tempoverall = 0;
            for i in range (iterations): #Anzahl iterations Werte messen und Durchschnitt bilden
                ADC_Channel = kanal
                Wert = 4096 - readAnalogData(ADC_Channel, SCLK, MOSI, MISO, CS)
                if (Wert > 60) and (sensorname != 'KTYPE'): #sinnvoller Wertebereich
                    Rtheta = messwiderstand[kanal]*((4096.0/Wert) - 1)
                    Tempvar = temperatur_sensor(Rtheta,sensortyp)
                    if Tempvar <> 999.9: #normale Messung, keine Sensorprobleme
                        gute = gute + 1
                        Temp = Temp + Tempvar
                        tempoverall = round(Temp/gute,2)
                    else:
                        if (gute==0):
                            tempoverall  = 999.9 # Problem waehrend des Messzyklus aufgetreten, Errorwert setzen
                else:
                    if sensorname=='KTYPE':
                        tempoverall = Wert*330/4096
                    else:
                        tempoverall = 999.9 # kein sinnvoller Messwert, Errorwert setzen
            jsonString = dict(value=tempoverall,typ=sensortyp,name=sensorname)
            payload = bytearray(json.dumps(jsonString))
            mqttc.publish("bbq/temperature/s{0}".format(kanal), payload)
        time.sleep(delay)
    return 0


if __name__ == '__main__':
    mqttc.connect("localhost", 1883)
    #Init SPI
    GPIO.setup(SCLK, GPIO.OUT)
    GPIO.setup(MOSI, GPIO.OUT)
    GPIO.setup(MISO, GPIO.IN)
    GPIO.setup(CS,   GPIO.OUT)

    # call main function
    try:
        main()
    finally:
        GPIO.cleanup()
        mqttc.disconnect()