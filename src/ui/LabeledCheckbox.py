from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.metrics import dp
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label


class LabeledCheckbox(BoxLayout):
    text = StringProperty()
    category_id = NumericProperty(0)
    checked = BooleanProperty(False)
    
    def __init__(self, text, category_id, checked=False, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.height = dp(20)
        self.spacing = dp(5)
        
        self.text=text
        self.category_id = category_id
        self.checked = checked
        
        
        self.checkbox = CheckBox( size_hint=(None,None), size=(dp(20), dp(20)), active=checked, color=(0,0,0,1))
        self.checkbox.bind(active=self.toggle_active)
        self.label = Label(text=text, size_hint=(1,None), height=dp(20), text_size=(None,None), halign='left', valign='center', color=(0,0,0,1))
        
        self.label.bind(texture_size=self._update_size)
        self._update_size()

        self.add_widget(self.checkbox)
        self.add_widget(self.label)

    def _update_size(self, *_):
        self.label.size = self.label.texture_size
        self.width = self.checkbox.width + self.spacing + self.label.width
    
    def toggle_active(self, _, value):
        self.checked=value