from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput

import math, threading
from backend.tlv493d import TLV493D
from backend.database_manager import Manager

class AngleDisplay(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 0
        Clock.schedule_interval(self.update_canvas, 1 / 30)
        self.tlv = TLV493D()
        data_collector = threading.Thread(target=self.tlv.start_reading, name="TLV_Reader", daemon=True).start() #multithreading data collection
        self.label = Label(pos=(10, self.height - 40), size_hint=(None, None))
        self.add_widget(self.label)


    def update_canvas(self, dt):
        self.angle = self.tlv.get_angle()
        self.canvas.clear()
        with self.canvas:
            Color(1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)

            cx, cy = self.center
            radius = min(self.width, self.height) * 0.4

            # Draw outer circle
            Color(0, 1, 0)
            Ellipse(pos=(cx - radius, cy - radius), size=(radius * 2, radius * 2), width=2)

            # Draw rotating line
            rad = math.radians(self.angle)
            x = cx + radius * math.cos(rad)
            y = cy + radius * math.sin(rad)
            Color(1, 0, 0)
            Line(points=[cx, cy, x, y], width=2)

            # Draw angle text
            Color(0, 0, 0)
            self.label.text = f"{self.angle:.1f}°"
            self.label.canvas.ask_update()


class StartupScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

        layout = BoxLayout(orientation='vertical') #use boxlayout inside the screen, a screen should contain a layout, not be one

        auto_button = Button(text="Automatic Calibration")
        auto_button.bind(on_press=self.auto_cfg)
        manual_button = Button(text="Manual Configuration")
        manual_button.bind(on_press=self.manual_cfg)
        
        layout.add_widget(auto_button)
        layout.add_widget(manual_button)

        self.add_widget(layout)

    def auto_cfg(self, *args):
        self.manager.current='auto'
    
    def manual_cfg(self, *args):
        self.manager.current='manual'

class AutoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

        base_layout = BoxLayout(orientation = "horizontal")
        left_layout = FloatLayout()

        back = Button(text="Back", size_hint=(0.14, 0.06), pos_hint={'x': 0.02, 'y': 0.02})
        back.bind(on_press=self.go_back)

        self.textinput = TextInput(hint_text="Input number of slices", size_hint=(0.8,0.1), multiline=False, pos_hint={'x': 0.1, 'y': 0.85})
        self.textinput.bind(on_text_validate=self.calculate)
        
        enter = Button(text="Enter", size_hint=(0.15,0.075), pos_hint={'x': 0.75, 'y': 0.75})
        enter.bind(on_press=self.calculate)

        angle_display = AngleDisplay()
        left_layout.add_widget(self.textinput)
        left_layout.add_widget(enter)
        left_layout.add_widget(back)
        base_layout.add_widget(left_layout)
        base_layout.add_widget(angle_display)

        self.add_widget(base_layout)

    def go_back(self, *args):
        self.manager.current = 'startup'
    
    def calculate(self, _): #input at instance.text
        print(self.textinput.text)

class ManualScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        back = Button(text="Back")
        back.bind(on_press=self.go_back)
        self.add_widget(back)

    def go_back(self, *args):
        self.manager.current = 'startup'


class ConfigApp(App):
    def build(self):
        sm = ScreenManager()
        startup_screen = StartupScreen(name="startup")
        auto_screen = AutoScreen(name="auto")
        manual_screen = ManualScreen(name="manual")

        sm.add_widget(startup_screen)
        sm.add_widget(auto_screen)
        sm.add_widget(manual_screen)

        return sm

if __name__ == '__main__':
    ConfigApp().run()
