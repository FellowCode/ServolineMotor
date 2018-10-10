import kivy
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from modbus import Modbus
from threading import Timer
from servo_reg import ServoReg
import pickle

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout


from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.dropdown import DropDown

from kivy.config import Config

from kivy.graphics import Color, Rectangle
from kivy.lang import Builder
with open("main.kv", encoding='utf-8') as f:  # Note the name of the .kv
    # doesn't match the name of the App
    Builder.load_string(f.read())

window_height = 320
window_width = 400

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('graphics', 'resizable', 0)
Config.set('graphics', 'width', window_width)
Config.set('graphics', 'height', window_height)
Config.write()

class Preset:
    def __init__(self, name, speed, accel_time, deccel_time, work_time):
        self.name = name
        self.speed = speed
        self.accel_time = accel_time
        self.deccel_time = deccel_time
        self.work_time = work_time

class AutoMode(FloatLayout):
    reverse = False
    start_button = ObjectProperty()
    stop_button = ObjectProperty()
    mode_button = ObjectProperty()
    reverse_switch = ObjectProperty()
    def start_servo_time_work(self, instance):
        self.motor_timer = Timer(self.work_time/1000, self.stop_servo_time_work)
        self.motor_timer.start()
        self.start_button.disabled = True
        self.reverse_switch.disabled = True
        if not self.reverse:
            self.motor.servo_forward_start()
        else:
            self.motor.servo_reverse_start()

    def stop_servo_time_work_btn(self, instance):
        self.stop_servo_time_work()

    def stop_servo_time_work(self):
        self.motor_timer.cancel()
        self.start_button.disabled = False
        self.reverse_switch.disabled = False
        if not self.reverse:
            self.motor.servo_forward_stop()
        else:
            self.motor.servo_reverse_stop()

    def change_reverse(self, instance, value):
        self.reverse = value
        self.save_params()

    def disable_buttons(self, val):
        self.start_button.disabled = val
        self.stop_button.disabled = val
        self.mode_button.disabled = val
        self.reverse_switch.disabled = val

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_button.bind(on_press=self.start_servo_time_work)
        self.stop_button.bind(on_press=self.stop_servo_time_work_btn)
        self.mode_button.bind(on_press=myApp.root_widget.change_mode)
        self.reverse_switch.active = self.reverse

class ManualMode(FloatLayout):
    left_button = ObjectProperty()
    right_button = ObjectProperty()
    mode_button = ObjectProperty()

    def left_btn_state(self, instance, value):
        if value is 'down':
            self.motor.servo_forward_start()
        else:
            self.motor.servo_forward_stop()

    def right_btn_state(self, instance, value):
        if value is 'down':
            self.motor.servo_reverse_start()
        else:
            self.motor.servo_reverse_stop()

    def disable_buttons(self, val):
        self.left_button.disabled = val
        self.right_button.disabled = val
        self.mode_button.disabled = val

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.left_button.bind(state=self.left_btn_state)
        self.right_button.bind(state=self.right_btn_state)
        self.mode_button.bind(on_press=myApp.root_widget.change_mode)

class ParamInput(TextInput):
    def params_changed(self, instance, value):
        try:
            int(value)
        except:
            instance.text = value[:-1]

        if len(instance.text)>4:
            instance.text = value[:-1]

    def params_focus(self, instance, value):
        if len(instance.text) == 0:
            instance.text = '0'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(text=self.params_changed)
        self.bind(focus=self.params_focus)

class AddPresetPopup(Popup):
    preset_input = ObjectProperty()
    ok_button = ObjectProperty()
    cancel_button = ObjectProperty()

    def save(self, instance):
        if self.preset_input.text != '':
            myApp.root_widget.add_preset(self.preset_input.text)
            self.dismiss()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ok_button.bind(on_release=self.save)
        self.cancel_button.bind(on_release=self.dismiss)

class QuestionPopup(Popup):
    question = ObjectProperty()
    ok_button = ObjectProperty()
    cancel_button = ObjectProperty()

    ok_func = None

    def ok_btn(self, func):
        self.ok_func()
        self.dismiss()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ok_button.bind(on_release=self.ok_btn)
        self.cancel_button.bind(on_release=self.dismiss)

