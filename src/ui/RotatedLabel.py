from kivy.uix.widget import Widget
from kivy.graphics import PushMatrix, PopMatrix, Rotate
from kivy.uix.label import Label

class RotatedLabel(Widget):
    def __init__(self, text:str, angle:int, color=(0.5,0.5,0.5,1), font_size="15sp", **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas:
            PushMatrix()
            self.rotation = Rotate(angle=angle, origin=self.center)
            self.label = Label(
                text=text,
                font_size=font_size,
                color=color,
                font_name="./DejaVuSans.ttf",
                pos=self.pos,
                size=self.size
            )
            PopMatrix()
            
        # Update rotation origin and label position when widget moves/resizes
        self.bind(pos=self.update_graphics, size=self.update_graphics)
    
    def update_graphics(self, *args):
        self.rotation.origin = self.center
        self.label.pos = self.pos
        self.label.size = self.size