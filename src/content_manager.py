from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.behaviors import FocusBehavior
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.behaviors.compoundselection import CompoundSelectionBehavior
from kivy.uix.label import Label

from backend.database_manager import Manager

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

        
class SelectableButton(HoverableButton, FocusBehavior, RecycleDataViewBehavior, Button):
    text = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.size_hint_x = 0.95
        self.pos_hint = {"center_x": 0.5}

    def on_press(self):
        pass


class ListSelector(RecycleView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.scroll_type=['bars', 'content']

        recycle_layout = RecycleBoxLayout(
            default_size=(None, None),  # Let buttons determine their own height
            default_size_hint=(1, None),
            size_hint=(1, None), #NOTE
            orientation='vertical',
            spacing=dp(10),
            padding=[5, 0, 10, 0]
        )
        recycle_layout.bind(minimum_height=recycle_layout.setter('height'))

        self.update_content(content='topics')

        
        self.add_widget(recycle_layout)
        self.viewclass='SelectableButton'

    def update_content(self, content):
        """content has to be 'topics' or 'categories'"""

        db = App.get_running_app().db
        if content == 'topics':
            topics = db.execute("SELECT id, title FROM topics").fetchall()
            self.data=[{'text' : f"{id} {title}"} for id, title in sorted(topics, key = lambda x: x[0])]
        elif content == 'categories':
            categories = db.execute("Select id, title FROM slices").fetchall()
            self.data=[{'text' : f"{id} {title}"} for id, title in sorted(categories, key = lambda x: x[0])]
        elif content == 'test':
            self.data=[{'text': f"Item {i} 123456789"} for i in range(10)]
        else:
            self.data=[{'text': "No data found"}]
        self.refresh_from_data()

class MenuBar(GridLayout, FocusBehavior, CompoundSelectionBehavior):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.cols=3
            self.rows=1
            self.row_force_default=True
            self.row_default_height=50
            self.padding=[10,0,10,0]

            empty_space_L = Label(text="", size_hint=(0.5,None))

            categories_button = Button(text="Categories", 
                                       color=(0,0,0,1), 
                                       background_color=(0,0,0,0), 
                                       size_hint=(0.5, 0.8))
            
            
            with categories_button.canvas.before:
                Color(rgba=(0, 0, 0, 1))
                self.cat_rect = Line(width=1)
            
            categories_button.bind(pos=self.update_cat_border, size=self.update_cat_border)

            topics_button = Button(text="Topics", 
                                   color=(0,0,0,1),
                                   background_color=(0,0,0,0), 
                                   size_hint=(0.5,0.8))
            
            with topics_button.canvas.before:
                Color(rgba=(0, 0, 0, 1))
                self.top_rect = Line(width=1)

            topics_button.bind(pos=self.update_top_border, size=self.update_top_border)

            self.add_widget(empty_space_L)
            self.add_widget(categories_button)
            self.add_widget(topics_button)


        def add_widget(self, widget, *args, **kwargs):
            """ Override the adding of widgets so we can bind and catch their
            *on_touch_down* events. """
            widget.bind(on_touch_down=self.button_touch_down)
            return super(MenuBar, self).add_widget(widget, *args, **kwargs)

        def button_touch_down(self, button, touch):
            """ Use collision detection to select buttons when the touch occurs
            within their area. """
            if button.collide_point(*touch.pos):
                self.select_with_touch(button, touch)

        def select_node(self, node):
            node.background_color = (200/255, 255/255, 255/255, 1)
            return super(MenuBar, self).select_node(node)

        def deselect_node(self, node):
            node.background_color = (0, 0, 0, 0)
            super(MenuBar, self).deselect_node(node)
        
        def on_selected_nodes(self, _, nodes):
            if not nodes: #this method, for some reason first gets an empty list and then a list with the element
                return    #gotta skip the empty list
                          #node objects are just the original objects, here the buttons, whose attributes can be accessed normally 
            
            #this assumes that MenuBar will *always* be added to ContentManager as a child
            if(nodes[0].text =="Categories"):
                self.parent.on_menu_selection(selection="categories")
            elif(nodes[0].text == "Topics"):
                self.parent.on_menu_selection(selection="topics")
            else:
                pass

        def update_cat_border(self, instance, _):
            self.cat_rect.rectangle = (*instance.pos, *instance.size)

        def update_top_border(self, instance, _):
            self.top_rect.rectangle = (*instance.pos, *instance.size)

class ContentManager(FloatLayout):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.orientation='horizontal'            

            self.list_selector = ListSelector(size_hint=(0.3, 0.9), pos_hint={'x': 0.01, 'y': 0.05})
            self.add_widget(self.list_selector)

            #menu bar
            menu_bar = MenuBar(size_hint=(1, None), pos_hint={'y':0.82})
            self.add_widget(menu_bar)
        
        def on_menu_selection(self, selection):
            if selection =="categories":
                self.list_selector.update_content(content='categories')
            elif selection == "topics":
                self.list_selector.update_content(content='topics')
            


class ContentApp(App):
    def build(self):

        Window.clearcolor=(0.95, 0.95, 0.95, 1) #global background color

        self.db = Manager()
        self.db.ensure_database_availability()

        window = ContentManager()

        return window



if __name__ == '__main__':
    ContentApp().run()