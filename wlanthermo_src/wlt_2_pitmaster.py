#!/usr/bin/python
import sys
import ConfigParser
import os
import time
import math
import logging
import string
import RPi.GPIO as GPIO
import math
import subprocess

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

HIGH = True  # HIGH-Pegel
LOW  = False # LOW-Pegel
last_pit = 0

# Konfigurationsdatei einlesen
Config = ConfigParser.ConfigParser()
for i in range(0,5):
    while True:
        try:
            Config.read('/var/www/conf/WLANThermo.conf')
        except IndexError:
            time.sleep(1)
            continue
        break

LOGFILE = Config.get('daemon_logging', 'log_file')
HW = Config.get('Hardware', 'version')
logger = logging.getLogger('WLANthermoPIT')
#Define Logging Level by changing >logger.setLevel(logging.LEVEL_YOU_WANT)< available: DEBUG, INFO, WARNING, ERROR, CRITICAL
log_level = Config.get('daemon_logging', 'level_PIT')
if log_level == 'DEBUG':
    logger.setLevel(logging.DEBUG)
if log_level == 'INFO':
    logger.setLevel(logging.INFO)
if log_level == 'ERROR':
    logger.setLevel(logging.ERROR)
if log_level == 'WARNING':
    logger.setLevel(logging.WARNING)
if log_level == 'CRITICAL':
    logger.setLevel(logging.CRITICAL)
handler = logging.FileHandler(LOGFILE)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info('WLANThermoPID started')

# Variablendefinition und GPIO Pin-Definition
ADC_Channel = 0  # Analog/Digital-Channel
#GPIO START
PIT_IO   = 2 # Pitmaster Relais 
PID_PWM  = 4 # Pitmaster PWM
#GPIO END

pit_type = Config.get('Pitmaster','pit_type')
pit_pwm_min = Config.getfloat('Pitmaster','pit_pwm_min')
pit_curve = Config.get('Pitmaster','pit_curve')
    
#Soundoption einlesen
websound_on = Config.getboolean('Sound','websound_enabled')

# Funktionsdefinition
def setPWM(val):
    subprocess.call (["echo 0=" + str(val) + " > /dev/servoblaster"], shell=True)

def setIO(val):
    GPIO.output(PIT_IO, int(val))
    
def checkTemp(temp):
    r = 0
    try:
        r = float(temp)
    except ValueError:
        temp = temp[2:]
        r = float(temp)
    return r
    
def handle_service(sService, sWhat):
    bashCommand = 'sudo ' + sService + ' ' + sWhat #/etc/init.d/WLANThermo restart'
    logger.debug('handle_service: ' + bashCommand)
    retcode = subprocess.Popen(bashCommand.split())
    retcode.wait()
    if retcode < 0:
        logger.info('Termin by signal')
    else:
        logger.info('Child returned' + str(retcode))

logger.info('Pitmaster Start')

if pit_type in ['SERVO','FAN']:
    handle_service('service WLANThermoSERVO', 'stop')
    if pit_type == 'SERVO':
        servod = '/usr/sbin/servod_servo'
    else:
        
        if HW == 'v3':
            servod = '/usr/sbin/servod_fan'
        else:
            servod = '/usr/sbin/servod_servo'

    bashCommand = 'sudo cp ' + servod + ' /usr/sbin/servod' #den richtigen servod aktivieren
    logger.debug('Init servod: ' + bashCommand)
    retcode = subprocess.Popen(bashCommand.split())
    retcode.wait()
    if retcode < 0:
        logger.info('Termin by signal')
    else:
        logger.info('Child returned' + str(retcode))

    logger.info('initialize servod')
    handle_service('service WLANThermoSERVO', 'restart')

#Log Dateinamen aus der config lesen
current_temp = Config.get('filepath','current_temp')
pitmaster_log = Config.get('filepath','pitmaster')

#Pfad aufsplitten
pitPath,pitFile = os.path.split(pitmaster_log)

# Pin-Programmierung
GPIO.setup(PIT_IO, GPIO.OUT)

#Variablen
if pit_type == 'IO':
    pit_val = 0 
if pit_type in ['SERVO','FAN']:
    pit_val = pit_pwm_min

#print pit_curve
steps = pit_curve.split("|")

step = []
for val in steps:
    step.append(val)

step_temp = []
step_val = []
for val in step:
    v = val.split("!")
#    print v[0]
#    print v[1]
    step_temp.append(v[0]) 
    step_val.append(v[1])

chanel_name = [ "temp_0", "temp_1", "temp_2", "temp_3", "temp_4", "temp_5", "temp_6", "temp_7" ]
pit_new = 0
pit_val = 0
#Wenn das display Verzeichniss im Ram Drive nicht exisitiert erstelle es

if not os.path.exists(pitPath):
    os.makedirs(pitPath)

count = 0

