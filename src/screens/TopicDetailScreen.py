from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.properties import NumericProperty


from hardware.JoystickManager import Joystick, Intent
from ui.HoverableButton import HoverableButton


from kivy.clock import Clock

class TopicDetailScreen(Screen):
    db_id = NumericProperty(None) #to be used for tracking/usage history
    
    def __init__(self, js:Joystick, **kwargs):
        super().__init__(**kwargs)

        self.js=js

        # Main container
        main_layout = BoxLayout(
            orientation='vertical',
            padding=[10, 10, 10, 10],
            spacing=10
        )
        
        # Set background
        with main_layout.canvas.before:
            Color(rgba=(0.95, 0.95, 0.95, 1))
            self.bg_rect = Rectangle(pos=main_layout.pos, size=main_layout.size)
        
        # Update background when layout changes
        main_layout.bind(pos=self.update_bg, size=self.update_bg)
        
        # Content label
        self.content_label = Label(
            text='Test',
            font_size=18,
            color=(0.1, 0.1, 0.1, 1),
            size_hint_y=0.9,
            text_size=(Window.width -60, None),
            halign='left',
            valign='top'
        )
        
        # Back button
        back_button = HoverableButton(
            text="Back",
            size_hint_y=0.1
        )
        back_button.bind(on_press=self.go_back)
        
        if(self.js):
            back_button.hovered=True #becomes unset if a mouse is present but oh well
        
        # Add widgets to main layout
        main_layout.add_widget(self.content_label)
        main_layout.add_widget(back_button)
        
        self.add_widget(main_layout)

    def update_bg(self, instance, _):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def display_topic(self, text):
        self.content_label.text = text
        if self.js:
            Clock.schedule_interval(self.check_joystick_events, 0.1)

    def go_back(self, *_):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'topic_list'
        
    def check_joystick_events(self, *_):
        if self.manager.current=='topic_detail':
            intent= self.js.get() #don't need to be here if it isnt the active screen
            if intent:
                self.handle_joystick_intents(intent)
    
    def handle_joystick_intents(self, intent:Intent):
        if intent== Intent.SELECT:
            Clock.unschedule(self.check_joystick_events)
            self.go_back()