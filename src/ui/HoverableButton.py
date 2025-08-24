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
        self.bind(width=self.on_width_change)  # Only bind to width changes
        self.bind(text=self.update_height)
        
        # Track if we're currently updating to prevent loops
        self._updating_height = False

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return
        pos = args[1]
        self.hovered = self.collide_point(*self.to_widget(*pos))

    def on_width_change(self, instance, width):
        # Only update text_size when width changes, not height
        if width > 0:
            self.text_size = (width - 40, None)  # 40px padding
            self.update_height()

    def update_height(self, *_):
        # Prevent recursive calls
        if self._updating_height or not self.text or self.width <= 0:
            return
            
        self._updating_height = True
        
        try:
            # Set text_size to enable wrapping
            if self.text_size[0] is None:
                self.text_size = (self.width - 20, None)
            
            # Calculate required height based on text
            self.texture_update()
            if self.texture:
                # Add padding (20px top/bottom + some extra for comfort)
                required_height = self.texture.height + 30
                min_height = dp(50)  # Minimum button height
                new_height = max(required_height, min_height)
                
                # Only update if height actually changed to avoid unnecessary updates
                if abs(self.height - new_height) > 1:
                    self.height = new_height
        finally:
            self._updating_height = False

    def on_hovered(self, instance, hovered):
        # Update canvas when hovered state changes
        self.canvas.before.clear()
        with self.canvas.before:
            Color(rgba=(0.8, 0.87, 1, 1) if hovered else (1, 1, 1, 1))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[12])

    def on_pos(self, *args):
        # Update canvas when position changes
        self.on_hovered(self, self.hovered)
        
    def on_size(self, *args):
        # Update canvas when size changes, but don't trigger height updates
        self.on_hovered(self, self.hovered)
        
    def __str__(self):
        return f"{self.text}"
    
    def __repr__(self):
        return f"{self.text}"