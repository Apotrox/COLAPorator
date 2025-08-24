from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FallOutTransition, RiseInTransition, SlideTransition
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.properties import ObjectProperty, NumericProperty
from kivy.uix.textinput import TextInput
from typing import List
#from kivy.event import EventDispatcher #learned of it's existence too late, would take too much time to rewrite everything in custom events .-.


from topics.TopicService import TopicService
from categories.CategoryService import CategoryService
from topics.Topic import Topic
from categories.Category import Category
from database.database_manager import Manager
from hardware.tlv493d import TLV493D
from hardware.JoystickManager import Joystick, Intent
from ui.SelectableButton import SelectableButton
from ui.HoverableButton import HoverableButton

from kivy.clock import Clock
import threading, time



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

class SearchBar(TextInput):
    def __init__(self, ts:TopicService, parent_screen, **kwargs):
        super().__init__(**kwargs)
        
        self.ts=ts
        self.parent_screen=parent_screen
        
        self.hint_text="Search topics here"
        self.multiline = False # change if necessary
        self.bind(on_text_validate=self.on_enter)
    
    def on_enter(self, instance):
        if self.parent_screen:
            self.parent_screen.on_search(instance.text)
                
        

class TopicListScreen(Screen):
    def __init__(self, ts:TopicService, cs:CategoryService, js:Joystick, **kwargs):
        super().__init__(**kwargs)

        self.js=js
        self.ts=ts
        self.cs=cs
        
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
            parent_screen = self
        )
        
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
        self.manager.transition = SlideTransition()
        self.manager.current = 'topic_detail'
        Clock.unschedule(self.check_joystick_events)

    def on_enter(self):
        """Triggers button update with all topics in the chosen category"""
        category = self.cs.get_for_angle(self.angle)
        self.title_label.text = category.title

        topics = self.ts.list_by_category(category)
        
        self.update_buttons(topics)
        
        self.selection_index=0
        if self.js:
            Clock.schedule_interval(self.check_joystick_events, 0.1)
        
        #Clock.schedule_once(self.debug, 0)
            
            
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
        
        
        if self.selection_index < 2:
            # Near the top - scroll to show from beginning
            target_scroll_y = 1.0
        elif self.selection_index >= total_items - 2 and total_items >6:
            # Near the bottom - scroll to show end
            target_scroll_y = 0.0
        else:
            # Middle items - center the selection in viewport
            # Calculate relative position (0.0 = bottom, 1.0 = top)
            relative_position = (total_items - 1 - self.selection_index) / max(1, total_items - visible_items) #TODO FIX
            target_scroll_y = max(0.0, min(1.0, relative_position))
        
        self.animate_scroll_to(target_scroll_y)
        
    def animate_scroll_to(self, target_y):
        """Smoothly animate scroll to target position"""
        from kivy.animation import Animation
        
        # Cancel any existing scroll animation
        Animation.cancel_all(self.rv)
        
        # Animate to target position
        anim = Animation(scroll_y=target_y, duration=0.2, transition='out_quart')
        anim.start(self.rv)
         
                

    def debug(self, *_):
        buttons = self.rv.children[0].children
        print(f"\nAmount of Buttons: {len(buttons)}")
        print(buttons)
        for i, button in enumerate(buttons):
            print(f"{len(buttons)-1-i}: {button}\n")
        
            


class TopicDetailScreen(Screen):
    def __init__(self, js:Joystick, **kwargs):
        super().__init__(**kwargs)

        self.js=js

        # Main container
        main_layout = BoxLayout(
            orientation='vertical',
            padding=[10, 10, 10, 10],
            spacing=10
        )
        
        # Set background
        with main_layout.canvas.before:
            Color(rgba=(0.95, 0.95, 0.95, 1))
            self.bg_rect = Rectangle(pos=main_layout.pos, size=main_layout.size)
        
        # Update background when layout changes
        main_layout.bind(pos=self.update_bg, size=self.update_bg)
        
        # Content label
        self.content_label = Label(
            text='Test',
            font_size=18,
            color=(0.1, 0.1, 0.1, 1),
            size_hint_y=0.9,
            text_size=(Window.width -60, None),
            halign='left',
            valign='top'
        )
        
        # Back button
        back_button = HoverableButton(
            text="Back",
            size_hint_y=0.1
        )
        back_button.bind(on_press=self.go_back)
        
        if(self.js):
            back_button.hovered=True #becomes unset if a mouse is present but oh well
        
        # Add widgets to main layout
        main_layout.add_widget(self.content_label)
        main_layout.add_widget(back_button)
        
        self.add_widget(main_layout)

    def update_bg(self, instance, _):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def display_topic(self, text):
        self.content_label.text = text
        if self.js:
            Clock.schedule_interval(self.check_joystick_events, 0.1)

    def go_back(self, *_):
        self.manager.current = 'topic_list'
        
    def check_joystick_events(self, *_):
        if self.manager.current=='topic_detail':
            intent= self.js.get() #don't need to be here if it isnt the active screen
            if intent:
                self.handle_joystick_intents(intent)
    
    def handle_joystick_intents(self, intent:Intent):
        if intent== Intent.SELECT:
            Clock.unschedule(self.check_joystick_events)
            self.go_back()



