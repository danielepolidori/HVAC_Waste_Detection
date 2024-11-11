#include <DHT.h>
#include <WiFi.h>

#include <Thing.CoAP.h>     // CoAP
#include <PubSubClient.h>   // MQTT



const int DHT_INTERNO_PIN = 4;
const int DHT_ESTERNO_PIN = 18;
const long DEFAULT_SENSE_FREQUENCY = 5000;

// WiFi data
const char* WIFI_SSID = "OPPO A54 5G dp";
const char* WIFI_PASS = "abcd1234";

const char* TOPIC_TEMPERATURA_INTERNA = "temperatura_interna";
const char* TOPIC_TEMPERATURA_ESTERNA = "temperatura_esterna";


DHT dht_int(DHT_INTERNO_PIN, DHT22);
DHT dht_est(DHT_ESTERNO_PIN, DHT22);

/* CoAP */
//Declare our CoAP server and the packet handler
Thing::CoAP::Server serverCoAP;
Thing::CoAP::ESP::UDPPacketProvider udpProvider;

/* MQTT */
PubSubClient clientMQTT;
WiFiClient clientWiFi;
const char* IP_MQTT_BROKER = "192.168.195.12";    // Indirizzo IP del mio pc con mosquitto


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

  while (WiFi.status() != WL_CONNECTED) {
  
    Serial.println("WiFi connection attempt...");
    delay(500);
  }
  
  delay(5000);
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println(WiFi.localIP());
  Serial.println("");
}


/* MQTT */

// Viene invocata ogni volta che l'ESP riceve un messaggio tramite MQTT
void callbackMQTT(char* topic, byte* payload, unsigned int length) {

  Serial.print("MQTT message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  
  for (int i = 0; i < length; i++) {

    Serial.print((char)payload[i]);
  }

  Serial.println();
  Serial.println("");


  //interval = 15000;  //tmp
  // ...
}

// Connessione MQTT
void reconnectMQTT() {

  // Loop until we're reconnected
  while (!clientMQTT.connected()) {

    Serial.print("Attempting MQTT connection...");

    // Attempt to connect
    if (clientMQTT.connect("MyESP32Client")) {

      Serial.println(" Connected");
      Serial.println("");

      // ... and resubscribe
      clientMQTT.subscribe("sampling_rate");
    }
    else {

      Serial.print("failed, rc=");
      Serial.print(clientMQTT.state());
      Serial.println(" try again in 5 seconds");

      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}


void setup() {
  
  Serial.begin(115200);
  delay(100);
  
  // Initialize the DHT sensors
  dht_int.begin();
  dht_est.begin();
  delay(2000);
  
  connectWiFi();    // WiFi


  // MQTT
  clientMQTT.setClient(clientWiFi);
  clientMQTT.setServer(IP_MQTT_BROKER, 1883);
  clientMQTT.setCallback(callbackMQTT);
  clientMQTT.setBufferSize(400);


  /* Inizializzo i valori delle temperature registrate */

  // Interna
  tempInterna = dht_int.readTemperature();
  Serial.print("READ new value from DHT sensor '");
  Serial.print(TOPIC_TEMPERATURA_INTERNA);
  Serial.println("'");
  Serial.println(tempInterna);
  Serial.println("");

  // Esterna
  tempEsterna = dht_est.readTemperature();
  Serial.print("READ new value from DHT sensor '");
  Serial.print(TOPIC_TEMPERATURA_ESTERNA);
  Serial.println("'");
  Serial.println(tempEsterna);
  Serial.println("");


  /* CoAP */
  
  // Configure our server to use our packet handler (It will use UDP)
  serverCoAP.SetPacketProvider(udpProvider);

  // Create a resource called "temperatura_interna"
  serverCoAP.CreateResource(TOPIC_TEMPERATURA_INTERNA, Thing::CoAP::ContentFormat::TextPlain, false)    // True means that this resource is observable
    .OnGet([](Thing::CoAP::Request & request) {                       // We are here configuring telling our server that, when we receive a "GET" request to this endpoint, run the following code

      Serial.print("GET request received for endpoint '");
      Serial.print(TOPIC_TEMPERATURA_INTERNA);
      Serial.println("'");

      // Legge l'ultimo valore della temperatura ottenuto dal DHT
      float value = tempInterna;
      String message = String(value);
      const char* payload = message.c_str();
      Serial.println(payload);
      Serial.println("");

      // Return the last state of dht
      return Thing::CoAP::Status::Content(payload);
    });

  // Create a resource called "temperatura_esterna"
  serverCoAP.CreateResource(TOPIC_TEMPERATURA_ESTERNA, Thing::CoAP::ContentFormat::TextPlain, false)    // True means that this resource is observable
    .OnGet([](Thing::CoAP::Request & request) {                       // We are here configuring telling our server that, when we receive a "GET" request to this endpoint, run the following code

      Serial.print("GET request received for endpoint '");
      Serial.print(TOPIC_TEMPERATURA_ESTERNA);
      Serial.println("'");

      // Legge l'ultimo valore della temperatura ottenuto dal DHT
      float value = tempEsterna;
      String message = String(value);
      const char* payload = message.c_str();
      Serial.println(payload);
      Serial.println("");

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
      Serial.print("READ new value from DHT sensor '");
      Serial.print(TOPIC_TEMPERATURA_INTERNA);
      Serial.println("'");
      Serial.println(tempInterna);
      Serial.println("");
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
      Serial.print("READ new value from DHT sensor '");
      Serial.print(TOPIC_TEMPERATURA_ESTERNA);
      Serial.println("'");
      Serial.println(tempEsterna);
      Serial.println("");
    }
  }



  serverCoAP.Process();     // CoAP


  /* MQTT */

  if (!clientMQTT.connected()) {

    reconnectMQTT();
  }

  clientMQTT.loop();
}
