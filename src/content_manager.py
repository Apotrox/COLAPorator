from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.behaviors import FocusBehavior
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.behaviors.compoundselection import CompoundSelectionBehavior
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.stacklayout import StackLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView

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
    db_id = NumericProperty(0) #give the button an id to store the DB id's in

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.size_hint_x = 0.95
        self.pos_hint = {"center_x": 0.5}

    def refresh_view_attrs(self, rv, index, data):
        super().refresh_view_attrs(rv, index, data)
        self.db_id = data.get('db_id', 0) # set db_id from data

    def on_press(self):
        cm = self.get_root_window().children[0]
        if hasattr(cm, 'update_editing_block_fields'):
            cm.update_editing_block_fields(self.db_id)

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
        


class ListSelector(RecycleView):
    """"The selection list used to select different topic/category items"""
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

        self.update_content(content='start')

        
        self.add_widget(recycle_layout)
        self.viewclass='SelectableButton'

    def update_content(self, content):
        """content has to be 'topics' or 'categories'"""

        db = App.get_running_app().db
        if content == 'topics':
            topics = db.execute("SELECT id, title FROM topics").fetchall()
            self.data=[{'text' : f"{id} {title}", 'db_id': id} for id, title in sorted(topics, key = lambda x: x[0])]
        elif content == 'categories':
            categories = db.execute("Select id, title FROM slices").fetchall()
            self.data=[{'text' : f"{id} {title}", 'db_id': id} for id, title in sorted(categories, key = lambda x: x[0])]
        elif content == 'test':
            self.data=[{'text': f"Item {i} 123456789", 'db_id': i+100} for i in range(10)] #something longer to test line wrapping
        else:
            self.data=[{'text': "Please select data type to load", 'db_id': 0}]
        self.refresh_from_data()

class MenuBar(GridLayout, FocusBehavior, CompoundSelectionBehavior):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.cols=4
            self.rows=1
            self.row_force_default=True
            self.row_default_height=50
            self.padding=[10,0,10,0]
            
            add_button = Button(text="Add", 
                                       color=(1,1,1,1), 
                                       background_color=(200/255, 255/255, 255/255, 1), 
                                       size_hint=(0.2, 0.8))
            add_button.bind(on_press=self.add_items)
            
            
            remove_button = Button(text="Remove", 
                                       color=(1,1,1,1), 
                                       background_color=(200/255, 255/255, 255/255, 1), 
                                       size_hint=(0.2, 0.8))
            remove_button.bind(on_press=self.remove_items)
            

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
            
            
            
            self.add_widget(add_button)
            self.add_widget(remove_button)
            self.add_widget(categories_button)
            self.add_widget(topics_button)

        def add_widget(self, widget, *args, **kwargs):
            """ Override the adding of widgets so we can bind and catch their
            *on_touch_down* events. """
            widget.bind(on_touch_down=self.button_touch_down)
            return super(MenuBar, self).add_widget(widget, *args, **kwargs)
        
        
        # the following are all kivy events btw
        def button_touch_down(self, button, touch):
            """ Use collision detection to select buttons when the touch occurs
            within their area. """
            if button.collide_point(*touch.pos):
                self.select_with_touch(button, touch)

        def select_node(self, node):
            node.background_color = (200/255, 255/255, 255/255, 1)
            node.color=(1,1,1,1)
            return super(MenuBar, self).select_node(node)

        def deselect_node(self, node):
            node.background_color = (0, 0, 0, 0)
            node.color=(0,0,0,1)
            super(MenuBar, self).deselect_node(node)
        
        def on_selected_nodes(self, _, nodes):
            #filtering out the nodes that are not supposed to be toggleable (add/remove)
            for node in nodes:
                if not (node.text == "Categories" or node.text == "Topics"):
                    super(MenuBar,self).deselect_node(node) # can't use my own deselect method here due to the color change...
            
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
            
            
        def add_items(self, _):
            self.parent.on_add_item()
        
        def remove_items(self,_):
            self.parent.on_remove_item()
            

