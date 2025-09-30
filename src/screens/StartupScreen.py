from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from kivy.graphics import Color, Rectangle

from kivy.clock import Clock

from hardware.JoystickManager import Joystick, Intent


class StartupScreen(Screen):
    def __init__(self, js:Joystick, **kw):
        super().__init__(**kw)
        
        self.js=js
        
        self.startup_label = Label(
            text='Spin the wheel to start or press the Select button',
            font_size="26sp",
            color=(0.2, 0.2, 0.2, 1),
            pos_hint={"center_x":0.5, "center_y":0.5}
        )
        hint_label = Label(
            text="Hint: You can spin the wheel at any point to reselect the category!",
            font_size="22sp",
            color=(0.3,0.3,0.3,1),
            pos_hint={"center_x":0.5, "center_y":0.3}
        )
        
        with self.canvas.before:
            Color(rgba=(0.95, 0.95, 0.95, 1))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
                # Update background when layout changes
        self.bind(pos=self.update_bg, size=self.update_bg)
        
        self.add_widget(self.startup_label)
        self.add_widget(hint_label)        
        
        if self.js:
            Clock.schedule_interval(self.check_joystick_events, 0.1)
        
    def update_bg(self, instance, _):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        
    def check_joystick_events(self, *_):
        if self.manager.current=='startup':
            intent= self.js.get() #don't need to be here if it isnt the active screen
            if intent:
                self.handle_joystick_intents(intent)
    
    def handle_joystick_intents(self, intent:Intent):
        if intent== Intent.SELECT:
            Clock.unschedule(self.check_joystick_events)
            Clock.unschedule(App.get_running_app().check_movement) #quick and dirty i admit...
            App.get_running_app().check_stopped()