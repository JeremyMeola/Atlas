
#define DEFAULT_RATE 115200
#define WHOIAM "lidarbase"  // define whoiam ID here (unique to each robot object)
#define LED13 13
#define MOTOR_PIN 3

#define ENCODER_PIN_1 2
#define ENCODER_PIN_2 4
#define MACRO_ENCODER_PIN A0
#define EMITTER_PIN 5

#define MOTOR_SPEED 255
byte encoderPin1Last;
byte numPulses = 0;
boolean direction;
unsigned long long numRotations = 0;

unsigned long prev_time = 0;
unsigned long curr_time = 0;
unsigned long delta_time = 0;

#define MACRO_ENCODER_THRESH 875
bool macro_enc_low = false;
int macro_enc = 0;
int prev_macro_enc = 0;
// unsigned long long macro_acq_t0 = millis();

char character = '\0';
char command_type = '\0';
String command = "";

bool paused = true;

bool led_state = false;

// Extremely fast string to int function
char _int2str[7];
char* int2str(register int i) {
    register unsigned char L = 1;
    register char c;
    register boolean m = false;
    register char b;  // lower-byte of i
    // negative
    if ( i < 0 ) {
        _int2str[ 0 ] = '-';
        i = -i;
    }
    else L = 0;
    // ten-thousands
    if( i > 9999 ) {
        c = i < 20000 ? 1
        : i < 30000 ? 2
        : 3;
        _int2str[ L++ ] = c + 48;
        i -= c * 10000;
        m = true;
    }
    // thousands
    if( i > 999 ) {
        c = i < 5000
        ? ( i < 3000
            ? ( i < 2000 ? 1 : 2 )
            :   i < 4000 ? 3 : 4
        )
        : i < 8000
        ? ( i < 6000
            ? 5
            : i < 7000 ? 6 : 7
        )
        : i < 9000 ? 8 : 9;
        _int2str[ L++ ] = c + 48;
        i -= c * 1000;
        m = true;
    }
    else if( m ) _int2str[ L++ ] = '0';
    // hundreds
    if( i > 99 ) {
        c = i < 500
        ? ( i < 300
            ? ( i < 200 ? 1 : 2 )
            :   i < 400 ? 3 : 4
        )
        : i < 800
        ? ( i < 600
            ? 5
            : i < 700 ? 6 : 7
        )
        : i < 900 ? 8 : 9;
        _int2str[ L++ ] = c + 48;
        i -= c * 100;
        m = true;
    }
    else if( m ) _int2str[ L++ ] = '0';
    // decades (check on lower byte to optimize code)
    b = char( i );
    if( b > 9 ) {
        c = b < 50
        ? ( b < 30
            ? ( b < 20 ? 1 : 2 )
            :   b < 40 ? 3 : 4
        )
        : b < 80
        ? ( i < 60
            ? 5
            : i < 70 ? 6 : 7
        )
        : i < 90 ? 8 : 9;
        _int2str[ L++ ] = c + 48;
        b -= c * 10;
        m = true;
    }
    else if( m ) _int2str[ L++ ] = '0';
    // last digit
    _int2str[ L++ ] = b + 48;
    // null terminator
    _int2str[ L ] = 0;
    return _int2str;
}

void encoderInit()
{
    direction = true;  //default -> Forward
    pinMode(ENCODER_PIN_2, INPUT);
    attachInterrupt(0, encoderCallback, CHANGE);//int.0

    pinMode(MACRO_ENCODER_PIN, INPUT);
    macro_enc_low = analogRead(MACRO_ENCODER_PIN) < MACRO_ENCODER_THRESH;
}

bool checkMacroEnc()
{
    // if (numPulses > 1000) {
    macro_enc = analogRead(MACRO_ENCODER_PIN);
    // Serial.print("\nmacro_enc:");
    // Serial.print(macro_enc);

    if (macro_enc > MACRO_ENCODER_THRESH && macro_enc_low)
    {
        macro_enc_low = false;
        return true;
    }
    else if (macro_enc < MACRO_ENCODER_THRESH) {
        macro_enc_low = true;
    }
    // }
    return false;
}

void encoderCallback()
{
    byte state = digitalRead(ENCODER_PIN_1);
    if (encoderPin1Last == LOW && state == HIGH)
    {
        byte val = digitalRead(ENCODER_PIN_2);
        if (val == LOW && direction) {
            direction = false;  // Reverse
        }
        else if (val == HIGH && !direction) {
            direction = true;  // Forward
        }
    }
    encoderPin1Last = state;
    if (!direction)  numPulses++;
    else  numPulses--;
}

unsigned long dt()
{
    curr_time = micros();
    if (prev_time < curr_time) {
        delta_time = (0xffffffffUL - prev_time) + curr_time;
    }
    else {
        delta_time = curr_time - prev_time;
    }
    prev_time = curr_time;

    return delta_time;
}

void writeWhoiam()
{
    Serial.print("iam");
    Serial.print(WHOIAM);
    Serial.print('\n');
}

void setLed(bool state)
{
    led_state = state;
    digitalWrite(LED13, led_state);
}

void pause()
{
    digitalWrite(EMITTER_PIN, LOW);
    analogWrite(MOTOR_PIN, 0);

    Serial.print("stopping\n");

    paused = true;
}

void unpause()
{
    digitalWrite(EMITTER_PIN, HIGH);
    analogWrite(MOTOR_PIN, MOTOR_SPEED);

    numRotations = 0;

    curr_time = micros();
    prev_time = curr_time;

    paused = false;
}

void readSerial()
{
    while (Serial.available() && character != '\n')
    {
        character = Serial.read();
        if (character != '\n') {
            command += character;
        }
    }

    if (character == '\n')
    {
        command_type = command.charAt(0);
        if (command.equals("whoareyou")) {
            writeWhoiam();
        }
        else if (command.equals("init?"))
        {
            digitalWrite(LED13, HIGH);
            writeInit();
        }
        else if (command.equals("start"))
        {
            digitalWrite(LED13, HIGH);
            unpause();
        }
        else if (command.equals("stop"))
        {
            digitalWrite(LED13, LOW);
            pause();
        }
        else if (command_type == 'p')
        {
           if ((bool)(command.substring(1).toInt())) {
               pause();
           }
           else{
               unpause();
           }
        }

        character = '\0';
        command = "";
    }
}

void writeSerial()
{
    // ticks, distance (tab seperated)
    if (numPulses > 0) {
        noInterrupts();
        Serial.print(int2str(numPulses));  // num pulses since last update
        numPulses = 0;
        interrupts();

        Serial.print('\t');
        Serial.print(dt());

        if (checkMacroEnc()) {
            Serial.print('\t');
            numRotations++;
            Serial.print(int2str(numRotations));
        }
        Serial.print('\n');
    }

    delay(1);
}

void writeInit()
{
    Serial.print("init:");
    Serial.print('\n');
}

void setup()
{
    Serial.begin(DEFAULT_RATE);

    encoderInit();

    pinMode(MOTOR_PIN, OUTPUT);
    pinMode(LED13, OUTPUT);
    pinMode(EMITTER_PIN, OUTPUT);
}

void loop()
{
    if (!paused) {
        writeSerial();
    }
    else {
        delay(100);  // Minimize activity when not in use
    }

    readSerial();
}
