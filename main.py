import time, _thread, network, ujson, gc
from machine import Pin, ADC, reset, freq, unique_id
from ubinascii import hexlify
from ntptime import settime

try:
  import usocket as socket
except:
  import socket

gc.enable()

class Stepper:
    # Stepper class source: https://github.com/zhcong/ULN2003-for-ESP32
    
    FULL_ROTATION = int(4075.7728395061727 / 8) # http://www.jangeox.be/2013/10/stepper-motor-28byj-48_25.html

    HALF_STEP = [
        [0, 0, 0, 1],
        [0, 0, 1, 1],
        [0, 0, 1, 0],
        [0, 1, 1, 0],
        [0, 1, 0, 0],
        [1, 1, 0, 0],
        [1, 0, 0, 0],
        [1, 0, 0, 1],
    ]

    FULL_STEP = [
        [1, 0, 1, 0],
        [0, 1, 1, 0],
        [0, 1, 0, 1],
        [1, 0, 0, 1]
    ]

    def __init__(self, mode, pin1, pin2, pin3, pin4, delay):
    	if mode=='FULL_STEP':
        	self.mode = self.FULL_STEP
        else:
            self.mode = self.HALF_STEP
        self.pin1 = pin1
        self.pin2 = pin2
        self.pin3 = pin3
        self.pin4 = pin4
        self.delay = delay  # Recommend 10+ for FULL_STEP, 1 is OK for HALF_STEP
        
        # Initialize all to 0
        self.reset()

    def step(self, count, direction=1, monitor_limits=0):
        if direction == 0:
            direction = -1

        """Rotate count steps. direction = -1 means backwards"""
        for x in range(count):

            if monitor_limits: # stop if either of limit switches is triggered
                if io19.value() == 0 and direction == 1:
                    break
                if io18.value() == 0 and direction == -1:
                    break

            for bit in self.mode[::direction]:
                self.pin1(bit[0])
                self.pin2(bit[1])
                self.pin3(bit[2])
                self.pin4(bit[3])
                time.sleep_ms(self.delay)
        self.reset()

    def angle(self, r, direction=1, monitor_limits=0):
    	self.step(int(self.FULL_ROTATION * r / 360), direction, monitor_limits)

    def reset(self):
        # Reset to 0, no holding, these are geared, you can't move them
        self.pin1(0) 
        self.pin2(0) 
        self.pin3(0) 
        self.pin4(0)

class Tracker:
    # Tracker monitors solar panel levels and turns stepper motors accordingly

    def __init__(self):
        self.running = False
        self.angle_threshold = 1
        self.level_threshold = 70
        self.flip_h_axis = 0
        self.avg_panel_level = round(sum(self.get_panel_levels()) / 4, 1)
        self.hibernate = False

    def __main_loop__(self):
        self.running = True
        self.hibernate = True

        while self.running == True:
            try:
                self.avg_panel_level = round(sum(self.get_panel_levels()) / 4, 1)

                if self.avg_panel_level >= self.level_threshold:
                    if freq() != 240000000:
                        freq(240000000)
                    
                    if self.hibernate:
                        while abs(self.get_h_step_angle()) > self.angle_threshold:
                            stepper_h.angle(abs(self.get_h_step_angle() * 4), self.get_h_step_direction())

                        v_direction = self.get_v_step_direction()
                        while io18.value() == 1 and io19.value() == 1:
                            stepper_v.angle(1, v_direction, monitor_limits=1)

                        self.hibernate = False
                        continue

                    if abs(self.get_h_step_angle()) > self.angle_threshold:
                        stepper_h.angle(abs(self.get_h_step_angle() * 4), self.get_h_step_direction())
                    
                    if abs(self.get_v_step_angle()) > self.angle_threshold:
                        stepper_v.angle(abs(self.get_v_step_angle() * 2), self.get_v_step_direction(), monitor_limits=1)

                elif not self.hibernate:
                    # level the panel array, drop CPU frequency
                    v_direction = self.get_v_step_direction()
                    while io18.value() == 1 and io19.value() == 1:
                        stepper_v.angle(1, v_direction, monitor_limits=1)

                    stepper_v.angle(110, io19.value(), monitor_limits=1)
                    
                    freq(80000000)
                    self.hibernate = True

                time.sleep(0.2) # cap loop cycle

            except Exception as e:
                print(e)
                self.running = False
    
    def get_panel_levels(self):
        return [round((sp2_lvl.read()) / 4095 * 100, 3), \
                round((sp3_lvl.read()) / 4095 * 100, 3), \
                round((sp4_lvl.read()) / 4095 * 100, 3), \
                round((sp5_lvl.read()) / 4095 * 100, 3)]

    def run(self):
        self.main_thread = _thread.start_new_thread(self.__main_loop__, ())

    def stop(self):
        self.running = False
        del self.main_thread

    def get_v_step_angle(self):
        return int(((self.get_panel_levels()[0] - self.get_panel_levels()[2]) / 100) * 110)

    def get_v_step_direction(self):
        if self.get_v_step_angle() > 0:
            return 0
        else:
            return 1

    def get_h_step_angle(self):
        return int(((self.get_panel_levels()[1] - self.get_panel_levels()[3]) / 100) * 180)

    def get_h_step_direction(self):
        if self.get_panel_levels()[0] > self.get_panel_levels()[2] and self.hibernate:
            self.flip_h_axis = True
        elif not io18.value() or not io19.value():
            self.flip_h_axis = not io18.value()
        elif self.hibernate:
            self.flip_h_axis = False

        if (self.get_h_step_angle() > 0 and not self.flip_h_axis) or (self.get_h_step_angle() < 0 and self.flip_h_axis):
            return 0
        else:
            return 1

