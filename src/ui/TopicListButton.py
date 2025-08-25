from ui.SelectableButton import SelectableButton
from ui.HoverableButton import HoverableButton
from kivy.properties import ObjectProperty, NumericProperty


class AppSelectableButton(SelectableButton):
    topic_id = NumericProperty(None)
    on_choose = ObjectProperty(None)    # callback injected via rv.data
    data_index = NumericProperty(None)  # indexing used for scrolling
    
    def refresh_view_attrs(self, rv, index, data):
        self.data_index = index
        return super().refresh_view_attrs(rv, self.data_index, data)
        

    def on_press(self):
        # Keep the view "dumb": just signal upward
        if callable(self.on_choose):
            self.on_choose(self.topic_id)
            
            
    def __repr__(self):
        return f"{self.data_index}: {super().__repr__()}"