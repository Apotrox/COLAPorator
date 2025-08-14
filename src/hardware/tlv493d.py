import time, board, busio, adafruit_tlv493d
import math
import json
import statistics
import threading


class TLV493D:
    #global mean_angle, arctan
    
    def __init__(self):
        self._stop_event = threading.Event()
        # Initialize I2C and sensor
        i2c = busio.I2C(board.SCL, board.SDA)
        i2c.unlock() #sometimes the i2c bus is taken by a previous instance of this tool (or just bugged out) and requires manual unlocking
        self.tlv = adafruit_tlv493d.TLV493D(i2c)
        self.mean_angle=0
        self.arctan=0.0000
        self.is_moving=False

    def start_reading(self):
        #moving average filter to reduce noise
        num_readings = 8 # 8 offers pretty good latency while still being stable enough
        readings = [self.tlv.magnetic] * num_readings

        while not self._stop_event.is_set():
            for i in range (0,num_readings-1):
                time.sleep(0.1)
                magnet = self.tlv.magnetic
                angle = math.degrees(math.atan2(magnet[1], magnet[0]))
                
                if(angle <0): angle +=360
                
                
                readings[i]=angle
                self.mean_angle = statistics.mean(readings)
                
                threshold = 10
                if abs(readings[0] - readings [4]) > threshold:
                    self.is_moving=True
                else:
                    self.is_moving=False

    def stop_reading(self):
        self._stop_event.set()

    def get_angle(self):
        return int(self.mean_angle)
    
    def get_arctan(self):
        return self.arctan
    
    def get_moving(self):
        return self.is_moving

    #------Debugging Helpers--------------

    def create_json_data(self, readings, angle):
        # Prepare data for JSON
        data = {
            "timestamp": time.time(),
            "X": readings[0],
            "Y": readings[1],
            "Z": readings[2],
            "angleXY": angle
        }
        return data

    def init_json(self):
        # Ensure JSON file exists
        self.filename = "magnetometer_data.json"
        with open(self.filename, "w") as f:
            json.dump([], f)

    def debug_json(self, data):
        """Outputs the read values in a json file for further analysis"""
        with open(self.filename, "r+") as f:
            try:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = []
            except json.JSONDecodeError:
                existing_data = []
            existing_data.append(data)
            f.seek(0)
            f.truncate()
            json.dump(existing_data, f, indent=4)