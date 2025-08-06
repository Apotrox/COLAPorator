from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.behaviors import FocusBehavior
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from backend.database_manager import Manager
from backend.tlv493d import TLV493D
import threading


db = Manager()
db.ensure_database_availability()

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

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return
        pos = args[1]
        self.hovered = self.collide_point(*self.to_widget(*pos))

    def on_hovered(self, instance, hovered):
        # Update canvas when hovered state changes
        self.canvas.before.clear()
        with self.canvas.before:
            Color(rgba=(0.8, 0.87, 1, 1) if hovered else (1, 1, 1, 1))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[12])

    def on_pos(self, *args):
        # Update canvas when position changes
        self.on_hovered(self, self.hovered)

    def on_size(self, *args):
        # Update canvas when size changes
        self.on_hovered(self, self.hovered)

        
class SelectableButton(HoverableButton, FocusBehavior, RecycleDataViewBehavior, Button):
    text = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.size_hint_x = 0.95
        self.pos_hint = {"center_x": 0.5}

    def on_press(self):
        desc = db.execute(f"SELECT description FROM topics WHERE title = '{self.text}'").fetchone()
        if desc:
            app = App.get_running_app()
            detail_screen = app.root.get_screen('topic_detail')
            detail_screen.display_topic(desc[0])
            app.root.current = 'topic_detail'

class TopicListScreen(Screen):
    def __init__(self, tlv, **kwargs):
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
        
        # Title label
        title_label = Label(
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
            default_size=(None, dp(50)),
            default_size_hint=(1, None),
            size_hint_y=None,
            orientation='vertical',
            spacing=dp(10),
            padding=[5, 0, 5, 0]
        )
        recycle_layout.bind(minimum_height=recycle_layout.setter('height'))
        
        self.rv.add_widget(recycle_layout)
        self.rv.viewclass = 'SelectableButton'
        
        # Add widgets to main layout
        main_layout.add_widget(title_label)
        main_layout.add_widget(self.rv)
        
        self.add_widget(main_layout)

    def update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def on_enter(self):
        data = db.execute("SELECT title FROM topics").fetchall()
        self.rv.data = [{'text': topic[0]} for topic in data]


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
            text='',
            font_size=18,
            color=(0.1, 0.1, 0.1, 1),
            size_hint_y=0.9
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

    def update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def display_topic(self, text):
        self.content_label.text = text

    def go_back(self, *args):
        self.manager.current = 'topic_list'

class StartupScreen(Screen):
    def __init__(self, tlv, **kw):
        super().__init__(**kw)

        startup_label = Label(
            text='Spin the wheel to start',
            font_size=26,
            color=(1, 1, 1, 1)
        )
        
        self.add_widget(startup_label)
        
        

class ColapsApp(App):
    def build(self):
        # binding one global instance of the sensor to then give to the other screens that need it
        self.tlv = TLV493D()
        threading.Thread(target=self.tlv.start_reading, daemon=True).start()
        
        
        sm = ScreenManager()
        startup_screen = StartupScreen(name="startup", tlv =self.tlv)
        topic_list_screen = TopicListScreen(name='topic_list', tlv = self.tlv)
        detail_screen = TopicDetailScreen(name='topic_detail')
        
        sm.add_widget(startup_screen)
        sm.add_widget(topic_list_screen)
        sm.add_widget(detail_screen)

        return sm


if __name__ == '__main__':
    ColapsApp().run()
