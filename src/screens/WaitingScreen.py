
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from kivy.graphics import Color, Rectangle



class WaitingScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        
        self.startup_label = Label(
            text='Please Wait...',
            font_size=26,
            color=(0.2, 0.2, 0.2, 1)
        )
        
        with self.canvas.before:
            Color(rgba=(0.95, 0.95, 0.95, 1))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
                # Update background when layout changes
        self.bind(pos=self.update_bg, size=self.update_bg)
        
        self.add_widget(self.startup_label)
        
        
    def update_bg(self, instance, _):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size