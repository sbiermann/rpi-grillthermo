#!/usr/bin/python
import os
import pyinotify
import subprocess
import ConfigParser
import thread
import time
import sys
import logging
import threading
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Timing Konstanten
E_PULSE = 0.00005
E_DELAY = 0.00005


HIGH = True  # HIGH-Pegel
LOW  = False # LOW-Pegel

wm = pyinotify.WatchManager()
#mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE
mask = pyinotify.IN_CLOSE_WRITE

cf = '/var/www/conf/WLANThermo.conf'

Config = ConfigParser.ConfigParser()
for i in range(0,5):
    while True:
        try:
            Config.read(cf)
        except IndexError:
            time.sleep(1)
            continue
        break

LOGFILE = Config.get('daemon_logging', 'log_file')
logger = logging.getLogger('WLANthermoWD')
#Define Logging Level by changing >logger.setLevel(logging.LEVEL_YOU_WANT)< available: DEBUG, INFO, WARNING, ERROR, CRITICAL
#logger.setLevel(logging.DEBUG)
log_level = Config.get('daemon_logging', 'level_WD')
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
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

logger.info('WLANThermoWD started')

class fs_wd(pyinotify.ProcessEvent):

    def process_IN_CLOSE_WRITE(self, event):
        if (os.path.join(event.path, event.name) == "/var/www/conf/WLANThermo.conf"):
            #print "IN_CLOSE_WRITE: %s " % os.path.join(event.path, event.name)
            read_config()		
			
def reboot_pi():
    logger.info('reboot PI')
    for i in range(0,5):
        while True:
            try:
                cfgfile = open(cf,'w')
                Config.set('ToDo', 'raspi_reboot', 'False')
                Config.write(cfgfile)
                cfgfile.close()
            except IndexError:
                time.sleep(1)
                continue
            break
    
    #Stoppe die Dienste
    handle_service('/etc/init.d/WLANThermo', 'stop')
    handle_service('/etc/init.d/WLANThermoPIT', 'stop')
    #Schreibe aufs LCD
    for i in range(0,5):
        while True:
            try:
                fw = open('/var/www/tmp/display/wd','w')
                fw.write('------ACHTUNG!-------;WLAN-Thermometer;- startet neu -;bis gleich...')
                fw.close()
            except IndexError:
                time.sleep(1)
                continue
            break
    
    bashCommand = 'sudo reboot'
    retcode = subprocess.Popen(bashCommand.split())
    retcode.wait()
    if retcode < 0:
        logger.info('Termin by signal')
    else:
        logger.info('Child returned' + str(retcode))

def halt_pi():
    logger.info('shutdown PI')
    for i in range(0,5):
        while True:
            try:
                cfgfile = open(cf,'w')
                Config.set('ToDo', 'raspi_shutdown', 'False')
                Config.write(cfgfile)
                cfgfile.close()
            except IndexError:
                time.sleep(1)
                continue
            break
    #Stoppe die Dienste
    handle_service('/etc/init.d/WLANThermo', 'stop')
    handle_service('/etc/init.d/WLANThermoPIT', 'stop')
    #Schreibe aufs LCD
    for i in range(0,5):
        while True:
            try:
                fw = open('/var/www/tmp/display/wd','w')
                fw.write('------ACHTUNG!-------;WLAN-Thermometer;- heruntergefahren -;und Tschuess...')
                fw.close()
            except IndexError:
                time.sleep(1)
                continue
            break
    bashCommand = 'sudo halt'
    retcode = subprocess.Popen(bashCommand.split())
    retcode.wait()
    if retcode < 0:
        logger.info('Termin by signal')
    else:
        logger.info('Child returned' + str(retcode))
 
