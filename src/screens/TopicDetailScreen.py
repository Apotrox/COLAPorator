from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.properties import NumericProperty
from kivy.graphics.texture import Texture

from hardware.JoystickManager import Joystick, Intent
from ui.HoverableButton import HoverableButton

import qrcode
import PIL
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image as kiImage
from io import BytesIO

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
            size_hint_y=0.7,
            text_size=(Window.width -60, None),
            halign='left',
            valign='top'
        )
        
        #making the qr code image transparent to have it not visible if no qr code is available
        # Create the texture first with RGBA format (includes alpha channel)
        self.default_texture = Texture.create(size=(100, 100), colorfmt='rgba')

        # Fill with transparent pixels (RGBA: 0, 0, 0, 0)
        # Create a buffer of transparent pixels
        transparent_pixels = b'\x00\x00\x00\x00' * (100 * 100)
        self.default_texture.blit_buffer(transparent_pixels, colorfmt='rgba', bufferfmt='ubyte')
        
        self.image=kiImage(size_hint=(0.3,0.3), pos_hint={"center_x":0.5}, texture=self.default_texture)
        
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
        main_layout.add_widget(self.image)
        main_layout.add_widget(back_button)
        
        self.add_widget(main_layout)

    def update_bg(self, instance, _):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def display_topic(self, text, source):
        self.content_label.text = text
        
        #if there is no source, dont generate the qr code
        if(source):
            
            qr = qrcode.QRCode()
            
            qr.add_data(data=source)
            qr.make()
            img = qr.make_image(back_color="transparent")
            data = BytesIO()
            img.save(data, format="png")
            data.seek(0)
            im=CoreImage(BytesIO(data.read()), ext="png")
            self.image.texture=im.texture
        else:
            self.image.texture=self.default_texture       
        
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