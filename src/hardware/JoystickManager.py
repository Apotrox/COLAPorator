from evdev import InputDevice, ecodes
import threading
from queue import Queue
from enum import Enum

class Intent(Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    SELECT = 4
    NOTHING = 5

class Joystick:
    def __init__(self):
        try:
            self.device = InputDevice('/dev/input/by-id/usb-Retro_Games_LTD_THECXSTICK-event-joystick')
        except Exception as e:
            print (e)
            return None #just escape if binding fails
        
        self._stop_event=threading.Event()
        self._thread =None
        self.events = Queue(maxsize=20) 

    def start(self):
        if self._thread: return
        self._thread = threading.Thread(target=self._run, name="Joystick Reader",daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def get(self) -> Intent | None:
        try:
            return self.events.get_nowait()
        except Exception as e:
            return None

    def _run(self):
        while not self._stop_event.is_set():
            try:
                event = self.device.read_one()
            except Exception as e:
                print("From run:", e)
                break
            
            intent = None
            
            if event and event.type == ecodes.EV_KEY and event.value==1:
                match event.code:
                    case 289: #Button Top
                            intent = Intent.UP
                    case 292: #Button Bottom
                            intent = Intent.DOWN
                    case 291: #Button Left
                            intent = Intent.LEFT
                    case 288: #Button Right
                            intent = Intent.RIGHT
                    case 290: #Button Trigger
                            intent = Intent.SELECT
                    case _:
                        pass
            elif event and event.type == ecodes.EV_ABS:
                if(event.code==0):
                    match event.value:
                        case 255: #Stick right
                            intent = Intent.RIGHT
                        case 0: #Stick left
                            intent = Intent.LEFT
                elif(event.code==1):
                    match event.value:
                        case 0: #Stick Top
                            intent = Intent.UP
                        case 255: #Stick Bottom
                            intent = Intent.DOWN
            if(intent):
                self.events.put_nowait(intent)
             


##INFO
# X-Axis: Code 00
#   Zero Position: value 127
#   right: value 255
#   left: value 00

# Y-Axis: Code 01
#   Zero: value 127
#   Top: value 00
#   bottom: value 255

# Note that position changes will be reported *EVERY* time. Basically every time there's an "down" and "up" trigger. For every up trigger, the value is 127 because "up" means going back to zero/center

# Button circle:
#   value 01 when pressed, value 00 when released
#   Top: code 289
#   Bottom: code 292
#   Left: code 291
#   Right: code 288

# Trigger Button:
#   code 290
#   value 01 when pressed

# Other buttons:
#   "shoulder Button": code 293
#   "twin buttons": code 294 for left, 295 for right