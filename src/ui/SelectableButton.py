from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import StringProperty, NumericProperty
from ui.HoverableButton import HoverableButton

class SelectableButton(HoverableButton, FocusBehavior, RecycleDataViewBehavior):
    text = StringProperty()
    db_id = NumericProperty(0) #give the button an id to store the DB id's in

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.size_hint_x = 0.95
        self.pos_hint = {"center_x": 0.5}

    def refresh_view_attrs(self, rv, index, data):
        super().refresh_view_attrs(rv, index, data)
        self.db_id = data.get('db_id', 0) # set db_id from data
        
    
    def __str__(self):
        return f"({self.db_id}: {super().__str__()})"
    
    def __repr__(self):
        return f"({self.db_id}: {super().__repr__()})\n"