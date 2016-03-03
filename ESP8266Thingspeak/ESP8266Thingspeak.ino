/*************************************************/
/* Includes                                      */
/*************************************************/
#include <stdio.h>
#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include "Client.h"

#include <Wire.h>

// Include API-Headers
extern "C" {
#include "ets_sys.h"
#include "os_type.h"
#include "osapi.h"
#include "mem.h"
#include "user_interface.h"
#include "cont.h"
}

/*************************************************/
/* Debugging                                     */
/*************************************************/
const bool debugOutput = true;  // set to true for serial OUTPUT


#define SERIAL_SPEED 115200



// Create an WiFiClient object, here called "ethClient":
WiFiClient ethClient;


// ------------------------
void setup() {
   Serial.begin(115200);   

   if (debugOutput) Serial.println("ESP8266 starts...");
   pinMode(A0, INPUT);
   pinMode(2, OUTPUT);
   
}


void loop() {
   digitalWrite(2, LOW);
   double a = 0.0033354016;
   double b = 0.000225;
   double c = 0.00000251094;
   int Rn = 925;
   int sensorvalue = 0;
   int resistor = 320;
    
   sensorvalue = analogRead(A0);

   if (debugOutput){ Serial.print("pin: "); Serial.println(A0);}
   if (debugOutput){ Serial.print("initial read: "); Serial.println(sensorvalue);}
   delay(2);
   double Rt = resistor * ((1024.0/sensorvalue) - 1);
   float v, T;
   v = log( Rt/Rn);
   T = (1.0f/(a + b*v + c*v*v)) - 273;
   if (debugOutput){ Serial.print("T="); Serial.println(T);
   Serial.println();
   }
   digitalWrite(2, HIGH);
   delay(4000);
}

