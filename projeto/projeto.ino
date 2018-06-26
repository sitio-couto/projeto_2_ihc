//projeto.ino
// sets up the pin assignments
const int obs_pin    = D9; // watched by the raspberry pi to know if there's an observer
const int red_pin    = D5;
const int green_pin  = D6;
const int blue_pin   = D7;
const int buzzer_pin = D3;
const int trig_pin   = D1;
const int echo_pin   = D0;
const int max_dist   = 100;

// stores the last MAX_STORED_DISTANCES distances
const int MAX_STORED_DISTANCES = 321;
boolean has_observers = false;
int counter = 0;

// starts with a red LED
int red   = 255;
int green = 0;
int blue  = 0;

void setup() {
    Serial.begin(115200);

    pinMode(obs_pin,    OUTPUT);
    pinMode(red_pin,    OUTPUT);
    pinMode(green_pin,  OUTPUT);
    pinMode(blue_pin,   OUTPUT);
    pinMode(buzzer_pin, OUTPUT);
    pinMode(trig_pin,   OUTPUT);
    pinMode(echo_pin,   INPUT);
}

void loop() {
    int stored_distances, mediana;
    int distances[MAX_STORED_DISTANCES];

    stored_distances = 0;

    while (stored_distances < MAX_STORED_DISTANCES) {
        // clears the trig_pin
        digitalWrite(trig_pin, LOW);
        delayMicroseconds(2);
        // sets the trig_pin on HIGH state for 10 micro seconds
        digitalWrite(trig_pin, HIGH);
        delayMicroseconds(10);
        digitalWrite(trig_pin, LOW);
        // reads the echo_pin and returns the sound wave travel time in microseconds
        distances[stored_distances++] = pulseIn(echo_pin, HIGH)*0.034/2;
    }

    mediana = median(distances, stored_distances);
    // Serial.println(mediana);

    if (mediana > max_dist) {
        if (has_observers){
            Serial.write(0);
            has_observers = false;
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
    quickSort(v, 0, v_size);
    return v[v_size/2];
}

void quickSort(int arr[], int left, int right) {
    int i = left, j = right;
    int tmp;
    int pivot = arr[(left + right) / 2];

    /* partition */
    while (i <= j) {
        while (arr[i] < pivot)
            i++;
            while (arr[j] > pivot) j--;
            if (i <= j) {
                tmp = arr[i];
                arr[i] = arr[j];
                arr[j] = tmp;
                i++;
                j--;
            }
      };

      /* recursion */
      if (left < j)
        quickSort(arr, left, j);
      if (i < right) 
        quickSort(arr, i, right);

}

void setColor(int r, int g, int b) {
    r = map(r, 0, 255, 0, 1023);
    g = map(g, 0, 255, 0, 1023);
    b = map(b, 0, 255, 0, 1023);
    analogWrite(red_pin,   r);
    analogWrite(green_pin, g);
    analogWrite(blue_pin,  b);
}