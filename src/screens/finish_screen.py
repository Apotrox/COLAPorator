from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.uix.screenmanager import FadeTransition, SlideTransition
from kivy.uix.slider import Slider
from kivy.metrics import dp, sp

from ui.SelectableButton import SelectableButton
from data.Guest import Guest
from services.GuestService import GuestService
from hardware.JoystickManager import Joystick, Intent

class FinishScreen(Screen):
    def __init__(self, js: Joystick, **kw):
        super().__init__(**kw)
        self.js=js
        
        self.main_layout = FloatLayout()
        
        
        # Set background
        with self.main_layout.canvas.before:
            Color(rgba=(0.95, 0.95, 0.95, 1))
            self.bg_rect = Rectangle(pos=self.main_layout.pos, size=self.main_layout.size)
        
        # Update background when layout changes
        self.main_layout.bind(pos=self.update_bg, size=self.update_bg)
        
        label = Label(text="Would you like to leave an entry in our guestbook?", color=(0,0,0,1), font_size="20sp", size_hint=(0.3, 0.2), pos_hint={"center_x":0.5, "center_y":0.6})
        self.main_layout.add_widget(label)  
        
        
        yes_button = SelectableButton(text="Yes", size_hint=(0.2, 0.1), pos_hint={"center_x":0.3, "center_y":0.45}, db_id=1)
        yes_button.hovered=False
        yes_button.bind(on_press=self.go_to_guest)
        self.main_layout.add_widget(yes_button)
        
        no_button = SelectableButton(text="No", size_hint=(0.2, 0.1), pos_hint={"center_x":0.7, "center_y":0.45}, db_id=2)
        no_button.hovered=False
        no_button.bind(on_press=self.restart)
        self.main_layout.add_widget(no_button)
        
        self.back_button = SelectableButton(text="Go Back", size_hint=(0.2, 0.1), pos_hint={"x":0.05, "y":0.03}, db_id=0)
        self.back_button.hovered=True
        self.back_button.bind(on_press=self.go_back)
        self.main_layout.add_widget(self.back_button)
        
        
        
        self.add_widget(self.main_layout)
    
    
    def update_bg(self, instance, _):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def go_to_guest(self, *_):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'guest'
    
    def restart(self, *_):
        
        popup=Popup(title="Thank You!",
                    content=Label(text="Thank You for your participation!", font_size="30sp"), size_hint=(None,None), size=(500,150), auto_dismiss=True)
        Clock.schedule_once(popup.dismiss, 3)
        popup.open()
        
        self.manager.transition=FadeTransition()
        self.manager.current="startup"

    def go_back(self, *_):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'topic_list'
            

    def on_enter(self):
        if self.js:
            Clock.schedule_interval(self.check_joystick_events, 0.1)    
    
    
    def check_joystick_events(self, *_):
        if self.manager.current=='finish':
            intent= self.js.get() #don't need to be here if it isnt the active screen
            if intent:
                self.handle_joystick_intents(intent)
    
    def handle_joystick_intents(self, intent:Intent):
        buttons = [x for x in self.main_layout.children if isinstance(x, SelectableButton)==True]
        id=[x.db_id for x in buttons if x.hovered]
        match intent:
            case Intent.SELECT:
                for button in buttons:    
                    if(button.hovered):
                        button.dispatch('on_press')
                        Clock.unschedule(self.check_joystick_events)    
            case Intent.UP:
                self.change_button_selection(id[0]+1)
            case Intent.RIGHT:
                self.change_button_selection(id[0]+1)
            case Intent.LEFT:
                self.change_button_selection(id[0]-1)
            case Intent.DOWN:
                self.change_button_selection(id[0]-1)
            case _:
                pass
        
    def change_button_selection(self, id: int):
        """Changes the button selection based on the id provided. Assumes type is SelectableButton"""
        buttons = [x for x in self.main_layout.children if isinstance(x, SelectableButton)==True]
        ids = [x.db_id for x in buttons]
        #clamping id's
        if(id > max(ids)):
            id=max(ids)
        if(id < min(ids)):
            id=min(ids)
            
        for button in buttons:
            if button.db_id==id:
                button.hovered=True
            else:
                button.hovered=False
            
        