class RootWidget(FloatLayout):
    auto_mode = True
    buttons_is_disable = False

    com_num = 1
    motor = Modbus()

    speed = 0
    accel_time = 0
    deccel_time = 0
    work_time = 0
    reverse = False
    presets = []
    selected_preset = -1

    com_input = ObjectProperty()
    connect_button = ObjectProperty()
    speed_input = ObjectProperty()
    accel_time_input = ObjectProperty()
    deccel_time_input = ObjectProperty()
    work_time_input = ObjectProperty()
    motor_switch = ObjectProperty()
    apply_param_button = ObjectProperty()
    preset_button = ObjectProperty()
    add_preset_button = ObjectProperty()
    del_preset_button = ObjectProperty()

    def save_params(self):
        f = open('settings.txt', 'w')
        f.write(str(self.com_num)+'\n')
        f.write(str(self.speed)+'\n')
        f.write(str(self.accel_time)+'\n')
        f.write(str(self.deccel_time)+'\n')
        f.write(str(self.work_time)+'\n')
        f.write(str(self.reverse)+'\n')
        f.close()

    def load_params(self):
        try:
            f = open('settings.txt')
            self.com_num = int(f.readline())
            self.speed = int(f.readline())
            self.accel_time = int(f.readline())
            self.deccel_time = int(f.readline())
            self.work_time = int(f.readline())
            self.reverse = f.readline().strip()=='True'
            f.close()
        except:
            pass

    def save_presets(self):
        with open('presets.prs', 'wb') as f:
            pickle.dump(self.presets, f)

    def load_presets(self):
        try:
            with open('presets.prs', 'rb') as f:
                self.presets = pickle.load(f)
        except:
            pass

    def add_preset_popup(self, instance):
        popup = AddPresetPopup()
        popup.open()

    def add_preset(self, name):
        preset = Preset(name, int(self.speed_input.text), int(self.accel_time_input.text),
                        int(self.deccel_time_input.text), int(self.work_time_input.text))
        self.presets.append(preset)
        self.save_presets()
        self.update_presets_dropdown()

    def del_preset(self):
        if self.selected_preset >= 0:
            del self.presets[self.selected_preset]
            self.save_presets()
            self.update_presets_dropdown()
            self.preset_button.text = 'Пресет'

    def del_preset_btn(self, instance):
        if self.selected_preset >= 0:
            quest_popup = QuestionPopup()
            quest_popup.ok_func = self.del_preset
            quest_popup.question.text = 'Вы действительно хотите удалить пресет?'
            quest_popup.open()

    def select_preset(self, instance):
        self.selected_preset = int(instance.id)
        preset = self.presets[self.selected_preset]
        self.preset_button.text = instance.text
        self.speed_input.text = str(preset.speed)
        self.accel_time_input.text = str(preset.accel_time)
        self.deccel_time_input.text = str(preset.deccel_time)
        self.work_time_input.text = str(preset.work_time)
        self.dropdown.dismiss()

    def change_mode(self, instance):
        self.auto_mode = not self.auto_mode
        if self.auto_mode:
            self.fl_mode_manual.clear_widgets()
            self.build_auto_mode()
        else:
            self.fl_mode_auto.clear_widgets()
            self.build_manual_mode()

    def com_changed(self, instance, value):
        try:
            if len(instance.text) > 2:
                instance.text = value[:-1]
            self.com_num = int(value)
            self.save_params()
        except:
            instance.text = value[:-1]

    def change_connect(self, instance):
        if not self.motor.is_connect:
            self.connect()
        else:
            self.disconnect()

    def connect(self):
        self.motor.connect(self.com_num)
        if not self.motor.is_connect:
            pass
        else:
            self.connect_button.text = 'Отключиться'
            self.motor_switch.disabled = False
            self.apply_param_button.disabled = False

    def disconnect(self):
        self.motor.disconnect()
        if not self.motor.is_connect:
            self.connect_button.text = 'Соединиться'
            self.motor_switch.active = False
            self.motor_switch.disabled = True
            self.apply_param_button.disabled = True
            self.disable_buttons(True)


    def disable_buttons(self, val):
        self.buttons_is_disable = val
        myApp.mode_widget.disable_buttons(val)

    def change_motor_state(self, instance, value):
        if value:
            self.motor.servo_on()
        else:
            self.motor.servo_off()
        self.disable_buttons(not value)

    def set_params(self, instance):
        try:
            speed = int(self.speed_input.text)
            if self.speed != speed:
                self.motor.set_param(ServoReg.SPEED, speed)
                self.speed = speed
        except:
            pass
        try:
            accel_time = int(self.accel_time_input.text)
            if self.accel_time != accel_time:
                self.motor.set_param(ServoReg.ACCEL_TIME, accel_time)
                self.accel_time = accel_time
        except:
            pass
        try:
            deccel_time = int(self.deccel_time_input.text)
            if self.deccel_time != deccel_time:
                self.motor.set_param(ServoReg.DECCEL_TIME, deccel_time)
                self.deccel_time = deccel_time
        except:
            pass
        try:
            self.work_time = int(self.work_time_input.text)
        except:
            pass
        self.save_params()

    def update_presets_dropdown(self):
        self.dropdown.clear_widgets()
        for index, preset in enumerate(self.presets):
            btn = Button(id=str(index), text=str(preset.name), size_hint_y=None, height=25)
            btn.bind(on_release=self.select_preset)
            self.dropdown.add_widget(btn)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            self.load_params()
        except:
            pass
        self.load_presets()
        self.com_input.text = str(self.com_num)
        self.com_input.bind(text=self.com_changed)
        self.connect_button.bind(on_press=self.change_connect)
        self.speed_input.text = str(self.speed)
        self.accel_time_input.text = str(self.accel_time)
        self.deccel_time_input.text = str(self.deccel_time)
        self.work_time_input.text = str(self.work_time)
        self.motor_switch.bind(active=self.change_motor_state)
        self.motor_switch.disabled = True

        self.dropdown = DropDown()
        self.update_presets_dropdown()
        self.preset_button.bind(on_release=self.dropdown.open)

        self.add_preset_button.bind(on_press=self.add_preset_popup)
        self.del_preset_button.bind(on_press=self.del_preset_btn)

        self.apply_param_button.bind(on_press=self.set_params)
        self.apply_param_button.disabled = True


class ServolineMotorApp(App):
    def build_auto_mode(self):
        self.mode_widget = AutoMode()

    def build_manual_mode(self):
        self.mode_widget = ManualMode()

    def build(self):
        self.root_widget = RootWidget()
        self.mode_widget = AutoMode()
        self.root_widget.disable_buttons(True)
        self.root_widget.add_widget(self.mode_widget)

        return self.root_widget

    def on_stop(self):
        self.root_widget.disconnect()


myApp = ServolineMotorApp()

if __name__ == '__main__':
    myApp.run()
