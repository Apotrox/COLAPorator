from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FallOutTransition, RiseInTransition, SlideTransition
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.properties import ObjectProperty, NumericProperty


from topics.TopicService import TopicService
from categories.CategoryService import CategoryService
from topics.Topic import Topic
from categories.Category import Category
from database.database_manager import Manager
from hardware.tlv493d import TLV493D
from ui.SelectableButton import SelectableButton
from ui.HoverableButton import HoverableButton

from kivy.clock import Clock
import threading, time



class AppSelectableButton(SelectableButton):
    topic_id = NumericProperty(None)
    on_choose = ObjectProperty(None)    # callback injected via rv.data

    def on_press(self):
        # Keep the view "dumb": just signal upward
        if callable(self.on_choose):
            self.on_choose(self.topic_id)


class TopicListScreen(Screen):
    def __init__(self, angle: int, ts:TopicService, cs:CategoryService, **kwargs):
        super().__init__(**kwargs)

        self.angle = angle 
        self.ts=ts
        self.cs=cs
        
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
        
        # Title label
        self.title_label = Label(
            text='Available Topics',
            font_size=24,
            size_hint_y=0.1,
            color=(0.2, 0.2, 0.2, 1)
        )
        
        # RecycleView
        self.rv = RecycleView(
            bar_width=10,
            scroll_type=['bars', 'content']
        )
        
        # RecycleBoxLayout
        recycle_layout = RecycleBoxLayout(
            default_size=(None, None),  # Let buttons determine their own height
            default_size_hint=(1, None),
            size_hint_y=None,
            orientation='vertical',
            spacing=dp(10),
            padding=[5, 0, 5, 0]
        )
        recycle_layout.bind(minimum_height=recycle_layout.setter('height'))
        
        self.rv.add_widget(recycle_layout)
        self.rv.viewclass = 'AppSelectableButton'
        
        # Add widgets to main layout
        main_layout.add_widget(self.title_label)
        main_layout.add_widget(self.rv)
        
        self.add_widget(main_layout)

    def update_bg(self, instance, _):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def handle_choose(self, topic_id):
        topic = self.ts.get_by_id(topic_id)  # expose a get_by_id in your service if not present
        detail_screen = self.manager.get_screen('topic_detail')
        detail_screen.display_topic(topic.description)
        self.manager.transition = SlideTransition()
        self.manager.current = 'topic_detail'

    def on_enter(self):
            category = self.cs.get_for_angle(self.angle)
            self.title_label.text = category.title

            topics = self.ts.list_by_category(category)
            
            # Feed the view props via rv.data (keys must match viewclass properties)
            self.rv.data = [{
                'text': t.title,         # still sets the Button label
                'topic_id': t.id,
                'on_choose': self.handle_choose
            } for t in topics]


class TopicDetailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
        
        # Add widgets to main layout
        main_layout.add_widget(self.content_label)
        main_layout.add_widget(back_button)
        
        self.add_widget(main_layout)

    def update_bg(self, instance, _):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def display_topic(self, text):
        self.content_label.text = text

    def go_back(self, *_):
        self.manager.current = 'topic_list'


class StartupScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        
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
        
    def update_bg(self, instance, _):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

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
        

class ColapsApp(App):
    def build(self):
        # binding one global instance of the sensor to then give to the other screens that need it
        self.tlv = TLV493D()
        threading.Thread(target=self.tlv.start_reading, daemon=True).start()
        
        db = Manager()
        db.ensure_database_availability()
        
        ts=TopicService(db)
        cs=CategoryService(db)
        
        
        self.sm = ScreenManager()
        startup_screen = StartupScreen(name="startup")
        waiting_screen= WaitingScreen(name="waiting")
        topic_list_screen = TopicListScreen(name='topic_list', angle=self.tlv.get_angle(), ts=ts, cs=cs)
        detail_screen = TopicDetailScreen(name='topic_detail')
        
        self.sm.add_widget(startup_screen)
        self.sm.add_widget(waiting_screen)
        self.sm.add_widget(topic_list_screen)
        self.sm.add_widget(detail_screen)

        time.sleep(1) #delay scheduling to give moving average time to fill up
        
        #periodically check for movement
        Clock.schedule_interval(self.check_movement, 0.5)

        return self.sm

    def check_movement(self, _):
        if not self.tlv.get_moving():
            return True #not moving yet, continue checking
        
        Clock.unschedule(self.check_movement)
        Clock.schedule_interval(self.check_stopped, 0.5)
        self.sm.transition=RiseInTransition(duration=0.05)
        self.sm.current = 'waiting'
        return False
        
    def check_stopped(self,_):
        if self.tlv.get_moving():
            return True # still moving, continue checking
        
        Clock.unschedule(self.check_stopped)
        if self.sm:
            self.sm.transition=FallOutTransition()
            self.sm.current = 'topic_list'
        Clock.schedule_interval(self.check_movement, 0.5)
        return False
    
    def on_stop(self):
        self.tlv.stop_reading()


if __name__ == '__main__':
    ColapsApp().run()
