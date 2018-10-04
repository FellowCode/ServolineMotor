import kivy

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout

from serial.tools import list_ports
print(list_ports.comports())

from kivy.uix.dropdown import DropDown
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput

from kivy.config import Config

Config.set('graphics', 'resizable', 0)
Config.set('graphics', 'width', 500)
Config.set('graphics', 'height', 320)


class ServolineMotorApp(App):

    def build(self):
        com_dropdown = DropDown()
        for i in range(3):
            com_dropdown.add_widget(Button(text=str(i), height=20))

        bl_main = BoxLayout(orientation='vertical', padding=10)
        fl1 = AnchorLayout(anchor_x='left', anchor_y='center')
        com_input = TextInput()
        fl1.add_widget(com_input)
        bl_main.add_widget(fl1)
        bl_main.add_widget(Widget())
        bl_main.add_widget(Widget())
        bl_main.add_widget(Widget())
        bl_main.add_widget(Widget())
        # return a Button() as a root widget
        return bl_main


if __name__ == '__main__':
    ServolineMotorApp().run()