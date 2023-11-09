import time
import machine
import mqtt
import urequests as requests
from secrets import tufts, io_key
import network, ubinascii
import uasyncio as a
import gamepad as pad
import math

#Connects to wifi
def establish_connections():
    station = network.WLAN(network.STA_IF)
    station.active(True)
    mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()    
    station.connect(tufts['ssid'],tufts['pass'])
    while not station.isconnected():
        time.sleep(1)
    print('Connected to the internet')
    client.connect()
    print('Connected to Adafruit via MQTT')

#Initialize everything 
client = mqtt.MQTTClient(client_id='Phila', 
                    server='io.adafruit.com', 
                    user='phila_', 
                    password=io_key)
pad_pin = machine.Pin(0, machine.Pin.OUT)
celcius = machine.Pin(16, machine.Pin.OUT)
faren = machine.Pin(17, machine.Pin.OUT)
lights = [18,19,20,21,22,15,27,28]
light_pins = [machine.Pin(x, machine.Pin.OUT) for x in lights]
for pin in light_pins: pin.off()
celcius.off()
faren.off()
pad_pin.on()
temp = 0
temp_unit = 'C'
temp_sensor = machine.ADC(26)

#Reads temp
def read_temp():
     # Voltage Divider
    Vin = 3.3
    Ro = 10000  # 10k Resistor
    # Steinhart Constants
    A = 0.001129148
    B = 0.000234125
    C = 0.0000000876741
    adc = temp_sensor.read_u16()
    Vout = (3.3/65535)*adc
    # Calculate Resistance
    Rt = (Vout * Ro) / (Vin - Vout)
    # Steinhart - Hart Equation
    temp_k = 1 / (A + (B * math.log(Rt)) + C * math.pow(math.log(Rt), 3))
    # Convert from Kelvin to Celsius
    temp_c = temp_k - 273.15
    # Convert from Celcius to Fahrenheit
    temp_f = (temp_c * 9/5) + 32
    print('Curr temp', temp_c, 'C (', temp_f, 'F )')
    
    return temp_c

#Dispalys the temperature 
def display_temp(temp):
    vals = [0,0,0,0,0,0,0, 0]
    
    # celcius: temp < 20 is not displayed. Range 20 - 34, increments by 2
    for i in range(len(vals)):
        thresh = 20 + 2 * i
        if temp >= thresh:
            vals[len(vals) - 1 - i] = 1
    
    for i in range(len(vals)):
        if vals[i] == 1:
            light_pins[i].on()
        else:
            light_pins[i].off()
            
    if temp_unit == 'C':
        celcius.on()
        faren.off()
    else:
        celcius.off()
        faren.on()
    

#Reads and posts the temperature to adafruit 
async def process_temp():
    global temp
    temp_c_topic = 'phila_/feeds/midterm.temp_c'
    temp_f_topic = 'phila_/feeds/midterm.temp_f'
    last_pushed = time.time()
    
    while True:
        
        #Read temp 
        temp = read_temp()
        # x, y = 1023 - pad.read_joystick(14), 1023 - pad.read_joystick(15)
        
        #display temp
        display_temp(read_temp())
        
        #Push if over 5 min since last push 
        if time.time() > last_pushed + (5 * 60):
            client.publish(temp_c_topic, str(i))
            client.publish(temp_f_topic, str(i * (9/5) + 32))
            print('Pushed temp to Adafruit')
            last_pushed = time.time()
            
        #Change display units on gamepad press
        if y > 900:
            temp_unit = 'C'
            print('Switched temp unit to C')
        elif y < 300:
            temp_unit = 'F'
            print('Switched temp unit to F')
            
        await a.sleep(1)
            
    
#Reads airtable cell, updates adafruit, and toggles between F and C based on color 
async def watch_airtable():
    global temp_unit
    last_color = 'Random'
    
    #Integrated ic2 device = gamepad. Move joystick up or down to switch between C and F
    while True:

        #Read airtable color data
        token = 'patbDnBxDqYjUCD8m.6c5194d260e2b1d692e46fb759db93e822eb8570409d13c4050ba861bccbe28b'
        url = "https://api.airtable.com/v0/applFraZvr74IZXEL/Colors/recPoZwtOE2AmioZU"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        data = response.json()
        color_got = data['fields']['Color']
        print('Latest color from Airtable', color_got)
        
        #Update Adafruit color feed over MQTT
        if color_got != last_color:
            color_topic = 'phila_/feeds/midterm.color'
            client.publish(color_topic, color_got)
            last_color = color_got
            print('Pushed updated color to Adafruit')
        
        #Update display. Green = Celcius, Red = Farenheit
        if color_got == 'Green': temp_unit = 'C'
        else: temp_unit = 'F'
        display_temp(read_temp())
        await a.sleep(1)
            
        
async def main():
    await a.gather(watch_airtable())
  
establish_connections()
pad.digital_setup()
a.run(main())