while True: #Regelschleife
    msg = ""
    #Aktuellen ist wert auslesen
    for i in range(0,5):
        while True:
            try:
                tl = open(current_temp, 'r')
            except IndexError:
                time.sleep(1)
                continue
            break
    tline = tl.readline()
    if len(tline) > 5:
        logger.debug('check temps and control...')
        for i in range(0,5):
            while True:
                try:
                    Config.read('/var/www/conf/WLANThermo.conf')
                except IndexError:
                    time.sleep(1)
                    continue
                break
        pit_curve = Config.get('Pitmaster','pit_curve')
        pit_set = Config.getfloat('Pitmaster','pit_set')
        pit_ch = Config.getint('Pitmaster','pit_ch')
        pit_pause = Config.getfloat('Pitmaster','pit_pause')
        pit_pwm_min = Config.getfloat('Pitmaster','pit_pwm_min')
        pit_pwm_max = Config.getfloat('Pitmaster','pit_pwm_max')
        pit_man = Config.getint('Pitmaster','pit_man')
        if pit_man == 0:
            temps = tline.split(";")
            if temps[(pit_ch + 1)] == "Error":
                msg = msg + '|Kein Temperaturfuehler an Kanal ' + pit_ch + ' angeschlossen!'
            else:
                pit_now = float(checkTemp(temps[(pit_ch + 1)]))
                msg = msg + "|Ist: " + str(pit_now) + " Soll: " + str(pit_set)
                calc = 0
                s = 0
                for step in step_temp:
                    if calc == 0:
                        dif = pit_now - pit_set
                        msg = msg + "|Dif: " + str(dif)
                        if (dif <= float(step)):
                            calc = 1
                            msg = msg + "|Step: " + step
                            pit_new = step_val[s]
                            msg = msg + "|New: " + pit_new
                        if (pit_now >= pit_set):
                            calc = 1
                            pit_new = 0
                            msg = msg +  "|New-overshoot: " + str(pit_new)
                    s = s + 1
                if calc == 0:
                    msg = msg + "|Keine Regel zutreffend, Ausschalten!"
                    pit_new = 0
            if pit_type in ['SERVO','FAN']:
                #Berechne die Position mit den min und max Werten...
                msg = msg + "|Min: " + str(pit_pwm_min) + " Max: " + str(pit_pwm_max)
                x = (pit_pwm_max - pit_pwm_min) / 100 * float(pit_new) + pit_pwm_min
                if x != pit_val:
                    msg = msg + "|Drive Servo to: " + str(x) + " = " + str(pit_val) + "%"
                    pit_val = x
                    if last_pit == 0 and pit_new < 25: #Wenn vorher 0% war zuerst auf 25% und dann nach einer Sekunde auf den berechneten Wert stellen.
                        setPWM((pit_pwm_max - pit_pwm_min) / 100 * 25 + pit_pwm_min)
                        time.sleep(1.0)
                    setPWM(int(pit_val))
                else:
                    msg = msg + "|Servo pos: " + str(pit_new) + "% = " + str(pit_val)
                    last_pit = pit_val
            if pit_type == "IO":
                #Abweichung vom Sollwert berechnen. 
                #Hystherese 2 Grad: Solange mehr als ein Grad unter Sollwert, Relais einschalten, ab ein Grad ueber Sollwert ausschalten.
                delta = pit_set - pit_now
                if delta >= 1:
                    setIO(1)
                    relais = ' EIN'
                if delta <= -1:
                    setIO(0)                      
                    relais = ' AUS'
                logger.info('IO:' + relais)
            # Export das aktuellen Werte in eine Text datei
            lt = time.localtime()#  Uhrzeit des Messzyklus
            jahr, monat, tag, stunde, minute, sekunde = lt[0:6]
            Uhrzeit = string.zfill(stunde,2) + ':' + string.zfill(minute,2)+ ':' + string.zfill(sekunde,2)
            Uhrzeit_lang = string.zfill(tag,2) + '.' + string.zfill(monat,2) + '.' + string.zfill((jahr-2000),2) + ' ' + Uhrzeit
            
            Uhrzeit = string.zfill(stunde,2) + ':' + string.zfill(minute,2)+ ':' + string.zfill(sekunde,2)
            Uhrzeit_lang = string.zfill(tag,2) + '.' + string.zfill(monat,2) + '.' + string.zfill((jahr-2000),2) + ' ' + Uhrzeit
            for i in range(0,5):
                while True:
                    try:
                        fp = open(pitPath + '/' + pitFile, 'w')
                        # Schreibe mit Trennzeichen ; 
                        # Zeit;Soll;Ist;%;msg
                        fp.write(str(Uhrzeit_lang) + ';'+ str(pit_set) + ';' + str(pit_now) + ';' + str(pit_new) + '%;' + msg)
                        fp.close()
                    except IndexError:
                        time.sleep(1)
                        continue
                    break
            
            if (Config.getboolean('ToDo', 'pit_on') == False):
                if (count > 0):
                    if pit_type in ['SERVO','FAN']:
                        setPWM(int(pit_pwm_min))
                    if pit_type == "IO":
                        setIO(0)
                    logger.info('WLANThermoPID stopped')
                    break
                count = 1
        else:
            setPWM(pit_man)
    if len(msg) > 0:
        logger.debug(msg)
    time.sleep(pit_pause) 
