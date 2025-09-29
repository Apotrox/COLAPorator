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

from ui.HoverableButton import HoverableButton
from data.Guest import Guest
from services.GuestService import GuestService
from hardware.JoystickManager import Joystick, Intent

class GuestBookScreen(Screen):
    def __init__(self, gs:GuestService, js: Joystick, **kw):
        super().__init__(**kw)
        self.gs=gs
        self.js=js
        
        main_layout = FloatLayout()
        
        #input fields:
        # name, institution, role, purpose of visit
        
                # Set background
        with main_layout.canvas.before:
            Color(rgba=(0.95, 0.95, 0.95, 1))
            self.bg_rect = Rectangle(pos=main_layout.pos, size=main_layout.size)
        
        # Update background when layout changes
        main_layout.bind(pos=self.update_bg, size=self.update_bg)
        
        form_layout= BoxLayout(orientation="vertical", size_hint=(0.8,0.8), pos_hint={"x":0.05,"top":0.98})
        
        self.name_input=TextInput(hint_text="Name", font_size="20sp", size_hint=(0.6,1))
        self.inst_input=TextInput(hint_text="Institution", font_size="20sp", size_hint=(0.6,1))
        self.role_input=TextInput(hint_text="Role", font_size="20sp", size_hint=(0.6,1))
        self.rating_slider=Slider(min=0, 
                                  max=5, 
                                  value=0, 
                                  orientation="horizontal", 
                                  value_track=True, 
                                  value_track_color=(1,0,0,1),
                                  step=1, 
                                  size_hint=(0.6,1))
        
        name=Label(text="Name:", color=(0,0,0,1), font_size="30sp", halign="left")
        name.bind(size=lambda l, _: setattr(l, 'text_size', (l.width, None))) 
        #for some reason i have to set the text size like this to have the labels align themselves properly
        
        inst= Label(text="Institution:", color=(0,0,0,1), font_size="30sp", halign="left")
        inst.bind(size=lambda l, _: setattr(l, 'text_size', (l.width, None)))
        
        role= Label(text="Role:", color=(0,0,0,1), font_size="30sp", halign="left")
        role.bind(size=lambda l, _: setattr(l, 'text_size', (l.width, None)))
        
        pov=Label(text="Rating:", color=(0,0,0,1), font_size="30sp", halign="left")
        pov.bind(size=lambda l, _: setattr(l, 'text_size', (l.width, None)))

        
        form_layout.add_widget(name)
        form_layout.add_widget(self.name_input)
        
        form_layout.add_widget(inst)
        form_layout.add_widget(self.inst_input)
        
        form_layout.add_widget(role)
        form_layout.add_widget(self.role_input)
        
        form_layout.add_widget(pov)
        form_layout.add_widget(self.rating_slider)
        
        main_layout.add_widget(form_layout)
        
        disclaimer = Label(text="Participation in this guestbook is voluntary. \
                            Your responses will be stored in a secure database and may be reviewed and processed by the COLAPS group for analysis purposes.\
                            By entering your data, you consent to the storage and processing of your responses in accordance with these terms.",
                            color=(0,0,0,1),
                            font_size=sp(15),
                            pos_hint={"right":1.35,"top": 1.2})
        
        disclaimer.bind(size=lambda l, _: setattr(l, 'text_size', (l.width*0.2, None)))        
        
        save_button = HoverableButton(text="Confirm", size_hint=(0.2, 0.1), pos_hint={"x":0.75, "y":0.03})
        save_button.bind(on_press=self.confirm)
        main_layout.add_widget(save_button)
        
        self.back_button = HoverableButton(text="Back", size_hint=(0.2, 0.1), pos_hint={"x":0.05, "y":0.03})
        self.back_button.hovered=True
        self.back_button.bind(on_press=self.go_back)
        main_layout.add_widget(self.back_button)
        
        
        main_layout.add_widget(disclaimer)  
        self.add_widget(main_layout)
    
    
    def update_bg(self, instance, _):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        
    def on_pre_enter(self):
        self.name_input.text=""
        self.role_input.text=""
        self.inst_input.text=""
        self.rating_slider.value=0


    def confirm(self, *_):
        name=self.name_input.text
        role=self.role_input.text
        inst=self.inst_input.text
        rating=self.rating_slider.value
        
        if((name or role or inst or rating)):
            self.gs.add_entry(Guest(None,name,inst, role,rating,None))

        
        popup=Popup(title="Thank You!",
                    content=Label(text="Thank You for your participation!", font_size="30sp"), size_hint=(None,None), size=(500,150), auto_dismiss=True)
        popup.bind(on_dismiss=self.dismiss)
        Clock.schedule_once(popup.dismiss, 3)
        popup.open()
    
    def dismiss(self, *_):
        self.manager.transition=FadeTransition()
        self.manager.current="startup"
    
    def go_back(self, *_):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'topic_list'
        
    def on_enter(self):
        if self.js:
            Clock.schedule_interval(self.check_joystick_events, 0.1)    
    
    
    def check_joystick_events(self, *_):
        if self.manager.current=='guest':
            intent= self.js.get() #don't need to be here if it isnt the active screen
            if intent:
                self.handle_joystick_intents(intent)
    
    def handle_joystick_intents(self, intent:Intent):
        match intent:
            case Intent.SELECT:
                if(self.back_button.hovered):
                    Clock.unschedule(self.check_joystick_events) 
                    self.go_back()    
            case _:
                return
        
        
            
        