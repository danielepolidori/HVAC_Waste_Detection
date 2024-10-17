#include <DHT.h>
#include <WiFi.h>
//#include <PubSubClient.h>   // library for MQTT messaging
#include <Thing.CoAP.h>     // CoAP



const int DHT_INTERNO_PIN = 4;
const int DHT_ESTERNO_PIN = 18;
const int DEFAULT_SENSE_FREQUENCY = 5000;

// WiFi data
const char* WIFI_SSID = "OPPO A54 5G dp";
const char* WIFI_PASS = "abcd1234";

/*const char* MQTT_USER = "iot2020";
const char* MQTT_PASSWD = "mqtt2020*";*/

const char* TOPIC_TEMPERATURA_INTERNA = "temperatura_interna";
const char* TOPIC_TEMPERATURA_ESTERNA = "temperatura_esterna";


DHT dht_int(DHT_INTERNO_PIN, DHT22);
DHT dht_est(DHT_ESTERNO_PIN, DHT22);

//PubSubClient clientMQTT; 
WiFiClient clientWiFi;
//const char* IP_MQTT_SERVER = "130.136.2.70";

/* CoAP */
//Declare our CoAP server and the packet handler
Thing::CoAP::Server server;
Thing::CoAP::ESP::UDPPacketProvider udpProvider;


// Variabili globali

float tempInterna;      // Aggiornata periodicamente raccogliendo nuovi dati dal sensore DHT interno
float tempEsterna;      // Aggiornata periodicamente raccogliendo nuovi dati dal sensore DHT esterno

int samplingRate = DEFAULT_SENSE_FREQUENCY;   // Intervallo tra le letture dei sensori

//bool resultMQTT;



// WiFi
void connect() {
  
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  while (WiFi.status() != WL_CONNECTED) {
  
    Serial.println("Connection attempt");
    delay(500);
  }
  
  delay(5000);
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println(WiFi.localIP());
  Serial.println("");
}


void setup() {
  
  Serial.begin(115200);
  delay(100);
  
  // Initialize the DHT sensors
  dht_int.begin();
  dht_est.begin();
  delay(2000);
  
  connect();    // WiFi
  /*
  clientMQTT.setClient(clientWiFi);
  clientMQTT.setServer(IP_MQTT_SERVER, 1883);
  clientMQTT.setBufferSize(400);
  
  resultMQTT = false;
*/

  // Inizializzo i valori delle temperature registrate

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
  server.SetPacketProvider(udpProvider);

  // Create a resource called "temperatura_interna"
  server.CreateResource(TOPIC_TEMPERATURA_INTERNA, Thing::CoAP::ContentFormat::TextPlain, false)    // True means that this resource is observable
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
  server.CreateResource(TOPIC_TEMPERATURA_ESTERNA, Thing::CoAP::ContentFormat::TextPlain, false)    // True means that this resource is observable
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

  server.Start();
}



void loop() {

  delay(samplingRate);


  // Leggo i valori delle temperature dai DHT

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


  server.Process();     // CoAP
}
