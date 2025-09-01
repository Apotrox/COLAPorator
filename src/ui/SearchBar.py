from kivy.uix.textinput import TextInput
from services.TopicService import TopicService
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty


class SearchBar(TextInput):
    callback=ObjectProperty(None)
    def __init__(self, ts:TopicService, hint_text:str, callback, **kwargs):
        super().__init__(**kwargs)
        
        self.ts=ts    
        self.callback=callback 

        self.hint_text=hint_text
        self.multiline = False # change if necessary
        self.bind(on_text_validate=self.on_enter)
    
    def on_enter(self, instance):
        if callable(self.callback):
            self.callback(instance.text)