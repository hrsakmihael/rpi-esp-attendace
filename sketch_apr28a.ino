#include <SPI.h>
#include <MFRC522.h>
#include <Servo.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#define SS_PIN 4
#define RST_PIN 16
#define SERVO_PIN 5

MFRC522 mfrc522(SS_PIN, RST_PIN);
Servo myServo;

bool isOpen = false;

const char* ssid = "WiFi_SSID";
const char* password = "WiFi_password";
const char* mqtt_server = "ip";

WiFiClient espClient;
PubSubClient client(espClient);

void callback(char* topic, byte* payload, unsigned int length) {

  String msg = "";

  for (int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }

  Serial.print("MQTT message: ");
  Serial.println(msg);

  if (msg == "OPEN") {
    isOpen = true;
    myServo.write(90);
    Serial.println("SERVO OPEN");
  }

  if (msg == "CLOSE") {
    isOpen = false;
    myServo.write(0);
    Serial.println("SERVO CLOSE");
  }
}

void reconnect() {

  while (!client.connected()) {

    Serial.print("MQTT connecting... ");

    if (client.connect("ESP_A1")) {

      Serial.println("OK");
      client.subscribe("door/control");
      Serial.println("Subscribed to door/control");

    } else {

      Serial.print("FAIL state=");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

void setup() {

  Serial.begin(9600);

  Serial.println("\nSTART");

  SPI.begin();
  mfrc522.PCD_Init();

  Serial.println("RFID ready");

  myServo.attach(SERVO_PIN);
  myServo.write(0);

  Serial.println("Servo ready");

  WiFi.begin(ssid, password);

  Serial.println("WiFi connecting...");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi OK");
  Serial.println(WiFi.localIP());

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {

  if (!client.connected()) reconnect();
  client.loop();

  if (!mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  if (!mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  String uid = "";

  for (byte i = 0; i < mfrc522.uid.size; i++) {

    if (mfrc522.uid.uidByte[i] < 0x10) uid += "0";

    uid += String(mfrc522.uid.uidByte[i], HEX);
  }

  uid.toUpperCase();

  Serial.print("UID: ");
  Serial.println(uid);

  String device = "A1";
  String message = device + ":" + uid;

  Serial.print("Sending: ");
  Serial.println(message);

  client.publish("rfid/tag", message.c_str());

  delay(1000);
}