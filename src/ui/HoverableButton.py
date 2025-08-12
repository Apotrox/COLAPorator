from kivy.uix.button import Button
from kivy.properties import BooleanProperty
from kivy.core.window import Window
from kivy.graphics import RoundedRectangle, Color
from kivy.metrics import dp

class HoverableButton(Button):
    hovered = BooleanProperty(False)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)
        
        # Set button properties from KV
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.color = (0.1, 0.1, 0.1, 1)
        
        # Enable text wrapping and auto-sizing
        self.text_size = (None, None)  # Will be set based on button width
        self.halign = "center"
        self.valign = "middle"
        self.bind(size=self.on_size_change) #NOTE
        self.bind(text=self.update_height)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return
        pos = args[1]
        self.hovered = self.collide_point(*self.to_widget(*pos))

    def on_size_change(self, *args):
        # Update text_size when button width changes
        if self.size[0] > 0:
            self.text_size = (self.size[0] - 40, None)  # 40px padding
        self.update_height()
        self.on_hovered(self, self.hovered)

    def update_height(self, *_):
        if not self.text or self.size[0] <= 0:
            return
            
        # Set text_size to enable wrapping
        if self.text_size[0] is None:
            self.text_size = (self.size[0] - 20, None)
        
        # Calculate required height based on text
        self.texture_update()
        if self.texture:
            # Add padding (20px top/bottom + some extra for comfort)
            required_height = self.texture.height + 30
            min_height = dp(50)  # Minimum button height
            new_height = max(required_height, min_height)
            
            # Only update if height actually changed to avoid infinite loops
            if abs(self.height - new_height) > 1:
                self.height = new_height

    def on_hovered(self, instance, hovered):
        # Update canvas when hovered state changes
        self.canvas.before.clear()
        with self.canvas.before:
            Color(rgba=(0.8, 0.87, 1, 1) if hovered else (1, 1, 1, 1))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[12])

    def on_pos(self, *args):
        # Update canvas when position changes
        self.on_hovered(self, self.hovered)