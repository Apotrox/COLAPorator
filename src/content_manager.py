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
from kivy.uix.behaviors.compoundselection import CompoundSelectionBehavior
from kivy.uix.textinput import TextInput
from kivy.uix.stacklayout import StackLayout
from kivy.uix.scrollview import ScrollView

from database.database_manager import Manager
from categories.CategoryService import CategoryService
from topics.TopicService import TopicService

from ui.SelectableButton import SelectableButton 
from ui.LabeledCheckbox import LabeledCheckbox


class CMSelectableButton(SelectableButton):
    #overwriting with custom press behaviour
    def on_press(self):
        print("pressed!")
        cm = self.get_root_window().children[0]
        if hasattr(cm, 'update_editing_block_fields'):
            cm.update_editing_block_fields(self.db_id)

class ListSelector(RecycleView):
    """"The selection list used to select different topic/category items"""
    def __init__(self, ts: TopicService, cs: CategoryService, **kwargs):
        super().__init__(**kwargs)
        
        self.topic_service=ts
        self.category_service=cs

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




class TypeSelector(GridLayout, FocusBehavior, CompoundSelectionBehavior):
        """Selecting content type"""
        def __init__(self, ts: TopicService, cs: CategoryService, cm, **kwargs):
            super().__init__(**kwargs)
            
            self.topic_service=ts
            self.category_service=cs
            self.cm=cm

            self.cols=2
            self.rows=1
            self.row_force_default=True
            self.row_default_height=50
            self.padding=[10,0,10,0]
            
            

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
            

            self.add_widget(categories_button)
            self.add_widget(topics_button)

        def add_widget(self, widget, *args, **kwargs):
            """ Override the adding of widgets so we can bind and catch their
            *on_touch_down* events. """
            widget.bind(on_touch_down=self.button_touch_down)
            return super(TypeSelector, self).add_widget(widget, *args, **kwargs)
        
        
        def update_cat_border(self, instance, _):
            self.cat_rect.rectangle = (*instance.pos, *instance.size)

        def update_top_border(self, instance, _):
            self.top_rect.rectangle = (*instance.pos, *instance.size)
            


        # the following are all kivy events btw
        def button_touch_down(self, button, touch):
            """ Use collision detection to select buttons when the touch occurs
            within their area. """
            if button.collide_point(*touch.pos):
                self.select_with_touch(button, touch)

        def select_node(self, node):
            node.background_color = (200/255, 255/255, 255/255, 1)
            node.color=(1,1,1,1)
            return super(TypeSelector, self).select_node(node)

        def deselect_node(self, node):
            node.background_color = (0, 0, 0, 0)
            node.color=(0,0,0,1)
            super(TypeSelector, self).deselect_node(node)
        
        def on_selected_nodes(self, _, nodes):
            if not nodes: #this method, for some reason first gets an empty list and then a list with the element
                return    #gotta skip the empty list
                          #node objects are just the original objects, here the buttons, whose attributes can be accessed normally 
                          

            if(nodes[0].text =="Categories"):
                self.cm.on_menu_selection(selection="categories")
            elif(nodes[0].text == "Topics"):
                self.cm.on_menu_selection(selection="topics")
            else:
                pass

            
            
            
class MenuBar(GridLayout):
    """Menubar to select content type and add/remove topics"""
    def __init__(self, ts: TopicService, cs: CategoryService,cm, **kwargs):
        super().__init__(**kwargs)
        
        self.topic_service=ts
        self.category_service=cs
        self.cm=cm
        
        self.cols=3
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
        
        type_selector= TypeSelector(ts=self.topic_service, cs=self.category_service, cm=self.cm)
        
        self.add_widget(add_button)
        self.add_widget(remove_button)
        self.add_widget(type_selector)
        
        
    def add_items(self, _):
        self.cm.on_add_item()
        
    def remove_items(self,_):
        self.cm.on_remove_item()
        
        
        