def halt_v3_pi():
    logger.info('shutdown PI')
    for i in range(0,5):
        while True:
            try:
                cfgfile = open(cf,'w')
                Config.set('ToDo', 'raspi_v3_shutdown', 'False')
                Config.write(cfgfile)
                cfgfile.close()
            except IndexError:
                time.sleep(1)
                continue
            break
    #Stoppe die Dienste
    handle_service('/etc/init.d/WLANThermo', 'stop')
    handle_service('/etc/init.d/WLANThermoPIT', 'stop')
    #Schreibe aufs LCD
    for i in range(0,5):
        while True:
            try:
                fw = open('/var/www/tmp/display/wd','w')
                fw.write('------ACHTUNG!-------;WLAN-Thermometer;- heruntergefahren -;und Tschuess...')
                fw.close()
            except IndexError:
                time.sleep(1)
                continue
            break
	GPIO.setup(27, GPIO.OUT)
	GPIO.output(27,True)
	time.sleep(1)
	GPIO.output(27,False)
	time.sleep(1)
	GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    bashCommand = 'sudo halt'
    retcode = subprocess.Popen(bashCommand.split())
    retcode.wait()
    if retcode < 0:
        logger.info('Termin by signal')
    else:
        logger.info('Child returned' + str(retcode))
def read_config():
    global cf
    logger.debug('Read Config..')
    try:
        # Konfigurationsdatei einlesen
        #Config = ConfigParser.ConfigParser()
        for i in range(0,5):
            while True:
                try:
                    Config.read(cf)
                except IndexError:
                    time.sleep(1)
                    continue
                break
        if (Config.getboolean('ToDo', 'restart_thermo')):
            logger.info('Restart Thermo Process...')
            handle_service('service WLANThermo', 'restart')
            time.sleep(3)
            logger.info('Aendere config wieder auf False')
            for i in range(0,5):
                while True:
                    try:
                        cfgfile = open(cf,'w')
                        Config.set('ToDo', 'restart_thermo', 'False')
                        Config.write(cfgfile)
                        cfgfile.close()
                    except IndexError:
                        time.sleep(1)
                        continue
                    break

        if (Config.getboolean('ToDo', 'restart_pitmaster')):
            logger.info('Restart Pitmaster')
            handle_service('service WLANThermoPIT', 'restart')
            time.sleep(3)
            logger.info('Aendere config wieder auf False')
            for i in range(0,5):
                while True:
                    try:
                        cfgfile = open(cf,'w')
                        Config.set('ToDo', 'restart_pitmaster', 'False')
                        Config.write(cfgfile)
                        cfgfile.close()
                    except IndexError:
                        time.sleep(1)
                        continue
                    break

        if (Config.getboolean('ToDo', 'raspi_shutdown')):
            halt_pi()
			
        if (Config.getboolean('ToDo', 'raspi_v3_shutdown')):
            halt_v3_pi()
        
        if (Config.getboolean('ToDo', 'restart_display')):
            check_display()

        if (Config.getboolean('ToDo', 'raspi_reboot')):
            reboot_pi()
        if (Config.getboolean('ToDo', 'backup')):
            logger.info('create backup!')
            for i in range(0,5):
                while True:
                    try:
                        cfgfile = open(cf,'w')
                        Config.set('ToDo', 'backup', 'False')
                        Config.write(cfgfile)
                        cfgfile.close()
                    except IndexError:
                        time.sleep(1)
                        continue
                    break
            ret = os.popen("/usr/sbin/wlt_2_backup.sh").read()
            logger.debug(ret)
        if (Config.getboolean('ToDo', 'update_gui')):
            logger.info('create backup!')
            for i in range(0,5):
                while True:
                    try:
                        cfgfile = open(cf,'w')
                        Config.set('ToDo', 'update_gui', 'False')
                        Config.write(cfgfile)
                        cfgfile.close()
                    except IndexError:
                        time.sleep(1)
                        continue
                    break
            ret = os.popen("/usr/sbin/wlt_2_update_gui.sh").read()
            logger.debug(ret)

        if (Config.getboolean('ToDo', 'start_update')):
            logger.info('Update Software!')
            for i in range(0,5):
                while True:
                    try:
                        cfgfile = open(cf,'w')
                        Config.set('ToDo', 'start_update', 'False')
                        Config.write(cfgfile)
                        cfgfile.close()
                    except IndexError:
                        time.sleep(1)
                        continue
                    break
            ret = os.popen("/usr/sbin/wlt_2_update.sh").read()
            logger.debug(ret)

            
        if (Config.getboolean('ToDo', 'create_new_log')):
            logger.info('create new log')
            for i in range(0,5):
                while True:
                    try:
                        cfgfile = open(cf,'w')
                        Config.set('ToDo', 'create_new_log', 'False')
                        Config.set('Logging', 'write_new_log_on_restart', 'True')
                        Config.write(cfgfile)
                        cfgfile.close()
                    except IndexError:
                        time.sleep(1)
                        continue
                    break
            time.sleep(2)
            handle_service('service WLANThermo', 'restart')
            time.sleep(10)
            for i in range(0,5):
                while True:
                    try:
                        cfgfile = open(cf,'w')
                        Config.set('Logging', 'write_new_log_on_restart', 'False')
                        Config.write(cfgfile)
                        cfgfile.close()
                    except IndexError:
                        time.sleep(1)
                        continue
                    break
            logger.info('finished create new log')

        if (Config.getboolean('ToDo', 'pit_on')):
            check_pitmaster() 

    except:
        logger.info('Unexpected error: ' +str(sys.exc_info()[0]))
        raise

