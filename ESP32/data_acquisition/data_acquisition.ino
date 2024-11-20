#include <DHT.h>
#include <WiFi.h>

#include <Thing.CoAP.h>     // CoAP
#include <PubSubClient.h>   // MQTT



/* Sensori DHT */

const int DHT_INTERNO_PIN = 4;
const int DHT_ESTERNO_PIN = 18;

const long DEFAULT_SENSE_FREQUENCY = 5000;

// Label
const char* LABEL_DHT_INTERNO = "indoor_DHT_sensor";
const char* LABEL_DHT_ESTERNO = "outdoor_DHT_sensor";


// WiFi data
const char* WIFI_SSID = "OPPO A54 5G dp";
const char* WIFI_PASS = "abcd1234";


/* Topic */

// CoAP
const char* TOPIC_COAP_TEMPERATURA_INTERNA = "indoor_temperature";
const char* TOPIC_COAP_TEMPERATURA_ESTERNA = "outdoor_temperature";

// MQTT
const char* TOPIC_MQTT_READ_DHT_INTERNO = "read_indoor_dht";
const char* TOPIC_MQTT_SAMPLING_RATE_DHT_INTERNO = "sampling_rate_indoor_dht";
const char* TOPIC_MQTT_READ_DHT_ESTERNO = "read_outdoor_dht";
const char* TOPIC_MQTT_SAMPLING_RATE_DHT_ESTERNO = "sampling_rate_outdoor_dht";



DHT dht_int(DHT_INTERNO_PIN, DHT22);
DHT dht_est(DHT_ESTERNO_PIN, DHT22);

/* CoAP */
//Declare our CoAP server and the packet handler
Thing::CoAP::Server serverCoAP;
Thing::CoAP::ESP::UDPPacketProvider udpProvider;

/* MQTT */
PubSubClient clientMQTT;
WiFiClient clientWiFi;
const char* IP_MQTT_BROKER = "192.168.73.12";    // Indirizzo IP del mio pc con mosquitto


/* Variabili globali */

// Temperatura interna
float tempInterna = 0;                                    // Aggiornata periodicamente raccogliendo nuovi dati dal sensore DHT interno
bool reading_dhtInterno = false; //true;                  // Start/stop the sensor reading
long samplingRate_dhtInterno = DEFAULT_SENSE_FREQUENCY;   // Intervallo tra le letture del sensore
unsigned long previousMillis_dhtInterno = 0;              // Will store last time temperature was read      // Generally, you should use "unsigned long" for variables that hold time (the value will quickly become too large for an int to store)

// Temperatura esterna
float tempEsterna = 0;                                    // Aggiornata periodicamente raccogliendo nuovi dati dal sensore DHT esterno
bool reading_dhtEsterno = false; //true;                  // Start/stop the sensor reading
long samplingRate_dhtEsterno = DEFAULT_SENSE_FREQUENCY;   // Intervallo tra le letture del sensore
unsigned long previousMillis_dhtEsterno = 0;              // Will store last time temperature was read      // Generally, you should use "unsigned long" for variables that hold time (the value will quickly become too large for an int to store)



// WiFi
void connectWiFi() {
  
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  Serial.print("WiFi connection attempt");
  while (WiFi.status() != WL_CONNECTED) {
  
    Serial.print("...");
    delay(5000);
  }
  
  delay(500);
  Serial.print(" Connected (");
  Serial.print(WiFi.localIP());
  Serial.println(")");
  Serial.println();
}


/* MQTT */

