#include <DHT.h>
#include <WiFi.h>
//#include <PubSubClient.h>   // library for MQTT messaging
#include <Thing.CoAP.h>     // CoAP

#define DHT_interno_PIN 4
#define DHT_esterno_PIN 18
#define DEFAULT_SENSE_FREQUENCY 5000



char* SSID = "OPPO A54 5G dp";    //fill with WiFi data
char* PASS = "abcd1234";          //fill with WiFi data

/*const char* MQTT_USER = "iot2020";
const char* MQTT_PASSWD = "mqtt2020*";*/

//const char* TOPIC_0 = "sensor/temp";
//const char* TOPIC_1 = "sensor/hum";


DHT dht_int(DHT_interno_PIN, DHT22);
DHT dht_est(DHT_esterno_PIN, DHT22);

//PubSubClient clientMQTT; 
WiFiClient clientWiFi;
//const char* IP_MQTT_SERVER = "130.136.2.70";

/* CoAP */
//Declare our CoAP server and the packet handler
Thing::CoAP::Server server;
Thing::CoAP::ESP::UDPPacketProvider udpProvider;


// Variabili globali

float tempInt;      // Aggiornata periodicamente raccogliendo nuovi dati dal sensore DHT interno
//float tempEst;    // Aggiornata periodicamente raccogliendo nuovi dati dal sensore DHT esterno

//int samplingRate = DEFAULT_SENSE_FREQUENCY;   // Intervallo tra le letture dei sensori

//bool resultMQTT;



void connect() {
  
  WiFi.begin(SSID, PASS);

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

  // Inizializzo il valore
  /*tempInt = dht_int.readTemperature();
  Serial.println("Acquisito nuovo valore dal sensore DHT 'temperatura_interna'");
  Serial.println(tempInt);
  Serial.println("");*/


  /* CoAP */
  
  //Configure our server to use our packet handler (It will use UDP)
  server.SetPacketProvider(udpProvider);

  //Create an resource called "temperatura_interna"
  //server.CreateResource("temperatura_interna", Thing::CoAP::ContentFormat::TextPlain, true)   // True means that this resource is observable
  server.CreateResource("temperatura_interna", Thing::CoAP::ContentFormat::TextPlain, false)    //True means that this resource is observable
    .OnGet([](Thing::CoAP::Request & request) {                       // We are here configuring telling our server that, when we receive a "GET" request to this endpoint, run the the following code

      Serial.println("GET Request received for endpoint 'temperatura_interna'");

      //Read the state of our dht
      float value = dht_int.readTemperature();
      //float value = tempInt;
      String message = String(value);
      const char* payload = message.c_str();
      Serial.println(payload);
      Serial.println("");

      //Return the current state of our dht
      return Thing::CoAP::Status::Content(payload);
    });

    server.Start();
}



void loop() {

  /*tempInt = dht_int.readTemperature();
  Serial.println("Acquisito nuovo valore dal sensore DHT 'temperatura_interna'");
  Serial.println(tempInt);
  Serial.println("");*/

  server.Process();

  //delay(samplingRate);
}