class EditingBlock(FloatLayout):
    """Contains all Input field necessary to edit content. Saves content type and selected ID in properties"""
    db_id = NumericProperty(0) #add the id as a property to make updates possible
    content_type = StringProperty() #for table selection
    
    def __init__(self, ts: TopicService, cs: CategoryService, **kwargs):
        super().__init__(**kwargs)
        
        self.topic_service=ts
        self.category_service=cs
        
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
        """Handles basic data processing for the services to save to DB"""
        title = self.title_input.text
        desc = self.desc_input.text
        category_selection=[checkbox.category_id for checkbox in self.category_box.children if checkbox.checked]
        
        if self.content_type=="categories":
            self.category_service.rename(self.db_id, title)
        elif self.content_type=="topics":
            self.topic_service.update(self.db_id, title, desc)
            self.topic_service.set_assignment(self.db_id, category_selection)
        
    
    def load_item_content(self, item_id, type):
        """Loads content for given item_id and type"""
        self.category_box.clear_widgets()
        
        self.db_id=item_id
        self.content_type=type
                                        
        if type == "topics":
           
            categories = self.category_service.list()
            topic_in_category = self.topic_service.get_assignments(item_id)
                                            
            topic = self.topic_service.get(item_id)
            self.title_input.text=topic.title
            self.desc_input.text=topic.description
            
            for category in categories:
                self.category_box.add_widget(LabeledCheckbox(text=category.title, category_id=category.id, checked=category.id in topic_in_category))
            
        
        elif type == "categories":
            self.title_input.text=self.category_service.get(item_id).title
            self.desc_input.text=""
            


#--Main window stuff

class ContentManager(FloatLayout):
        # use this as central controller/interface for different window parts
        def __init__(self, ts:TopicService, cs: CategoryService, **kwargs):
            super().__init__(**kwargs)
            
            self.topic_service=ts
            self.category_service=cs
            
            self.orientation='horizontal'
            self.current_data_type = None #tracking which type is currently active (topics/cats)                meow
                        

            self.list_selector = ListSelector(size_hint=(0.2, 0.8), pos_hint={'x': 0.01, 'y': 0.05}, ts=self.topic_service, cs=self.category_service)
            self.add_widget(self.list_selector)

            #menu bar
            menu_bar = MenuBar(size_hint=(1, None), pos_hint={'y':0.82}, ts=self.topic_service, cs=self.category_service, cm=self)
            self.add_widget(menu_bar)
            
            #EditingBlock with input fields
            self.editing_block = EditingBlock(size_hint=(0.74, 0.83), pos_hint={'x': 0.25, 'y': 0.02}, ts=self.topic_service, cs=self.category_service)
            #editing_block.bind(pos=self.debug_bg_update, size=self.debug_bg_update)
            self.add_widget(self.editing_block)

        def on_add_item(self, *_):
            if self.current_data_type == "categories": #skip categories as we won't be handling those
                return
            
            self.topic_service.add_topic()
            
            self.list_selector.update_content("topics")
            self.list_selector.scroll_to_end()
        
        def on_remove_item(self, *_):
            if self.current_data_type == "categories":
                return
            
            id = self.editing_block.db_id
            self.topic_service.remove_topic(id)
            
            self.list_selector.update_content("topics")
            
            
        def update_editing_block_fields(self, db_id):
            """"Called when a button on the list is pressed"""
            if self.current_data_type:
                self.editing_block.load_item_content(db_id, self.current_data_type)
        
        def on_menu_selection(self, selection):
            if selection =="categories":
                self.current_data_type="categories"
            elif selection == "topics":
                self.current_data_type ="topics"
                
            self.list_selector.update_content(content=self.current_data_type)
        
        def debug_bg_update(self, instance, *_):
            with instance.canvas.before:
                Color(rgba=(0.2,0.2,0.2,0.5))
                Rectangle(pos=instance.pos, size=instance.size)


class ContentManagerApp(App):
    def build(self):

        Window.clearcolor=(0.95, 0.95, 0.95, 1) #global background color

        db = Manager()
        db.ensure_database_availability()
        
        topic_service = TopicService(db)
        category_service = CategoryService(db)

        window = ContentManager(topic_service, category_service)

        return window



if __name__ == '__main__':
    ContentManagerApp().run()