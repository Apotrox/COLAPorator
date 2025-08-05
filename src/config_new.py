from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup

import math, threading
from backend.tlv493d import TLV493D
from backend.database_manager import Manager

class AngleDisplay(FloatLayout):
    def __init__(self, tlv, **kwargs):
        super().__init__(**kwargs)
        self.angle = 0
        self.tlv=tlv

        # Label added as widget
        self.label = Label(text="0°", color=(0,0,1,1), pos_hint={'x':0, 'y':0.3}, font_size='40sp')
        self.add_widget(self.label)

        # Static background + circle (draw once)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)

            Color(0, 1, 0)
            self.circle = Ellipse(size=(0, 0), pos_hint={'x':0.5, 'y':1})

        # Dynamic line (redraw in canvas.after)
        with self.canvas.after:
            self.line_color = Color(1, 0, 0)
            self.line = Line(points=[0, 0, 0, 0], width=2)

        # Update canvas and geometry
        self.bind(pos=self.update_static, size=self.update_static)
        Clock.schedule_interval(self.update_dynamic, 1 / 40)

    def update_static(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

        cx = self.x + self.width * 0.5
        cy = self.y + self.height * 0.5
        radius = min(self.width, self.height) * 0.4
        self.circle.pos = (cx - radius, cy - radius)
        self.circle.size = (radius * 2, radius * 2)

    def update_dynamic(self, dt):
        self.angle = -self.tlv.get_angle()
        self.label.text = f"{-self.angle:.1f}°"

        cx, cy = self.center
        radius = min(self.width, self.height) * 0.4
        rad = math.radians(self.angle)
        x = cx + radius * math.cos(rad)
        y = cy + radius * math.sin(rad)

        self.line.points = [cx, cy, x, y]

class TableDisplay(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols=2
        self.row_force_default=True
        self.row_default_height=40

    def update_table(self, data):
        self.clear_widgets()
        for row in data:
            for cell in row:
                self.add_widget(Label(text=str(cell), color=(1,1,1,1)))

class ConfirmPopup(Popup):
    def __init__(self,msg , slice_data, **kwargs):
        super().__init__(**kwargs)
        self.data = slice_data
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

        #globalizing popup to close it in confirm method
        self.title='Confirmation'
        self.content=popup_layout
        self.size_hint=(None,None) 
        self.size=(400,200)
        self.auto_dismiss=False
        dismiss_button.bind(on_press=self.dismiss)
    
    def _confirm(self, _):
        self.angles_to_database(self.data)

        end_layout = BoxLayout(orientation="vertical")
        end_layout.add_widget(Label(text="Successfully commited to database"))
        end_button = Button(text="Ok")
        end_button.bind(on_press=self.dismiss)
        end_layout.add_widget(end_button)
        self.content=end_layout
        self.auto_dismiss=True

    def angles_to_database(self, data):
        #db = Manager()
        #db.ensure_database_availability()
        slice_angles = [x[1] for x in data]
        slice_names = [x[0] for x in data]
        
        slices = [(
            slice_names[i],
            slice_angles[i], #begin angle
            slice_angles[(i+1) % len(slice_angles)] #end angle
        )for i in range (len(slice_angles))]
        #db.execute_many("INSERT INTO slices (title, angle_begin, angle_end) VALUES (?, ?, ?)", slices)
        #db.commit_changes()
        print(slices)

        #TODO Error Handling


class StartupScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation='vertical') #use boxlayout inside the screen, a screen should contain a layout, not be one

        auto_button = Button(text="Automatic Calibration")
        auto_button.bind(on_press=self.auto_cfg)
        manual_button = Button(text="Manual Configuration")
        manual_button.bind(on_press=self.manual_cfg)
        
        layout.add_widget(auto_button)
        layout.add_widget(manual_button)

        self.add_widget(layout)

    def auto_cfg(self, *args):
        self.manager.current='auto'
    
    def manual_cfg(self, *args):
        self.manager.current='manual'

class AutoScreen(Screen):
    def __init__(self, tlv, **kw):
        super().__init__(**kw)
        self.data =[] 
        self.tlv = tlv

        base_layout = BoxLayout(orientation = "horizontal")
        left_layout = FloatLayout()
        right_layout = FloatLayout()

        back = Button(text="Back", size_hint=(0.14, 0.06), pos_hint={'x': 0.02, 'y': 0.02})
        back.bind(on_press=self.go_back)

        self.textinput = TextInput(hint_text="Input number of slices", size_hint=(0.8,0.1), multiline=False, pos_hint={'x': 0.1, 'y': 0.85})
        self.textinput.bind(on_text_validate=self.calculate)
        
        enter = Button(text="Enter", size_hint=(0.15,0.075), pos_hint={'x': 0.75, 'y': 0.75})
        enter.bind(on_press=self.calculate)

        hint_label = Label(text="Align any slice edge with the pointer, enter the number of slices above and press enter.",
                           text_size=(220,None), pos_hint={'x':-0.08, 'y':0.29})

        self.table = TableDisplay(pos_hint={'x':0, 'y':-0.3})

        confirm = Button(text="Confirm", size_hint=(0.18, 0.06), pos_hint={'x':0.8, 'y':0.02})
        confirm.bind(on_press=self.popup_dialogue)

        #adding the widgets to each side
        angle_display = AngleDisplay(tlv=self.tlv, pos_hint={'x':0.01, 'y':0})
        right_layout.add_widget(angle_display)
        right_layout.add_widget(confirm)

        left_layout.add_widget(self.textinput)
        left_layout.add_widget(enter)
        left_layout.add_widget(hint_label)
        left_layout.add_widget(self.table)
        left_layout.add_widget(back)

        base_layout.add_widget(left_layout)
        base_layout.add_widget(right_layout)

        self.add_widget(base_layout)

    def go_back(self, _):
        #resetting everything
        self.data=[]
        self.table.update_table(self.data)
        self.textinput.text=""
        self.manager.current = 'startup'
    
    def calculate(self, _): #input at instance.text
        self.data=[] #clear data for new calculation
        initial_angle = self.tlv.get_angle()
        self.data.append(["Slice 0", initial_angle])

        num_slices = int(self.textinput.text)
        #if a circle is [0;2pi), then we can divide 2pi by the number of segments to get accurate points
        segment_length = int(math.degrees((math.pi*2)/num_slices))
        for i in range (1, num_slices):
            angle = initial_angle + segment_length*i
            if(angle <0): angle +=360
            if(angle > 360): angle -= 360
            self.data.append([f"Slice {i}",angle])
        self.table.update_table(self.data)
    
    
    def popup_dialogue(self, _):
        popup = ConfirmPopup(msg="Commit to database?", slice_data=self.data)
        popup.open()



class ManualScreen(Screen):
    def __init__(self,tlv, **kw):
        super().__init__(**kw)
        self.tlv = tlv
        self.data=[]

        base_layout = BoxLayout(orientation = "horizontal")
        left_layout = FloatLayout()
        right_layout = FloatLayout()

        back = Button(text="Back", size_hint=(0.14, 0.06), pos_hint={'x': 0.02, 'y': 0.02})
        back.bind(on_press=self.go_back)
        
        record = Button(text="Record Angle", size_hint=(0.3,0.1), pos_hint={'x': 0.35, 'y': 0.85})
        record.bind(on_press=self.add_angles)

        hint_label = Label(text="Align next slice edge with the pointer and press the button above to record the angle. " \
        "The programm will automatically detect if the wheel looped around.",
                           text_size=(270,None), pos_hint={'x':-0.05, 'y':0.29})

        self.table = TableDisplay(pos_hint={'x':0, 'y':-0.3})

        confirm = Button(text="Confirm", size_hint=(0.18, 0.06), pos_hint={'x':0.8, 'y':0.02})
        confirm.bind(on_press=self.popup_dialogue)

        #adding the widgets to each side
        angle_display = AngleDisplay(tlv=self.tlv, pos_hint={'x':0.01, 'y':0})
        right_layout.add_widget(angle_display)
        right_layout.add_widget(confirm)

        left_layout.add_widget(record)
        left_layout.add_widget(hint_label)
        left_layout.add_widget(self.table)
        left_layout.add_widget(back)

        base_layout.add_widget(left_layout)
        base_layout.add_widget(right_layout)

        self.add_widget(base_layout)

    def add_angles(self, _):
        angle = self.tlv.get_angle()
        if(len(self.data)>0 and (angle+5 >= int(self.data[0][1]) and angle-5 <= int(self.data[0][1]))):
            self.popup_dialogue()
        else:
            self.data.append([f"Slice {len(self.data)}", angle])
            self.table.update_table(self.data)

    def go_back(self, *args):
        #resetting everything
        self.data=[]
        self.table.update_table(self.data)
        self.manager.current = 'startup'
    
    def popup_dialogue(self):
        popup = ConfirmPopup(msg=f"Are {len(self.data)} slices correct?",slice_data=self.data)
        popup.open()


class ConfigApp(App):
    def build(self):
        # binding one global instance of the sensor to then give to the other screens that need it
        self.tlv = TLV493D()
        threading.Thread(target=self.tlv.start_reading, daemon=True).start()

        sm = ScreenManager()
        startup_screen = StartupScreen(name="startup")
        auto_screen = AutoScreen(name="auto", tlv=self.tlv)
        manual_screen = ManualScreen(name="manual", tlv=self.tlv)

        sm.add_widget(startup_screen)
        sm.add_widget(auto_screen)
        sm.add_widget(manual_screen)

        return sm

if __name__ == '__main__':
    ConfigApp().run()
