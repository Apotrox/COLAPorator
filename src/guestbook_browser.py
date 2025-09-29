from kivy.app import App
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup

import time

from database.database_manager import Manager
from services.GuestService import GuestService

from ui.SelectableButton import SelectableButton 


class CMSelectableButton(SelectableButton):
    #overwriting with custom press behaviour
    def on_press(self):
        cm = self.get_root_window().children[0]
        if hasattr(cm, 'update_text_block_fields'):
            cm.update_text_block_fields(self.db_id)

class ListSelector(RecycleView):
    """"The selection list used to select different topic/category items"""
    def __init__(self, gs: GuestService, **kwargs):
        super().__init__(**kwargs)
        self.guest_service =gs

        self.scroll_type=['bars', 'content']
        self.bar_width=7

        recycle_layout = RecycleBoxLayout(
            default_size=(None, None),  # Let buttons determine their own height
            default_size_hint=(1, None),
            size_hint=(1, None), #NOTE
            orientation='vertical',
            spacing=dp(10),
            padding=[5, 0, 10, 0]
        )
        recycle_layout.bind(minimum_height=recycle_layout.setter('height'))
        
        self.add_widget(recycle_layout)
        self.viewclass='CMSelectableButton'
        
        guests = self.guest_service.list()
        self.data=[{'text' : f"{guest.id} {guest.name}", 'db_id': guest.id} for guest in guests]
        self.refresh_from_data()
        

class TextBlock(GridLayout):
    """Contains all Input field necessary to edit content. Saves content type and selected ID in properties"""
    
    def __init__(self, gs: GuestService, **kwargs):
        super().__init__(**kwargs)
        
        self.cols=2
        self.spacing=dp(15)
        self.padding=dp(10)
        
        
        self.guest_service=gs
        
        with self.canvas.before:
            Color(rgba=(0.8, 0.8, 0.8, 1))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_bg, size=self.update_bg)
        
        self.load_item_content(-1)
                 
        
    def load_item_content(self, item_id):
        """Loads content for given item_id and type"""
        self.clear_widgets()
        
        if(item_id>=0):                                           
            guest = self.guest_service.get_for_id(item_id)
        else:
            guest = ("","","","","","") #just for init
            
            
        _,name,inst,role,pov,date = guest
        
        guest = {"Name:": name,
                 "Institution:": inst,
                 "Role:": role,
                 "Purpose of Visit:": pov,
                 "Date:": date}
        
        for key in guest.keys():
            # Left label (key) - right aligned
            left_label = Label(text=key, font_size="20sp", color=(0,0,0,1), halign='right', valign='middle')
            left_label.bind(size=lambda label, size: setattr(label, 'text_size', size))
            self.add_widget(left_label)
            
            # Right label (value) - left aligned
            right_label = Label(text=guest.get(key), font_size="20sp", color=(0,0,0,1), halign='left', valign='middle')
            right_label.bind(size=lambda label, size: setattr(label, 'text_size', size))
            self.add_widget(right_label)
            
    def update_bg(self, instance, _):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size  
            


#--Main window stuff

class Guestbook(BoxLayout):
        # use this as central controller/interface for different window parts
        def __init__(self, gs:GuestService, **kwargs):
            super().__init__(**kwargs)
            
            self.guest_service=gs
            self.orientation="horizontal"

            self.list_selector = ListSelector(size_hint=(0.4, 0.9), gs=self.guest_service)
            self.add_widget(self.list_selector)
            
            self.text_block = TextBlock(size_hint=(0.6, 0.9), gs=self.guest_service)
            self.add_widget(self.text_block)
                      
            
        def update_text_block_fields(self, db_id):
            """"Called when a button on the list is pressed"""
            self.text_block.load_item_content(db_id)

        
        
class GuestbookApp(App):
    def build(self):

        Window.clearcolor=(0.95, 0.95, 0.95, 1) #global background color

        db = Manager()
        db.ensure_database_availability()
        
        guest_service= GuestService(db)

        window = Guestbook(guest_service)

        return window



if __name__ == '__main__':
    GuestbookApp().run()