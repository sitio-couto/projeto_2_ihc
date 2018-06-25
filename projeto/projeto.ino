//projeto.ino

#include <ESP8266WiFi.h>
#include <MQTTClient.h>

const char client_id[] = "microcontrolador";     //arbitrary identification
const char client_key[] = "a0160aee";            //token KEY from shiftr.io
const char client_secret[] = "eb90656ac81576b0"; //token SECRET from shiftr.io

const char ssid[] = "11111"; //name of the used Wi-Fi network
const char pass[] = "21111"; //password of the Wi-Fi network

WiFiClient net;
MQTTClient client;
const int QoS = 1;

// sets up the pin assignments
const int obs_pin    = D9; // watched by the raspberry pi to know if there's an observer
const int red_pin    = D5;
const int green_pin  = D6;
const int blue_pin   = D7;
const int buzzer_pin = D3;
const int trig_pin   = D1;
const int echo_pin   = D0;
const int max_dist   = 150;

// stores the last MAX_STORED_DISTANCES distances
const int MAX_STORED_DISTANCES = 10;
int distances[MAX_STORED_DISTANCES];
int stored_distances = 0;

// starts with a red LED
int red   = 255;
int green = 0;
int blue  = 0;

int distance;
boolean has_observers = false;
boolean is_buzzing = false;
const int MAX_LOOPS_BUZZING = 1000;
int loops_buzzing = 0;

void setup() {
    Serial.begin(115200);

    pinMode(obs_pin,    OUTPUT);
    pinMode(red_pin,    OUTPUT);
    pinMode(green_pin,  OUTPUT);
    pinMode(blue_pin,   OUTPUT);
    pinMode(buzzer_pin, OUTPUT);
    pinMode(trig_pin,   OUTPUT);
    pinMode(echo_pin,   INPUT);

    /*
    connectWIFI();
    client.begin("broker.shiftr.io", net);
    client.onMessage(messageReceived);
    connectMQTT();

    client.subscribe("/red");
    client.subscribe("/green");
    client.subscribe("/blue");
    */
}

void loop() {
    // if (is_buzzing) {
    //     if (++loops_buzzing >= MAX_LOOPS_BUZZING) {
    //         digitalWrite(buzzer_pin, LOW);
    //         is_buzzing = false;
    //         loops_buzzing = 0;
    //     }
    // }

    delayMicroseconds(30000);

    // clears the trig_pin
    digitalWrite(trig_pin, LOW);
    delayMicroseconds(2);
    // sets the trig_pin on HIGH state for 10 micro seconds
    digitalWrite(trig_pin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trig_pin, LOW);
    // reads the echo_pin and returns the sound wave travel time in microseconds
    int distance = pulseIn(echo_pin, HIGH)*0.034/2;

    // Serial.print("Distance: ");
    // Serial.println(distance);

    if (stored_distances < MAX_STORED_DISTANCES) {
        distances[stored_distances++] = distance;
    } else {
        for (int i = 0; i < stored_distances - 1; ++i) distances[i] = distances[i+1];
        distances[stored_distances - 1] = distance;
    }

    // calculates the median of the last stored distances
    int mediana = median(distances, stored_distances);

    // Serial.print("Median: ");
    // Serial.println(mediana);

    if (mediana > max_dist) {
        if (has_observers){
            Serial.write(0);

            has_observers = false;
            // digitalWrite(buzzer_pin, HIGH);
            // is_buzzing = true;
            // loops_buzzing = 1;
        }
        red   = 255;
        green = 0;

    } else {
        Serial.write(1);

        has_observers = true;
        red   = 0;
        green = 255;
    }

    setColor(red, green, blue);

    if (has_observers) {
        digitalWrite(obs_pin, HIGH);
    } else {
        digitalWrite(obs_pin, LOW);
    }
}

// note that v_size should be less or equal to MAX_STORED_DISTANCES
int median(int *v, int v_size) {
    int vec[MAX_STORED_DISTANCES];
    int j, i;

    for (i = 0 ; i < MAX_STORED_DISTANCES; ++i) vec[i] = v[i];
  
    for (i = 0; i < v_size; ++i) {
        for (j = i-1; (j >= 0) && (vec[j] > vec[i]); --j) {
            vec[j+1] = vec[j];
        }
        vec[j+1] = vec[i];
    }

    return vec[v_size/2];
}

void connectWIFI() {
    Serial.print("Connecting Wi-Fi: ");
    WiFi.begin(ssid, pass);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println(" Wi-Fi connected!");
}

void connectMQTT() {
    Serial.print("Connecting MQTT: ");
    while (!client.connect(client_id, client_key, client_secret)) {
        delay(500);
        Serial.print(".");
    }
    Serial.println(" MQTT connected!");
}

void messageReceived(String &topic, String &payload) {
    Serial.println("New message: " + topic + " - " + payload);
    if (topic == "/red")   red   = payload.toInt();
    if (topic == "/green") green = payload.toInt();
    if (topic == "/blue")  blue  = payload.toInt();
}

void setColor(int r, int g, int b) {
    r = map(r, 0, 255, 0, 1023);
    g = map(g, 0, 255, 0, 1023);
    b = map(b, 0, 255, 0, 1023);
    analogWrite(red_pin,   r);
    analogWrite(green_pin, g);
    analogWrite(blue_pin,  b);
}