// Connessione MQTT
void connectMQTT() {

  // Loop until we're reconnected
  while (!clientMQTT.connected()) {

    Serial.print("MQTT connection attempt...");

    // Attempt to connect
    if (clientMQTT.connect("MyESP32Client")) {

      Serial.println(" Connected");
      Serial.println();

      // ... and resubscribe
      clientMQTT.subscribe("#");      // '#': all remaining levels of hierarchy (only the final part)
    }
    else {

      Serial.print(" Failed (rc=");
      Serial.print(clientMQTT.state());
      Serial.println(")");

      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

// Viene invocata ogni volta che l'ESP riceve un messaggio tramite MQTT
void callbackMQTT(char* topic, byte* payload, unsigned int length) {

  Serial.print("MQTT message arrived [");
  Serial.print(topic);
  Serial.print(", ");
  
  for (int i = 0; i < length; i++) {

    Serial.print((char)payload[i]);
  }

  Serial.print("]");
  Serial.println();


  if (strcmp(topic, TOPIC_MQTT_READ_DHT_INTERNO) == 0) {    // strcmp() restituisce 0 quando le due stringhe sono uguali

    if ((char)payload[0] == '1') {
    
      reading_dhtInterno = true;
    }
    else {

      reading_dhtInterno = false;
    }


    if (reading_dhtInterno) {

      Serial.print("Start");
    }
    else {

      Serial.print("Stop");
    }

    Serial.print(" reading values from ");
    Serial.print(LABEL_DHT_INTERNO);
    if (reading_dhtInterno) {Serial.print("...");}
    Serial.println();
  }
  else if (strcmp(topic, TOPIC_MQTT_SAMPLING_RATE_DHT_INTERNO) == 0) {

    /* Converto il payload ricevuto in un long e lo assegno alla variabile */

    char payload_string[length + 1];
    int payload_int;

    memcpy(payload_string, payload, length);
    payload_string[length] = '\0';            // C strings have an extra byte on the end ('\0') which indicates end-of-string
    payload_int = atoi(payload_string);
    samplingRate_dhtInterno = long(payload_int);
    

    Serial.print("Changed sampling rate for ");
    Serial.println(LABEL_DHT_INTERNO);
  }
  else if (strcmp(topic, TOPIC_MQTT_READ_DHT_ESTERNO) == 0) {

    if ((char)payload[0] == '1') {
    
      reading_dhtEsterno = true;
    }
    else {

      reading_dhtEsterno = false;
    }


    if (reading_dhtEsterno) {

      Serial.print("Start");
    }
    else {

      Serial.print("Stop");
    }

    Serial.print(" reading values from ");
    Serial.print(LABEL_DHT_ESTERNO);
    if (reading_dhtEsterno) {Serial.print("...");}
    Serial.println();
  }
  else if (strcmp(topic, TOPIC_MQTT_SAMPLING_RATE_DHT_ESTERNO) == 0) {

    /* Converto il payload ricevuto in un long e lo assegno alla variabile */

    char payload_string[length + 1];
    int payload_int;

    memcpy(payload_string, payload, length);
    payload_string[length] = '\0';            // C strings have an extra byte on the end ('\0') which indicates end-of-string
    payload_int = atoi(payload_string);
    samplingRate_dhtEsterno = long(payload_int);


    Serial.print("Changed sampling rate for ");
    Serial.println(LABEL_DHT_ESTERNO);
  }
  else {

    Serial.println("ERRORE: Topic MQTT non valido.");
  }

  Serial.println();
}


void setup() {
  
  Serial.begin(115200);
  delay(100);
  
  // Initialize the DHT sensors
  dht_int.begin();
  dht_est.begin();
  delay(2000);
  
  connectWiFi();    // WiFi connection

  // MQTT connection
  clientMQTT.setClient(clientWiFi);
  clientMQTT.setServer(IP_MQTT_BROKER, 1883);
  clientMQTT.setCallback(callbackMQTT);
  clientMQTT.setBufferSize(400);
  connectMQTT();


  /* Inizializzo i valori delle temperature registrate */

  // Interna
  tempInterna = dht_int.readTemperature();
  Serial.print("READ new value from ");
  Serial.print(LABEL_DHT_INTERNO);
  Serial.println(":");
  Serial.println(tempInterna);
  Serial.println();

  // Esterna
  tempEsterna = dht_est.readTemperature();
  Serial.print("READ new value from ");
  Serial.print(LABEL_DHT_ESTERNO);
  Serial.println(":");
  Serial.println(tempEsterna);
  Serial.println();


  /* CoAP */
  
  // Configure our server to use our packet handler (It will use UDP)
  serverCoAP.SetPacketProvider(udpProvider);

  // Create a resource called "temperatura_interna"
  serverCoAP.CreateResource(TOPIC_COAP_TEMPERATURA_INTERNA, Thing::CoAP::ContentFormat::TextPlain, false)    // True means that this resource is observable
    .OnGet([](Thing::CoAP::Request & request) {                       // We are here configuring telling our server that, when we receive a "GET" request to this endpoint, run the following code

      Serial.print("CoAP request received [GET ");
      Serial.print(TOPIC_COAP_TEMPERATURA_INTERNA);
      Serial.println("]");

      // Legge l'ultimo valore della temperatura ottenuto dal DHT
      float value = tempInterna;
      String message = String(value);
      const char* payload = message.c_str();
      Serial.print("Sending value '");
      Serial.print(payload);
      Serial.println("'...");
      Serial.println();

      // Return the last state of dht
      return Thing::CoAP::Status::Content(payload);
    });

  // Create a resource called "temperatura_esterna"
  serverCoAP.CreateResource(TOPIC_COAP_TEMPERATURA_ESTERNA, Thing::CoAP::ContentFormat::TextPlain, false)    // True means that this resource is observable
    .OnGet([](Thing::CoAP::Request & request) {                       // We are here configuring telling our server that, when we receive a "GET" request to this endpoint, run the following code

      Serial.print("CoAP request received [GET ");
      Serial.print(TOPIC_COAP_TEMPERATURA_ESTERNA);
      Serial.println("]");

      // Legge l'ultimo valore della temperatura ottenuto dal DHT
      float value = tempEsterna;
      String message = String(value);
      const char* payload = message.c_str();
      Serial.print("Sending value '");
      Serial.print(payload);
      Serial.println("'...");
      Serial.println();

      // Return the last state of dht
      return Thing::CoAP::Status::Content(payload);
    });

  serverCoAP.Start();
}



void loop() {

  /* Leggo i valori delle temperature dai DHT */

  // Interna
  if (reading_dhtInterno) {

    unsigned long currentMillis = millis();

    /* Check to see if it's time to read new temperature
     *  (i.e. if the difference between the current time and last time you read the temperature
     *  is bigger than the interval at which you want to read new temperature).
     */
    if (currentMillis - previousMillis_dhtInterno >= samplingRate_dhtInterno) {

      // Save the last time you read the temperature
      previousMillis_dhtInterno = currentMillis;
  
      tempInterna = dht_int.readTemperature();
      Serial.print("READ new value from ");
      Serial.print(LABEL_DHT_INTERNO);
      Serial.println(":");
      Serial.println(tempInterna);
      Serial.println();
    }
  }

  // Esterna
  if (reading_dhtEsterno) {

    unsigned long currentMillis = millis();

    /* Check to see if it's time to read new temperature
     *  (i.e. if the difference between the current time and last time you read the temperature
     *  is bigger than the interval at which you want to read new temperature).
     */
    if (currentMillis - previousMillis_dhtEsterno >= samplingRate_dhtEsterno) {

      // Save the last time you read the temperature
      previousMillis_dhtEsterno = currentMillis;
  
      tempEsterna = dht_est.readTemperature();
      Serial.print("READ new value from ");
      Serial.print(LABEL_DHT_ESTERNO);
      Serial.println(":");
      Serial.println(tempEsterna);
      Serial.println();
    }
  }



  serverCoAP.Process();     // CoAP

  clientMQTT.loop();        // MQTT
}
