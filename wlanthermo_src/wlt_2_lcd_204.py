#!/usr/bin/python
import sys
import ConfigParser
import os
import time
import math
import string
import logging
import RPi.GPIO as GPIO
import math
import pyinotify



GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

HIGH = True  # HIGH-Pegel
LOW  = False # LOW-Pegel
# Variablendefinition und GPIO Pin-Definition
#GPIO START
LCD_RS      = 7  # RS-Leitung Display
LCD_E       = 8  # Enable-Leitung Display
LCD_D4      = 22 # Data-4 Display
LCD_D5      = 10 # Data-5 Display
LCD_D6      = 9  # Data-6 Display
LCD_D7      = 11 # Data-7 Display
#GPIO END

LCD_WIDTH = 20  # Maximum Zeichen pro Zeile
LCD_CHR = True  # Charakter/DATA an das Display
LCD_CMD = False # Kommando an das Display

LCD_LINE_1 = 0x80 # LCD RAM Adresse fuer die erste Zeile
LCD_LINE_2 = 0xC0 # LCD RAM Adresse fuer die zweite Zeile
LCD_LINE_3 = 0x94 # LCD RAM Adresse fuer die dritte Zeile
LCD_LINE_4 = 0xD4 # LCD RAM Adresse fuer die vierte Zeile 

# Timing Konstanten
E_PULSE = 0.0005
E_DELAY = 0.0005

counter = 0
#String Length
sLen = 6

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
logger = logging.getLogger('WLANthermoDIS')
#Define Logging Level by changing >logger.setLevel(logging.LEVEL_YOU_WANT)< available: DEBUG, INFO, WARNING, ERROR, CRITICAL
log_level = Config.get('daemon_logging', 'level_DISPLAY')
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

logger.info('Display Started!')

#File System Watcher
wm = pyinotify.WatchManager()
mask = pyinotify.IN_CLOSE_WRITE

class PTmp(pyinotify.ProcessEvent):

    def process_IN_CLOSE_WRITE(self, event):
        logger.debug("IN_CLOSE_WRITE: %s " % os.path.join(event.path, event.name))
        show_values()


def lcd_init():  # Initialisierung Display und Definition Sonderzeichen Pfeil runter ASCII 0 und Pfeil hoch ASCII 1
  lcd_byte(0x33,LCD_CMD) # Noch im 8 Bit Modus also 30 30 
  lcd_byte(0x32,LCD_CMD) # 30 20 (30 = 8 Bit, 20 =4-Bit Modus)
  lcd_byte(0x28,LCD_CMD) # 4-Bit, 2-Zeilig, 5x8 Font
  lcd_byte(0x0C,LCD_CMD) # Display ein 
  
  lcd_byte(0x40,LCD_CMD) # Sonderzeichen 0 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 0 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 0 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 0 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 0 definieren
  lcd_byte(0x15,LCD_CHR) # Sonderzeichen 0 definieren
  lcd_byte(0x0E,LCD_CHR) # Sonderzeichen 0 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 0 definieren
  lcd_byte(0x00,LCD_CHR) # Sonderzeichen 0 definieren

  lcd_byte(0x48,LCD_CMD) # Sonderzeichen 1 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 1 definieren
  lcd_byte(0x0E,LCD_CHR) # Sonderzeichen 1 definieren
  lcd_byte(0x15,LCD_CHR) # Sonderzeichen 1 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 1 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 1 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 1 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 1 definieren
  lcd_byte(0x00,LCD_CHR) # Sonderzeichen 1 definieren


  lcd_byte(0x06,LCD_CMD) # Cursor nach rechts wandernd, kein Displayshift
  lcd_byte(0x01,LCD_CMD) # Display loeschen 
 
  

def lcd_string(message,style):
  # Sende String zum  Display
  # style=1 Linksbuendig
  # style=2 Zentriert
  # style=3 Rechtsbuendig

  if style==1:
    message = message.ljust(LCD_WIDTH," ")  
  elif style==2:
    message = message.center(LCD_WIDTH," ")
  elif style==3:
    message = message.rjust(LCD_WIDTH," ")

  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR)

