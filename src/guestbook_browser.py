from kivy.app import App
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.behaviors import FocusBehavior
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors.compoundselection import CompoundSelectionBehavior
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.stacklayout import StackLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup

import time

from database.database_manager import Manager
from services.GuestService import GuestService

from ui.SelectableButton import SelectableButton 
from ui.LabeledCheckbox import LabeledCheckbox


class CMSelectableButton(SelectableButton):
    #overwriting with custom press behaviour
    def on_press(self):
        cm = self.get_root_window().children[0]
        if hasattr(cm, 'update_editing_block_fields'):
            cm.update_editing_block_fields(self.db_id)

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

        self.update_content(content='start')

        
        self.add_widget(recycle_layout)
        self.viewclass='CMSelectableButton'

    def update_content(self, content):
        """content has to be 'topics' or 'categories'"""
        
        if content == 'topics':
            topics = self.topic_service.list_all()
            self.data=[{'text' : f"{topic.id} {topic.title}", 'db_id': topic.id} for topic in topics]
        elif content == 'categories':
            categories = self.category_service.list()
            self.data=[{'text' : f"{cat.id} {cat.title}", 'db_id': cat.id} for cat in categories]
        elif content == 'test':
            self.data=[{'text': f"Item {i} 123456789", 'db_id': i+100} for i in range(10)] #something longer to test line wrapping
        else:
            self.data=[{'text': "Please select data type to load", 'db_id': 0}]
        self.refresh_from_data()
        
    def scroll_to_end(self):
        if self.data:
            self.scroll_y=0 #easiest way to scroll down

class ConfirmPopup(Popup):
    def __init__(self,msg, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        
        popup_layout= BoxLayout(orientation="vertical")
        button_layout = BoxLayout(orientation="horizontal")

        dismiss_button = Button(text="No")

        confirm_button = Button(text="Yes")
        confirm_button.bind(on_press=self._confirm)
        if(isinstance(msg, str)):
            label = Label(text=msg)
        else:
            label = Label(text="")

        button_layout.add_widget(dismiss_button)
        button_layout.add_widget(confirm_button)
        popup_layout.add_widget(label)
        popup_layout.add_widget(button_layout)

        self.title='Confirmation'
        self.content=popup_layout
        self.size_hint=(None,None) 
        self.size=(400,200)
        self.auto_dismiss=False
        dismiss_button.bind(on_press=self._dismiss)

    def _confirm(self, _):
        if self.callback:
            self.callback(True)
        self.dismiss()
    
    def _dismiss(self, _):
        if self.callback:
            self.callback(False)
        self.dismiss()
        

class TextBlock(GridLayout):
    """Contains all Input field necessary to edit content. Saves content type and selected ID in properties"""
    db_id = NumericProperty(0) #add the id as a property to make updates possible
    
    def __init__(self, gs: GuestService, **kwargs):
        super().__init__(**kwargs)
        self.cols=2
        self.guest_service=gs          
        
    def load_item_content(self, item_id):
        """Loads content for given item_id and type"""
        self.db_id=item_id
                                                   
        guest = self.guest_service.get_by_id(item_id)
        
        _,name,inst,role,pov,date = guest
        
        guest = {"Name": name,
                 "Institution": inst,
                 "Role": role,
                 "Purpose of Visit": pov,
                 "Date": date}
        
        for key in guest.keys:
            self.add_widget(Label(text=key,font_size="20sp"))
            self.add_widget(Label(text=guest.get(key), font_size="20sp"))
        
            


#--Main window stuff

class Guestbook(FloatLayout):
        # use this as central controller/interface for different window parts
        def __init__(self, gs:GuestService, **kwargs):
            super().__init__(**kwargs)
            
            self.guest_service=gs

            self.list_selector = ListSelector(size_hint=(0.2, 0.8), pos_hint={'x': 0.01, 'y': 0.05}, ts=self.topic_service, cs=self.category_service)
            self.add_widget(self.list_selector)
            
            #EditingBlock with input fields
            self.text_block = TextBlock(size_hint=(0.74, 0.83), pos_hint={'x': 0.25, 'y': 0.02}, ts=self.topic_service, cs=self.category_service)
            #editing_block.bind(pos=self.debug_bg_update, size=self.debug_bg_update)
            self.add_widget(self.text_block)

        
        def on_remove_item(self, *_):
            
            id = self.text_block.db_id
            self.guest_service.remove_entry(id)
            
            self.list_selector.update_content()
            
            
        def update_editing_block_fields(self, db_id):
            """"Called when a button on the list is pressed"""
            if self.current_data_type:
                self.editing_block.load_item_content(db_id, self.current_data_type)

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