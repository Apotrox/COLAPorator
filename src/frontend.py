from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.behaviors import FocusBehavior
from kivy.core.window import Window
from kivy.uix.label import Label
from backend.database_manager import Manager
from backend.tlv493d import TLV493D


db = Manager()
db.ensure_database_availability()

class HoverableButton(Button):
    hovered = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return
        pos = args[1]
        self.hovered = self.collide_point(*self.to_widget(*pos))
        
class SelectableButton(HoverableButton ,FocusBehavior, RecycleDataViewBehavior, Button):
    text = StringProperty()

    def on_press(self):
        desc = db.execute(f"SELECT description FROM topics WHERE title = '{self.text}'").fetchone()
        if desc:
            app = App.get_running_app()
            detail_screen = app.root.get_screen('topic_detail')
            detail_screen.display_topic(desc[0])
            app.root.current = 'topic_detail'

class TopicListScreen(Screen):
    def on_enter(self):
        data = db.execute("SELECT title FROM topics").fetchall()
        self.ids.rv.data = [{'text': topic[0]} for topic in data]


class TopicDetailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def display_topic(self, text):
        self.ids.label.text = text

    def go_back(self, *args):
        self.manager.current = 'topic_list'

class StartupScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

class ColapsApp(App):
    def build(self):
        sm = ScreenManager()
        topic_list_screen = TopicListScreen(name='topic_list')
        detail_screen = TopicDetailScreen(name='topic_detail')
        startup_screen = StartupScreen(name= "startup")
        
        sm.add_widget(startup_screen)
        sm.add_widget(topic_list_screen)
        sm.add_widget(detail_screen)

        return sm

if __name__ == '__main__':
    ColapsApp().run()