def lcd_byte(bits, mode):
  # Sende Byte an die Daten-Leitungen des Displays
  # bits = data
  # mode = True  fuer Zeichen
  #        False fuer Kommando

  GPIO.output(LCD_RS, mode) # RS

  # High Nibble uebertragen
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x10==0x10:
    GPIO.output(LCD_D4, True)
  if bits&0x20==0x20:
    GPIO.output(LCD_D5, True)
  if bits&0x40==0x40:
    GPIO.output(LCD_D6, True)
  if bits&0x80==0x80:
    GPIO.output(LCD_D7, True)

  # Toggle 'Enable' pin
  time.sleep(E_DELAY)    
  GPIO.output(LCD_E, True)  
  time.sleep(E_PULSE)
  GPIO.output(LCD_E, False)  
  time.sleep(E_DELAY)      

  # Low Nibble uebertragen
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x01==0x01:
    GPIO.output(LCD_D4, True)
  if bits&0x02==0x02:
    GPIO.output(LCD_D5, True)
  if bits&0x04==0x04:
    GPIO.output(LCD_D6, True)
  if bits&0x08==0x08:
    GPIO.output(LCD_D7, True)

  # Toggle 'Enable' pin
  time.sleep(E_DELAY)    
  GPIO.output(LCD_E, True)  
  time.sleep(E_PULSE)
  GPIO.output(LCD_E, False)  
  time.sleep(E_DELAY)   

def str_len(v,l,s):
    global error_val, sLen
    r = ''
    if (v == '999.9'):
        v = error_val.replace('"','')
    if (len(v) > l):
        r = v[:sLen]
    else:
        for char in range(l - len(v)):
            r = r + s
        r = r + v
    return r
  
def show_values():
    global counter, sLen, curPath, curFile, pitFile
    alarm = ['']
    if counter == 100:
        lcd_init()
        counter=0
    try:
        if os.path.isfile(curPath + '/wd'):
            logger.debug("Daten vom WD zum Anzeigen vorhanden --> uebersteuert die Anzeige!")
            fwd = open(curPath + '/wd').read()
            wd = fwd.split(';')
            lcd_byte(LCD_LINE_1, LCD_CMD)
            lcd_string(wd[0],2)
            lcd_byte(LCD_LINE_2, LCD_CMD)
            lcd_string(wd[1],2)
            lcd_byte(LCD_LINE_3, LCD_CMD)
            lcd_string(wd[2],2)
            lcd_byte(LCD_LINE_4, LCD_CMD)
            lcd_string(wd[3],2)
        else:
            #LCD NEU
            
            # Alarm values ok, hi, lo, er
            alarm_values = [chr(1), chr(0), '', '']
            
            if os.path.isfile(curPath + '/' + curFile):
                logger.debug("Daten vom WLANThermo zum Anzeigen vorhanden")
                ft = open(curPath + '/' + curFile).read()
                temps = ft.split(';')
                for al in range (8):
                    if temps[al + 9] == 'ok':
                        alarm.append('')    
                    if temps[al + 9] == 'hi':
                        alarm.append(chr(1))    
                    if temps[al + 9] == 'lo':
                        alarm.append(chr(0))    
                    if temps[al + 9] == 'er':
                        alarm.append('')    
                    #print alarm[al]
                    
                lcd_byte(LCD_LINE_1, LCD_CMD)
                lcd_string('C1:' +  str_len(alarm[1] + temps[1],sLen,' ') + chr(0xdf) + 'C2:' + str_len(alarm[2] + temps[2],sLen,' ') + chr(0xdf),2)
                #print 'C1:' +  str_len(alarm[1] + temps[1],sLen,' ') + chr(0xdf) + 'C2:' + str_len(temps[10] + temps[2],sLen,' ') + chr(0xdf)
                lcd_byte(LCD_LINE_2, LCD_CMD)
                lcd_string('C3:' +  str_len(alarm[3] + temps[3],sLen,' ') + chr(0xdf) + 'C4:' + str_len(alarm[4] + temps[4],sLen,' ') + chr(0xdf),2)  
                lcd_byte(LCD_LINE_3, LCD_CMD)
                lcd_string('C5:' +  str_len(alarm[5] + temps[5],sLen,' ') + chr(0xdf) + 'C6:' + str_len(alarm[6] + temps[6],sLen,' ') + chr(0xdf),2) 
                
                Config.read('/var/www/conf/WLANThermo.conf')
                lcd_byte(LCD_LINE_4, LCD_CMD)
                if (Config.getboolean('ToDo', 'pit_on')):
                    if os.path.isfile(curPath + '/' + pitFile):
                        logger.debug("Pitmaster laeuft, zeige die Daten in der 3. Zeile an")
                        fp = open(curPath + '/' + pitFile).read()
                        pits = fp.split(';')
                        lcd_string('Pit: S:' + str("%.0f" % float(pits[1])) + ' I:' + str("%.0f" % float(pits[2])) + ' ' + pits[3],2)
                else:
                    lcd_string('C7:' +  str_len(alarm[7] + temps[7],sLen,' ') + chr(0xdf) + 'C8:' + str_len(alarm[8] + temps[8],sLen,' ') + chr(0xdf),2) 
        counter = counter + 1
    except IndexError: 
        return None


#Einlesen Displayeinstellungen
LCD = Config.getboolean('Display','lcd_present')

