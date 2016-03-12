/*************************************************/
/* Includes                                      */
/*************************************************/
#include <stdio.h>
#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include "Client.h"
#include "myconfig.h"
#include <Wire.h>

#include <DNSServer.h>
#include <ESP8266WebServer.h>
#include <WiFiManager.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266httpUpdate.h>

// Include API-Headers
extern "C" {
#include "ets_sys.h"
#include "os_type.h"
#include "osapi.h"
#include "mem.h"
#include "user_interface.h"
#include "cont.h"
}


#define SERIAL_SPEED 115200

// Create an WiFiClient object, here called "ethClient":
WiFiClient ethClient;
WiFiManager wifiManager;

// ------------------------
void setup() {
   Serial.begin(SERIAL_SPEED);   

   if (debugOutput) Serial.println("ESP8266 starts...");
   pinMode(A0, INPUT);
   pinMode(2, OUTPUT);

   wifiManager.autoConnect();
   delay(100);
   do_update();
}

void loop() {
   digitalWrite(2, LOW);
   int sensorvalue = 0;
   float sumTemp = 0;
   float minTemp = 999.99f;
   float maxTemp = 0.0;
   int numberReadings = 1000;
   boolean badReading = false;
   if (debugOutput) { Serial.println("start reading..."); }
   for(int i = 0; i < numberReadings; i++)
   { 
     sensorvalue = analogRead(A0);
     if(sensorvalue <= 5 || sensorvalue > 1024)
     {
       badReading = true;
       break;
     }
     delay(2);
     double Rt = resistor * ((1024.0/sensorvalue) - 1);
     float v, T;
     v = log( Rt/Rn);
     T = (1.0f/(a + b*v + c*v*v)) - 273;
     if(T < minTemp)
      minTemp = T;
     if(maxTemp < T)
      maxTemp = T;
     sumTemp += T;
   }
   digitalWrite(2, HIGH);
   float avTemp = 999.99f;
   if(!badReading)
      avTemp = sumTemp/numberReadings;
   if (debugOutput) { 
    Serial.println("finished reading...");
    Serial.print("minTemp: "); Serial.print(minTemp); Serial.print(" maxTemp: "); Serial.print(maxTemp); Serial.print(" avTemp: "); Serial.println(avTemp);
   }
   yield();
  
   if (!ethClient.connect(thingspeak_host, 80)) {
    Serial.println("connection failed");
    return;
   }

   String url = "/update?key=" + String(thingspeak_key) + "&" + String(thingspeak_field) + "="+ String(avTemp);
   if (debugOutput) {
    Serial.print("Requesting URL: ");
    Serial.println(url);
   }
   ethClient.print(String("GET ") + url + " HTTP/1.1\r\n" +
               "Host: " + thingspeak_host + "\r\n" + 
               "Connection: close\r\n\r\n");
   delay(100);

   if (debugOutput) {
    Serial.println("Respond:");
    while(ethClient.available()){
      String line = ethClient.readStringUntil('\r');
      Serial.print(line);
    }
    Serial.println();
   }
   ethClient.stop();
   if (debugOutput) { Serial.println("waiting 30s..."); }
   delay(30000);
}

void do_update(){
  Serial.println("do update");
  t_httpUpdate_return ret = ESPhttpUpdate.update(update_server, 80, update_uri, firmware_version);
  switch(ret) {
    case HTTP_UPDATE_FAILED:
        Serial.println("[update] Update failed.");
        break;
    case HTTP_UPDATE_NO_UPDATES:
        Serial.println("[update] no Update needed");
        break;
    case HTTP_UPDATE_OK:
        Serial.println("[update] Update ok."); // may not called we reboot the ESP
        break;
  }
}

