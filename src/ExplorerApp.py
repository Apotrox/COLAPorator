from kivy.app import App

from kivy.uix.screenmanager import ScreenManager, FallOutTransition, RiseInTransition

from topics.TopicService import TopicService
from categories.CategoryService import CategoryService

from database.database_manager import Manager

from hardware.tlv493d import TLV493D
from hardware.JoystickManager import Joystick

from screens.TopicListScreen import TopicListScreen
from screens.TopicDetailScreen import TopicDetailScreen
from screens.StartupScreen import StartupScreen
from screens.WaitingScreen import WaitingScreen


from kivy.clock import Clock
import threading

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
        
        #Window.fullscreen = True

        return self.sm

    # centralized movement checks
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