class EditingBlock(FloatLayout):
    db_id = NumericProperty(0) #add the id as a property to make updates possible
    content_type = StringProperty() #for table selection
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.db = App.get_running_app().db
        
        #input for title box
        self.title_input = TextInput(text="",font_size="20sp", size_hint=(1, 0.08), pos_hint={'x': 0, 'y': 0.92})
        self.add_widget(self.title_input)
        
        self.desc_input = TextInput(text="", font_size="20sp", size_hint=(0.7, 0.7), pos_hint={'x':0, 'y': 0.2})
        self.add_widget(self.desc_input)
        
        #category list was too large, required a scrollview
        scroll_view = ScrollView(
            size_hint=(0.7, 0.15),
            pos_hint={'x': 0.0, 'y': 0.02},
            do_scroll_x=False  # only scroll vertically
        )

        self.category_box = StackLayout(
            orientation='lr-tb',
            size_hint_y=None,  # required for scrolling
            spacing=dp(5),
            padding=dp(5)
        )
        self.category_box.bind(minimum_height=self.category_box.setter('height'))
        
        scroll_view.add_widget(self.category_box)
        self.add_widget(scroll_view)
        
        save_button=Button(text="save", font_size="16sp", color=(0,0,0,1),
                           size_hint=(0.2,0.1),
                           pos_hint={'x': 0.78, 'y':0.02})
        self.add_widget(save_button)
        
        save_button.bind(on_press=self.save_changes)
        
    def save_changes(self, _):
        
        title = self.title_input.text.replace("'", "''") #escape single quotes to contain all the text 
        desc = self.desc_input.text.replace("'", "''")
        category_selection=[]
        
        for checkbox in self.category_box.children:
            if checkbox.checked:
                category_selection.append((self.db_id, checkbox.category_id))
        
        if self.content_type=="categories":
            self.db.execute(f"UPDATE slices SET title='{title}' WHERE id={self.db_id}")
        elif self.content_type=="topics":
            self.db.execute(f"UPDATE topics SET title='{title}', description='{desc}' WHERE id={self.db_id}")
            self.db.execute(f"DELETE FROM topicAssignment WHERE topic_id={self.db_id}") #just remove all entries related to the topic
            self.db.execute_many("INSERT INTO topicAssignment (topic_id, slice_id) VALUES (?, ?)", category_selection)
              
        #self.db.commit_changes()


    
    def load_item_content(self, item_id, type):
        
        self.category_box.clear_widgets()
        
        self.db_id=item_id
        self.content_type=type
                                        
        if type == "topics":
           
            result = self.db.execute(f"SELECT title, description FROM topics where id = {item_id}").fetchall() #getting topic data
            categories = self.db.execute("SELECT ID, title from slices").fetchall() #getting all categories
            topic_in_category = [x[0] for x in (self.db.execute(f"SELECT slices.id FROM slices \
                                            INNER JOIN topicAssignment ON slices.ID = topicAssignment.slice_id \
                                            INNER JOIN topics on topicAssignment.topic_id = topics.id WHERE topics.id = {item_id}").fetchall())]
                                            #then get all categories the selected topic already belongs to (also returns tuples)
            
            title, desc = result[0]
            self.title_input.text=title
            self.desc_input.text=desc
            
            for (id, category_title) in categories:
                self.category_box.add_widget(LabeledCheckbox(text=category_title, category_id=id, checked=id in topic_in_category))
            
        
        elif type == "categories":
            res = self.db.execute(f"SELECT title from slices where id = {item_id}").fetchall() #ducking returns (title,). yes, a tuple
            title = res[0][0]
            self.title_input.text=title
            self.desc_input.text=""
            


#--Main window stuff

class ContentManager(FloatLayout):
        # use this as central controller/interface for different window parts
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.orientation='horizontal'
            self.current_data_type = None #tracking which type is currently active (topics/cats)                meow
                        

            self.list_selector = ListSelector(size_hint=(0.2, 0.8), pos_hint={'x': 0.01, 'y': 0.05})
            self.add_widget(self.list_selector)

            #menu bar
            menu_bar = MenuBar(size_hint=(1, None), pos_hint={'y':0.82})
            self.add_widget(menu_bar)
            
            #EditingBlock with input fields
            self.editing_block = EditingBlock(size_hint=(0.74, 0.83), pos_hint={'x': 0.25, 'y': 0.02})
            #editing_block.bind(pos=self.debug_bg_update, size=self.debug_bg_update)
            self.add_widget(self.editing_block)

        def on_add_item(self, *_):
            if self.current_data_type == "categories": #skip categories as we won't be handling those
                return
            
            db = App.get_running_app().db
            
            db.execute(f"INSERT INTO topics (title, description) VALUES ('New Topic', 'Placeholder description')")
            #db.commit_changes()
        
        def on_remove_item(self, *_):
            if self.current_data_type == "categories":
                return
            
            db = App.get_running_app().db
            
            id = self.editing_block.db_id
            db.execute(f"DELETE FROM topics WHERE id = {id}")
            
            #db.commit_changes()
            
            
        def update_editing_block_fields(self, db_id):
            """"Called when a button on the list is pressed"""
            if self.current_data_type:
                self.editing_block.load_item_content(db_id, self.current_data_type)
        
        def on_menu_selection(self, selection):
            if selection =="categories":
                self.current_data_type="categories"
                self.list_selector.update_content(content='categories')
            elif selection == "topics":
                self.current_data_type ="topics"
                self.list_selector.update_content(content='topics')
        
        def debug_bg_update(self, instance, *_):
            with instance.canvas.before:
                Color(rgba=(0.2,0.2,0.2,0.5))
                Rectangle(pos=instance.pos, size=instance.size)


class ContentManagerApp(App):
    def build(self):

        Window.clearcolor=(0.95, 0.95, 0.95, 1) #global background color

        self.db = Manager()
        self.db.ensure_database_availability()

        window = ContentManager()

        return window



if __name__ == '__main__':
    ContentManagerApp().run()