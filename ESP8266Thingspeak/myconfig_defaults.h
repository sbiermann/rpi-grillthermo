/*************************************************/
/* Debugging                                     */
/*************************************************/
const bool debugOutput = true;  // set to true for serial OUTPUT

/*************************************************/
/* Update settings                               */
/*************************************************/ 
const char* firmware_version = "wlanthermo_0.X.Y";
const char* update_server = "10.0.0.X";
const char* update_uri = "/esp/update/arduino.php";

/*************************************************/
/* Thingspeak data                               */
/*************************************************/
const char* thingspeak_host = "api.thingspeak.com";
const char* thingspeak_key = "thingspeakkey";
const char* thingspeak_field = "field1";

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
