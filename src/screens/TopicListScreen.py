
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.screenmanager import  Screen, SlideTransition
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from typing import List


from topics.TopicService import TopicService
from categories.CategoryService import CategoryService
from topics.Topic import Topic
from hardware.JoystickManager import Joystick, Intent
from ui.RotatedLabel import RotatedLabel
from ui.TopicListButton import AppSelectableButton
from ui.SearchBar import SearchBar

from kivy.clock import Clock


class TopicListScreen(Screen):
    def __init__(self, ts:TopicService, cs:CategoryService, js:Joystick, **kwargs):
        super().__init__(**kwargs)

        self.js=js
        self.ts=ts
        self.cs=cs
        
        self.selection_index=0
        
        main_layout = FloatLayout()
        
        # Set background
        with main_layout.canvas.before:
            Color(rgba=(0.95, 0.95, 0.95, 1))
            self.bg_rect = Rectangle(pos=main_layout.pos, size=main_layout.size)
        
        # Update background when layout changes
        main_layout.bind(pos=self.update_bg, size=self.update_bg)
        
        
        self.title_label = Label(
            text='Available Topics',
            font_size=24,
            size_hint=(None,0.1),
            color=(0.2, 0.2, 0.2, 1),
            pos_hint={'center_x': 0.5, 'top':0.99}
        )
        
        self.rv = RecycleView(
            bar_width=10,
            scroll_type=['bars', 'content'],
            pos_hint={'center_x': 0.5, 'top':0.8},
            size_hint=(0.85,0.75)
        )
        
        recycle_layout = RecycleBoxLayout(
            default_size=(None, None),  # Let buttons determine their own height
            default_size_hint=(1, None),
            size_hint_y=None,
            orientation='vertical',
            spacing=dp(10),
            padding=[5, 0, 5, 0]
        )
        recycle_layout.bind(minimum_height=recycle_layout.setter('height'))
        
        
        searchbar=SearchBar(
            pos_hint={'center_x':0.5, 'top':0.9},
            size_hint=(0.7, 0.05),
            ts=self.ts,
            hint_text="Search topics here",
            callback=self.on_search
        )
        
        finish_layout=FloatLayout(pos_hint={"center_x":0.96, "center_y":0.5}, size_hint=(0.2,0.8))
        
        arrow=dict(text=("\u27A7"), font_size="40sp", color=(0.5,0.5,0.5,1), font_name="./DejaVuSans.ttf")
        
        finish_layout.add_widget(Label(**arrow, pos_hint={"right":1, "center_y":1}))
        finish_layout.add_widget(Label(**arrow,pos_hint={"right":1, "center_y":0.0}))
        
        finish_layout.add_widget(RotatedLabel(text="Move to the side to finish!", angle=90, font_size="20sp", pos_hint={"right":1, "center_y":0.5}))
        
        main_layout.add_widget(finish_layout)
        
        
        self.rv.add_widget(recycle_layout)
        self.rv.viewclass = 'AppSelectableButton'
        
        # Add widgets to main layout
        main_layout.add_widget(self.title_label)
        main_layout.add_widget(self.rv)
        
        main_layout.add_widget(searchbar)
        
        self.add_widget(main_layout)
        
        if(self.js): #if there is no joystick connected, skip it's entire logic
            self.selection_index=0
    

    def update_bg(self, instance, _):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def handle_choose(self, topic_id):
        topic = self.ts.get(topic_id)
        detail_screen = self.manager.get_screen('topic_detail')
        detail_screen.display_topic(topic.description)
        detail_screen.db_id=topic_id # to lay the groundwork for tracking/usage history
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'topic_detail'
        Clock.unschedule(self.check_joystick_events)

    def on_pre_enter(self):
        """Triggers button update with all topics in the chosen category"""
        category = self.cs.get_for_angle(self.angle)
        self.title_label.text = category.title

        topics = self.ts.list_by_category(category)
        
        self.update_buttons(topics)
        
        # very hacky and not pretty but by god it works 
        (_,size_y)=self.rv.size
        if(len(self.rv.data)>round(size_y/60)):
            Clock.schedule_once(lambda dt: self.animate_scroll_to(0.0, 0.2),0)
            Clock.schedule_once(lambda dt: self.animate_scroll_to(1.0, 0.2),1)

  
    def on_enter(self):
        if self.js:
            Clock.schedule_interval(self.check_joystick_events, 0.1)                
            
    def on_search(self, keyword: str):
        """Triggers button update with topics that match the keyword in the title"""
        results=self.ts.search(keyword) #returns list of IDs
        topics = self.ts.get_many(results) #returns list of Topics
        self.update_buttons(topics)
        
        
    def update_buttons(self, topics: List[Topic]):
        """Updates the buttons shown based on a list of Topics"""
        # Feed the view props via rv.data (keys must match viewclass properties)
        self.rv.data = [{
                'text': t.title,         # still sets the Button label
                'topic_id': t.id,
                'on_choose': self.handle_choose
            } for t in topics]
        

    #---Joystick input handling
    
    def check_joystick_events(self, *_):
        if self.manager.current=='topic_list':
            intent= self.js.get() #don't need to be here if it isnt the active screen
            if intent:
                self.handle_joystick_intents(intent)
    
    def handle_joystick_intents(self, intent:Intent):
        max_items=len(self.rv.data)
        if(max_items==0):
            return #just skip if there is no data
        
        if(0 <= self.selection_index < max_items): #gotta check bc apparently it can still exceed this despite the min/max above
            match intent:
                case Intent.UP:
                    self.selection_index=max(0, self.selection_index-1)
                    self.update_selection()
                    self.scroll_with_selection()
                case Intent.DOWN:
                    self.selection_index=min(max_items-1, self.selection_index+1)
                    self.update_selection()
                    self.scroll_with_selection()
                case Intent.SELECT:
                    topic_id=self.rv.data[self.selection_index]['topic_id']
                    self.handle_choose(topic_id)
                case _:
                    return

    def update_selection(self):
        """Updates the visual selection of buttons by setting 'hovered' state"""
        
        buttons=self.rv.children[0].children
        for i, button in enumerate(buttons):
            if hasattr(button, 'hovered'):
                button.hovered=(button.data_index==self.selection_index)
                
    def scroll_with_selection(self):
        total_items=len(self.rv.data)
        visible_items = len(self.rv.children[0].children)-1  # Approximate number of items visible at once
        (_,size_y)=self.rv.size
        
        if self.selection_index < 2 or (total_items <= round(size_y/60)):
            # Near the top - scroll to show from beginning
            target_scroll_y = 1.0
        elif ((self.selection_index >= total_items - 2)):
            # Near the bottom - scroll to show end
            target_scroll_y = 0.0
        else:
            # Middle items - center the selection in viewport
            # Calculate relative position (0.0 = bottom, 1.0 = top)
            relative_position = (total_items - 1 - self.selection_index) / max(1, total_items - visible_items)
            target_scroll_y = max(0.0, min(1.0, relative_position))
        
        self.animate_scroll_to(target_scroll_y)
        
    def animate_scroll_to(self, target_y, duration= 0.2):
        """Smoothly animate scroll to target position"""
        
        from kivy.animation import Animation
        
        # Cancel any existing scroll animation
        Animation.cancel_all(self.rv)
        
        # Animate to target position
        anim = Animation(scroll_y=target_y, duration=duration, transition='out_quart')
        anim.start(self.rv)