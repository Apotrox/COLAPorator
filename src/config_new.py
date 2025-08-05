from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
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

class AngleDisplay(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 0
        self.tlv = TLV493D()
        threading.Thread(target=self.tlv.start_reading, daemon=True).start()

        # Label added as widget
        self.label = Label(text="0°", color=(0,0,1,1), pos_hint={'x':0, 'y':0.3}, font_size='40sp')
        self.add_widget(self.label)

        # Static background + circle (draw once)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)

            Color(0, 1, 0)
            self.circle = Ellipse(size=(0, 0), pos_hint={'x':0.5, 'y':1})

        # Dynamic line (redraw in canvas.after)
        with self.canvas.after:
            self.line_color = Color(1, 0, 0)
            self.line = Line(points=[0, 0, 0, 0], width=2)

        # Update canvas and geometry
        self.bind(pos=self.update_static, size=self.update_static)
        Clock.schedule_interval(self.update_dynamic, 1 / 40)

    def update_static(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

        cx = self.x + self.width * 0.5
        cy = self.y + self.height * 0.5
        radius = min(self.width, self.height) * 0.4
        self.circle.pos = (cx - radius, cy - radius)
        self.circle.size = (radius * 2, radius * 2)

    def update_dynamic(self, dt):
        self.angle = -self.tlv.get_angle()
        self.label.text = f"{-self.angle:.1f}°"

        cx, cy = self.center
        radius = min(self.width, self.height) * 0.4
        rad = math.radians(self.angle)
        x = cx + radius * math.cos(rad)
        y = cy + radius * math.sin(rad)

        self.line.points = [cx, cy, x, y]



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
        self.data =[] 

        base_layout = BoxLayout(orientation = "horizontal")
        left_layout = FloatLayout()
        right_layout = FloatLayout()

        back = Button(text="Back", size_hint=(0.14, 0.06), pos_hint={'x': 0.02, 'y': 0.02})
        back.bind(on_press=self.go_back)

        self.textinput = TextInput(hint_text="Input number of slices", size_hint=(0.8,0.1), multiline=False, pos_hint={'x': 0.1, 'y': 0.85})
        self.textinput.bind(on_text_validate=self.calculate)
        
        enter = Button(text="Enter", size_hint=(0.15,0.075), pos_hint={'x': 0.75, 'y': 0.75})
        enter.bind(on_press=self.calculate)

        hint_label = Label(text="Align any slice edge with the pointer, enter the number of slices above and press enter.",
                           text_size=(220,None), pos_hint={'x':-0.08, 'y':0.29})

        table = GridLayout(cols=2, pos_hint={'x':0, 'y':-0.3}, row_force_default=True, row_default_height=40 )
        for row in self.data:
            for cell in row:
                table.add_widget(Label(text=str(cell), color=(1,1,1,1)))

        confirm = Button(text="Confirm", size_hint=(0.18, 0.06), pos_hint={'x':0.8, 'y':0.02})
        #confirm.bind(on_press=None)

        angle_display = AngleDisplay(pos_hint={'x':0.01, 'y':0})
        right_layout.add_widget(angle_display)
        right_layout.add_widget(confirm)

        left_layout.add_widget(self.textinput)
        left_layout.add_widget(enter)
        left_layout.add_widget(hint_label)
        left_layout.add_widget(table)
        left_layout.add_widget(back)

        base_layout.add_widget(left_layout)
        base_layout.add_widget(right_layout)

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