class StartupScreen(Screen):
    def __init__(self, js:Joystick, **kw):
        super().__init__(**kw)
        
        self.js=js
        
        self.startup_label = Label(
            text='Spin the wheel to start',
            font_size=26,
            color=(0.2, 0.2, 0.2, 1)
        )
        
        with self.canvas.before:
            Color(rgba=(0.95, 0.95, 0.95, 1))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
                # Update background when layout changes
        self.bind(pos=self.update_bg, size=self.update_bg)
        
        self.add_widget(self.startup_label)
        
        if self.js:
            Clock.schedule_interval(self.check_joystick_events, 0.1)
        
    def update_bg(self, instance, _):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        
    def check_joystick_events(self, *_):
        if self.manager.current=='startup':
            intent= self.js.get() #don't need to be here if it isnt the active screen
            if intent:
                self.handle_joystick_intents(intent)
    
    def handle_joystick_intents(self, intent:Intent):
        if intent== Intent.SELECT:
            Clock.unschedule(self.check_joystick_events)
            Clock.unschedule(App.get_running_app().check_movement) #quick and dirty i admit...
            App.get_running_app().check_stopped()

class WaitingScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        
        self.startup_label = Label(
            text='Please Wait...',
            font_size=26,
            color=(0.2, 0.2, 0.2, 1)
        )
        
        with self.canvas.before:
            Color(rgba=(0.95, 0.95, 0.95, 1))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
                # Update background when layout changes
        self.bind(pos=self.update_bg, size=self.update_bg)
        
        self.add_widget(self.startup_label)
        
        
    def update_bg(self, instance, _):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        

class ColapsExplorerApp(App):
    def build(self):
        # binding one global instance of the sensor to then give to the other screens that need it
        self.tlv = TLV493D()
        threading.Thread(target=self.tlv.start_reading, daemon=True).start()
        
        db = Manager()
        db.ensure_database_availability()
        
        ts=TopicService(db)
        cs=CategoryService(db)
        
        self.joystick = Joystick()
        if self.joystick:
            self.joystick.start() 
        
        
        self.sm = ScreenManager()
        startup_screen = StartupScreen(name="startup", js=self.joystick)
        waiting_screen= WaitingScreen(name="waiting")
        self.topic_list_screen = TopicListScreen(name='topic_list', ts=ts, cs=cs, js=self.joystick)
        detail_screen = TopicDetailScreen(name='topic_detail', js=self.joystick)
        
        self.sm.add_widget(startup_screen)
        self.sm.add_widget(waiting_screen)
        self.sm.add_widget(self.topic_list_screen)
        self.sm.add_widget(detail_screen)
        
        #periodically check for movement
        Clock.schedule_interval(self.check_movement, 0.5)

        return self.sm

    def check_movement(self, *_):
        if not self.tlv.get_moving():
            return True #not moving yet, continue checking
        
        Clock.unschedule(self.check_movement)
        Clock.schedule_interval(self.check_stopped, 0.5)
        self.sm.transition=RiseInTransition(duration=0.05)
        self.sm.current = 'waiting'
        return False
        
    def check_stopped(self,*_):
        if self.tlv.get_moving():
            return True # still moving, continue checking
        
        Clock.unschedule(self.check_stopped)
        if self.sm:
            self.sm.transition=FallOutTransition()
            self.topic_list_screen.angle=self.tlv.get_angle() #setting the current angle before changing screens
            self.sm.current = 'topic_list'
        Clock.schedule_interval(self.check_movement, 0.5)
        return False
    
    def on_stop(self):
        self.tlv.stop_reading()
        self.joystick.stop()
        


if __name__ == '__main__':
    ColapsExplorerApp().run()