#Einlesen des gewuenschten Error value --> wenn ein unplausibler Messwert festgestellt wird wird statt dem Wert dieser String angezeigt
error_val = Config.get('Display','error_val')

#Einlesen der Software-Version
build = Config.get('Version','build')

#ueberpruefe ob der Dienst schon laeuft
PID = os.popen('ps aux|grep ' + str(sys.argv[0]) + '|grep -v grep|wc -l').read()
bashCommand = ''
if (int(PID) > 1):
    logger.debug('Display ausgabe ist schon gestartet, abbruch')
    sys.exit()

# Pfad fuer die uebergabedateien auslesen
curPath,curFile = os.path.split(Config.get('filepath','current_temp'))
pitPath,pitFile = os.path.split(Config.get('filepath','pitmaster'))

# Wenn das display Verzeichniss im Ram Drive nicht exisitiert erstelle es
if not os.path.exists(curPath):
    os.makedirs(curPath)

# wd file beim Starten des Display Daemons loeschen!
logger.debug("Check for WD File >" + curPath + "/wd<")
if os.path.isfile(curPath + '/wd'):
    os.remove(curPath + '/wd')

if LCD:
    GPIO.setup(LCD_E, GPIO.OUT)  # E
    GPIO.setup(LCD_RS, GPIO.OUT) # RS
    GPIO.setup(LCD_D4, GPIO.OUT) # DB4
    GPIO.setup(LCD_D5, GPIO.OUT) # DB5
    GPIO.setup(LCD_D6, GPIO.OUT) # DB6
    GPIO.setup(LCD_D7, GPIO.OUT) # DB7

    #Display initialisieren und Begruessungstext ausgeben
    lcd_init()
    lcd_byte(LCD_LINE_1, LCD_CMD)
    lcd_string("------8-Kanal-------",2) 
    lcd_byte(LCD_LINE_2, LCD_CMD)
    lcd_string("WLAN-Thermometer",2)
    lcd_byte(LCD_LINE_3, LCD_CMD)
    lcd_string("Armin Thinnes",2)
    lcd_byte(LCD_LINE_4, LCD_CMD)
    lcd_string(build,2)    

    time.sleep(3) # 3 second delay 

    lcd_byte(LCD_LINE_1, LCD_CMD)
    lcd_string("Grillsportverein",2)
    lcd_byte(LCD_LINE_2, LCD_CMD)
    lcd_string("",2)  
    lcd_byte(LCD_LINE_3, LCD_CMD)
    lcd_string("Die Referenz zum",1) 
    lcd_byte(LCD_LINE_4, LCD_CMD)
    lcd_string("Grillen und Messen!",1)   

    time.sleep(3) # 3 second delay

    # IP-Adressen ermitteln
    ETH1 = "0.0.0.0"
    ETH0 = "0.0.0.0"
    WLAN0 = "0.0.0.0"
    retvalue = os.popen("LANG=C ifconfig eth0 | grep 'inet addr:' | cut -d':' -f2| cut -d' ' -f1").readlines()
    
    if (len(retvalue)==0):
        ETH0="0.0.0.0"
    else:
        ETH=retvalue[0]
        ETH0=ETH[:-1]
    retvalue = os.popen("LANG=C ifconfig eth1 | grep 'inet addr:' | cut -d':' -f2| cut -d' ' -f1").readlines()
    
    if (len(retvalue)==0):
        ETH0="0.0.0.0"
    else:
        ETH=retvalue[0]
        ETH1=ETH[:-1]

    retvalue = os.popen("LANG=C ifconfig wlan0 | grep 'inet addr:' | cut -d':' -f2| cut -d' ' -f1").readlines()
    
    if (len(retvalue)==0):
        WLAN0="0.0.0.0"
    else:
        WLAN=retvalue[0]
        WLAN0=WLAN[:-1]
    WLAN0="WLAN0: " + WLAN0
    ETH0="ETH0: " + ETH0
    ETH1="ETH1: " + ETH1
    lcd_byte(LCD_LINE_1, LCD_CMD)
    lcd_string("IP-Adressen:",2)
    lcd_byte(LCD_LINE_2, LCD_CMD)
    lcd_string(WLAN0,2)  
    lcd_byte(LCD_LINE_3, LCD_CMD)
    lcd_string(ETH0,2) 
    lcd_byte(LCD_LINE_4, LCD_CMD)
    lcd_string(ETH1,2)   

    time.sleep(3) # 3 second delay


    

    
    notifier = pyinotify.Notifier(wm, PTmp())
    wdd = wm.add_watch(curPath, mask) #, rec=True)
    
    show_values()
    while True:
        try:
            notifier.process_events()
            if notifier.check_events():
                notifier.read_events()
        except KeyboardInterrupt:
            notifier.stop()
            break
logger.info('Display stopped!')
        
