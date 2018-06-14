//projeto.ino

#include <ESP8266WiFi.h>
#include <MQTTClient.h>

const char client_id[] = "microcontrolador";     //arbitrary identification
const char client_key[] = "a0160aee";                   //token KEY from shiftr.io
const char client_secret[] = "eb90656ac81576b0";                //token SECRET from shiftr.io

const char ssid[] = "11111";     //name of the used Wi-Fi network
const char pass[] = "21111";     //password of the Wi-Fi network

WiFiClient net;
MQTTClient client;
const int QoS = 1;

const int red_pin = D5;
const int green_pin = D6;
const int blue_pin = D7;
const int trig_pin = D1;
const int echo_pin = D0;
const int buzzer = D3;
const int max_dist = 40;
boolean pessoa = false;
int distancias[10];
int i = -1;

int red = 255;
int green = 0;
int blue = 0;

// defines variables
long duration;
int distance;
//boolean person = false;

void setup() {
  // put your setup code here, to run once:
    Serial.begin(115200);

    pinMode(red_pin, OUTPUT);
    pinMode(green_pin, OUTPUT);
    pinMode(blue_pin, OUTPUT);
  	pinMode(trig_pin, OUTPUT); // Sets the trig_pin as an Output
	pinMode(echo_pin, INPUT); // Sets the echo_pin as an Input
	pinMode(buzzer, OUTPUT); // Set buzzer as an output


    //connectWIFI();
    client.begin("broker.shiftr.io", net);
    //client.onMessage(messageReceived);
    //connectMQTT();

    client.subscribe("/red");
    client.subscribe("/green");
    client.subscribe("/blue");
}

void loop() {
  // put your main code here, to run repeatedly:

  // Clears the trig_pin
	digitalWrite(trig_pin, LOW);
	delayMicroseconds(2);
	// Sets the trig_pin on HIGH state for 10 micro seconds
	digitalWrite(trig_pin, HIGH);
	delayMicroseconds(10);
	digitalWrite(trig_pin, LOW);
	// Reads the echo_pin, returns the sound wave travel time in microseconds
	duration = pulseIn(echo_pin, HIGH);
	// Calculating the distance
	distance= duration*0.034/2;
	// Prints the distance on the Serial Monitor
	Serial.print("Distance: ");
	Serial.println(distance);

	if(i < 9){
		i++;
		distancias[i] = distance;
	} else {
		for(int j = 0; j < 9; j++){
			distancias[j] = distancias[j+1];
		}
		distancias[9] = distance;
	}

	int mediana = medf(distancias, i+1);

	Serial.print("MEDIANA: ");
	Serial.println(mediana);

	if(mediana > max_dist){
		//if(pessoa){
		//	pessoa = false;
		//	tone(buzzer, 100, 1000); // Send 1KHz sound signal for 1 sec
		//}
		red = 255;
		green = 0;
	} else{
		//pessoa = true;
		red = 0;
		green = 255;
	}

	setColor(red, green, blue);
}

void connectWIFI()
{
    Serial.print("Connecting Wi-Fi: ");
    WiFi.begin(ssid, pass);
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }
    Serial.println(" Wi-Fi connected!");
}

void connectMQTT()
{
    Serial.print("Connecting MQTT: ");
    while (!client.connect(client_id, client_key, client_secret))
    {
        delay(500);
        Serial.print(".");
    }
    Serial.println(" MQTT connected!");
}

void messageReceived(String &topic, String &payload)
{
    Serial.println("New message: " + topic + " - " + payload);

    if (topic == "/red")
    {
        red = payload.toInt();
    }

    if (topic == "/green")
    {
        green = payload.toInt();
    }

    if (topic == "/blue")
    {
        blue = payload.toInt();
    }
}

void setColor(int r, int g, int b)
{
    r = map(r, 0, 255, 0, 1023);
    g = map(g, 0, 255, 0, 1023);
    b = map(b, 0, 255, 0, 1023);
    analogWrite(red_pin, r);
    analogWrite(green_pin, g);
    analogWrite(blue_pin, b);
}

int medf(int *b, int n)
{
	int a[10];
	for(int c = 0; c < 10; c++){
		a[c] = b[c];
	}
 for (int d = 1; d < n; ++d)
 {
   int j = a[d];
   int k;
   for (k = d - 1; (k >= 0) && (j < a[k]); k--)
   {
     a[k + 1] = a[k];
   }
   a[k + 1] = j;
 }
 return a[5];
}