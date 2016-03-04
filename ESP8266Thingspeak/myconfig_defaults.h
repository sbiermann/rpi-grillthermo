/*************************************************/
/* Debugging                                     */
/*************************************************/
const bool debugOutput = true;  // set to true for serial OUTPUT

/*************************************************/
/* Settings for WLAN                             */
/*************************************************/
const char* ssid = "ssid";
const char* password = "mysecret";

/*************************************************/
/* Static IP                                     */
/*************************************************/
IPAddress ip(192,168,0,2);
IPAddress gateway(192,168,0,1);
IPAddress subnet(255,255,255,0);

/*************************************************/
/* Thingspeak data                               */
/*************************************************/
const char* thingspeak_host = "api.thingspeak.com";
const char* thingspeak_key = "thingspeakkey";

/*************************************************/
/* Maverick ET-732                               */
/*************************************************/
double a = 0.0033354016;
double b = 0.000225;
double c = 0.00000251094;
int Rn = 925;

/*************************************************/
/* Sum of voltage divider resistors in kOhm      */
/*************************************************/   
int resistor = 320;