def handle_service(sService, sWhat):
    bashCommand = 'sudo ' + sService + ' ' + sWhat #/etc/init.d/WLANThermo restart'
    logger.debug('handle_service: ' + bashCommand)
    retcode = subprocess.Popen(bashCommand.split())
    retcode.wait()
    if retcode < 0:
        logger.info('Termin by signal')
    else:
        logger.info('Child returned' + str(retcode))

def check_file(f):
    if ( not os.path.isfile(f)):
        for i in range(0,5):
            while True:
                try:
                    fw1 = open(f,'w')
                    fw1.write('-')
                    fw1.close()
                except IndexError:
                    time.sleep(1)
                    continue
                break

def check_display():
    logger.debug('Check Display')
    logger.info('Aendere config wieder auf False')
    for i in range(0,5):
            while True:
                try:
                    cfgfile = open(cf,'w')
                    Config.set('ToDo', 'restart_display', 'False')
                    Config.write(cfgfile)
                    cfgfile.close()
                except IndexError:
                    time.sleep(1)
                    continue
                break
    if (Config.get('Display', 'lcd_present')):
        logger.debug('Display enabled, run it')
        handle_service('service WLANThermoDIS', 'restart')
    else:
        handle_service('service WLANThermoDIS', 'stop')
            

def check_pitmaster():
    logger.debug('Check Pitmaster')
    pitmasterPID = os.popen("ps aux|grep wlt_2_pitmaster.py|grep -v grep|awk '{print $2}'").read()
    bashCommandPit = ''
    if (Config.getboolean('ToDo', 'pit_on')):
        if (len(pitmasterPID) < 1):
            logger.info('start pitmaster')
            bashCommandPit = 'sudo service WLANThermoPIT start'
        else:
            logger.info('pitmaster already running')
    else:
        if (len(pitmasterPID) > 0):
            logger.info('stop pitmaster')
            #obsolet
        else:
            logger.info('pitmaster already stopped')
    if (len(bashCommandPit) > 0):
        retcodeO = subprocess.Popen(bashCommandPit.split())
        retcodeO.wait()
        if retcodeO < 0:
            logger.info('Termin by signal')
        else:
            logger.info('Child returned' + str(retcodeO))

notifier = pyinotify.Notifier(wm, fs_wd())

wdd = wm.add_watch('/var/www/conf', mask) #, rec=True)

#Start thread for shutdown pin
#input_thread = threading.Thread(target = wait_input)
#input_thread.start()

GPIO.add_event_detect(27, GPIO.RISING, callback=halt_pi, bouncetime=1000)


Config.read(cf)
check_display()
check_pitmaster()

while True:
    try:
        Config.read(cf)
        #time.sleep(5) 
        notifier.process_events()
        if notifier.check_events():
            notifier.read_events()
    except KeyboardInterrupt:
        notifier.stop()
        logging.shutdown()
        break
logging.shutdown()
logger.info('WLANThermoWD stopped')