def init_network(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(dhcp_hostname="solartracker")

    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

class HTTPServer:
    # https://docs.micropython.org/en/latest/esp8266/tutorial/network_tcp.html#simple-http-server
    # Server monitors HTTP requests sent through the web UI and executes functions accordingly

    def __init__(self):
        self.running = False

    def __main_loop__(self):
        try:
            self.running = True

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # setup a socket s
            s.bind(('', 80)) # bind the socket s to port 80
            s.listen(5) # set the socket s to listen for incoming connections, max 5 simultaneous conns

            while self.running == True:
                conn, addr = s.accept()
                # print('Got a connection from %s' % str(addr))
                request = str(conn.recv(1024))
                # print(request)

                if request.find('/?trackeron') != -1:
                    tracker.run()
                elif request.find('/?trackeroff') != -1:
                    tracker.stop()
                elif request.find('/?rotatehccw') != -1:
                    stepper_h.angle(45*4, 1)
                elif request.find('/?rotatehcw') != -1:
                    stepper_h.angle(45*4, 0)
                elif request.find('/?rotatevccw') != -1:
                    stepper_v.angle(27*2, 1, monitor_limits=1)
                elif request.find('/?rotatevcw') != -1:
                    stepper_v.angle(27*2, 0, monitor_limits=1)
                elif request.find('/?restart') != -1:
                    reset()
                elif request.find('/?status') != -1:
                    conn.send(ujson.dumps({'powerlevel':tracker.avg_panel_level, 'hibernate':tracker.hibernate, 'running':tracker.running}))
                else:
                    conn.send('HTTP/1.1 200 OK\n')
                    conn.send('Content-Type: text/html\n')
                    conn.send('Connection: close\n\n')
                    conn.sendall(parse_webpage())

                conn.close()

        except Exception as e:
            print(e)
            s.close()
            self.stop()

    def run(self):
        self.thread = _thread.start_new_thread(self.__main_loop__, ())

    def stop(self):
        self.running = False
        del self.thread

def parse_webpage():
    # Replace comments within index.html with variable information etc.

    with open("index.html","r") as f:
        page = f.read()

        with open('index.js', 'r') as js_f:
            js_source = js_f.read()
            page = page.replace('// external js file content', js_source)

    return page

# init solar panel level monitoring adc:s
# since the panel output can go as high as 8V, 2.5dB attenuation is applied giving ADC:s a voltage range of 0...1.34V
sp2_lvl = ADC(Pin(33))
sp2_lvl.atten(ADC.ATTN_2_5DB)
sp3_lvl = ADC(Pin(32))
sp3_lvl.atten(ADC.ATTN_2_5DB)
sp4_lvl = ADC(Pin(35))
sp4_lvl.atten(ADC.ATTN_2_5DB)
sp5_lvl = ADC(Pin(34))
sp5_lvl.atten(ADC.ATTN_2_5DB)

# init input pins for limit switches
io18 = Pin(18, Pin.IN)
io19 = Pin(19, Pin.IN)

# init horizontal/vertical stepper motors
stepper_h = Stepper(mode="HALF_STEP", pin1=Pin(4,Pin.OUT), pin2=Pin(16,Pin.OUT), pin3=Pin(17,Pin.OUT), pin4=Pin(5,Pin.OUT), delay=2)
stepper_v = Stepper(mode="HALF_STEP", pin1=Pin(12,Pin.OUT), pin2=Pin(14,Pin.OUT), pin3=Pin(27,Pin.OUT), pin4=Pin(26,Pin.OUT), delay=2)

tracker = Tracker()
tracker.run()

# get wifi ssid and password from a separate 'network.credentials' file
with open('network.credentials', 'r') as f:
    try:
        credentials = f.read()

        ssid = credentials.split(',')[0]
        password = credentials.split(',')[1]
        
        init_network(ssid, password)

        settime()

        httpserver = HTTPServer()
        httpserver.run()

    except Exception as e:
        print(e)
        
freq(80000000) # set CPU frequency to 80MHz
