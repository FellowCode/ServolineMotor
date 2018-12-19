import kivy
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from modbus import Modbus
from threading import Timer
from servo_reg import ServoReg
import pickle
import sys
import os
from copy import deepcopy

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

# from kivy.modules import keybinding
from pynput.keyboard import Key, Listener

from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.dropdown import DropDown

from kivy.config import Config
from kivy.core.window import Window

from kivy.graphics import Color, Rectangle
from kivy.lang import Builder


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


kv_path = 'main.kv'
with open(resource_path(kv_path), encoding='utf-8') as f:  # Note the name of the .kv
    # doesn't match the name of the App
    Builder.load_string(f.read())

window_height = 320
window_width = 400
Window.size = (window_width, window_height)

Config.read(resource_path('config.ini'))
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('graphics', 'width', window_width)
Config.set('graphics', 'height', window_height)
Config.set('graphics', 'resizable', 0)
Config.set('kivy', 'window_icon', resource_path('icon.ico'))
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
        self.motor_timer = Timer(myApp.root_widget.work_time / 1000, self.stop_servo_time_work)
        self.motor_timer.start()
        self.start_button.disabled = True
        self.reverse_switch.disabled = True
        if not self.reverse:
            myApp.root_widget.motor.servo_forward_start()
        else:
            myApp.root_widget.motor.servo_reverse_start()

    def stop_servo_time_work(self, instance=None):
        self.motor_timer.cancel()
        self.start_button.disabled = False
        self.reverse_switch.disabled = False
        if not self.reverse:
            myApp.root_widget.motor.servo_forward_stop()
        else:
            myApp.root_widget.motor.servo_reverse_stop()

    def change_reverse(self, instance, value):
        self.reverse = myApp.root_widget.reverse = value
        myApp.root_widget.save_params()

    def disable_buttons(self, val):
        self.start_button.disabled = val
        self.stop_button.disabled = val
        self.mode_button.disabled = val
        self.reverse_switch.disabled = val

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_button.bind(on_press=self.start_servo_time_work)
        self.stop_button.bind(on_press=self.stop_servo_time_work)
        self.mode_button.bind(on_press=myApp.change_mode)
        self.reverse_switch.bind(active=self.change_reverse)
        self.reverse_switch.active = self.reverse


class ManualMode(FloatLayout):
    left_button = ObjectProperty()
    right_button = ObjectProperty()
    mode_button = ObjectProperty()

    def left_btn_state(self, instance, value):
        if value is 'down':
            myApp.root_widget.motor.servo_forward_start()
        else:
            myApp.root_widget.motor.servo_forward_stop()

    def right_btn_state(self, instance, value):
        if value is 'down':
            myApp.root_widget.motor.servo_reverse_start()
        else:
            myApp.root_widget.motor.servo_reverse_stop()

    def disable_buttons(self, val):
        self.left_button.disabled = val
        self.right_button.disabled = val
        self.mode_button.disabled = val

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.left_button.bind(state=self.left_btn_state)
        self.right_button.bind(state=self.right_btn_state)
        self.mode_button.bind(on_press=myApp.change_mode)


class ParamInput(TextInput):
    def params_changed(self, instance, value):
        try:
            int(value)
        except:
            instance.text = value[:-1]

        if len(instance.text) > 4:
            instance.text = value[:-1]

    def params_focus(self, instance, value):
        if len(instance.text) == 0:
            instance.text = '0'
        elif int(instance.text) < 0:
            instance.text = '0'
        myApp.root_widget.check_param_equals()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(text=self.params_changed)
        self.bind(focus=self.params_focus)
        self.text = '0'


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


class ErrorPopup(Popup):
    error = ObjectProperty()
    ok_button = ObjectProperty()

    def __init__(self, text):
        super().__init__()
        self.error.text = text
        self.ok_button.bind(on_release=self.dismiss)
        self.open()


class RootWidget(FloatLayout):
    buttons_is_disable = False

    sync_param_process = False

    com_num = 1
    motor = Modbus()

    speed = -1
    accel_time = -1
    deccel_time = -1

    auto_speed = -1
    auto_accel_time = -1
    auto_deccel_time = -1

    manual_speed = -1
    manual_accel_time = -1
    manual_deccel_time = -1

    work_time = -1
    reverse = False
    auto_presets = []
    manual_presets = []
    selected_preset = -1

    com_input = ObjectProperty()
    connect_button = ObjectProperty()
    speed_input = ObjectProperty()
    speed_error_img = ObjectProperty()
    accel_time_input = ObjectProperty()
    accel_error_img = ObjectProperty()
    deccel_time_input = ObjectProperty()
    deccel_error_img = ObjectProperty()
    work_time_input = ObjectProperty()
    work_error_img = ObjectProperty()
    motor_switch = ObjectProperty()
    apply_param_button = ObjectProperty()
    preset_button = ObjectProperty()
    add_preset_button = ObjectProperty()
    del_preset_button = ObjectProperty()
    sync_params_button = ObjectProperty()

    def error(self, text):
        ErrorPopup(text)

    def resource_path(self, relative_path):
        print(resource_path(relative_path))
        return resource_path(relative_path)

    def save_params(self):
        with open('settings.txt', 'w') as f:
            f.write(str(self.com_num) + '\n')
            f.write(str(self.auto_speed) + '\n')
            f.write(str(self.auto_accel_time) + '\n')
            f.write(str(self.auto_deccel_time) + '\n')
            f.write(str(self.work_time) + '\n')
            f.write(str(self.reverse) + '\n')
            f.write(str(self.manual_speed) + '\n')
            f.write(str(self.manual_accel_time) + '\n')
            f.write(str(self.manual_deccel_time) + '\n')

    def load_params(self):
        try:
            f = open('settings.txt')
            self.com_num = int(f.readline())
            auto_speed = f.readline().strip()
            if auto_speed != '-1':
                self.speed_input.text = auto_speed
                self.accel_time_input.text = f.readline().strip()
                self.deccel_time_input.text = f.readline().strip()
                self.work_time_input.text = f.readline().strip()
                self.work_time = int(self.work_time_input.text)
                self.reverse = f.readline().strip() == 'True'
            else:
                for i in range(4):
                    f.readline()

            manual_speed = int(f.readline())
            if manual_speed != -1:
                self.manual_speed = manual_speed
                self.manual_accel_time = int(f.readline())
                self.manual_deccel_time = int(f.readline())
            f.close()
        except:
            print('load params error')

    def save_presets(self):
        with open('presets.prs', 'wb') as f:
            presets = [self.auto_presets, self.manual_presets]
            pickle.dump(presets, f)

    def load_presets(self):
        try:
            with open('presets.prs', 'rb') as f:
                presets = pickle.load(f)
                self.auto_presets = presets[0]
                self.manual_presets = presets[1]
        except:
            self.auto_presets = []
            self.manual_presets = []

    def check_param_equals(self):
        if int(self.speed_input.text) != self.speed:
            self.speed_error_img.color = (1, 1, 1, 1)
        else:
            self.speed_error_img.color = (1, 1, 1, 0)
        if int(self.accel_time_input.text) != self.accel_time:
            self.accel_error_img.color = (1, 1, 1, 1)
        else:
            self.accel_error_img.color = (1, 1, 1, 0)
        if int(self.deccel_time_input.text) != self.deccel_time:
            self.deccel_error_img.color = (1, 1, 1, 1)
        else:
            self.deccel_error_img.color = (1, 1, 1, 0)
        if int(self.work_time_input.text) != self.work_time:
            self.work_error_img.color = (1, 1, 1, 1)
        else:
            self.work_error_img.color = (1, 1, 1, 0)

    def set_param(self, register, value):
        if myApp.auto_mode:
            if register == ServoReg.SPEED:
                self.auto_speed = self.speed = value
                self.speed_input.text = str(value)
            elif register == ServoReg.ACCEL_TIME:
                self.auto_accel_time = self.accel_time = value
                self.accel_time_input.text = str(value)
            elif register == ServoReg.DECCEL_TIME:
                self.auto_deccel_time = self.deccel_time = value
                self.deccel_time_input.text = str(value)
        else:
            if register == ServoReg.SPEED:
                self.manual_speed = self.speed = value
                self.speed_input.text = str(value)
            elif register == ServoReg.ACCEL_TIME:
                self.manual_accel_time = self.accel_time = value
                self.accel_time_input.text = str(value)
            elif register == ServoReg.DECCEL_TIME:
                self.manual_deccel_time = self.deccel_time = value
                self.deccel_time_input.text = str(value)

        if register == ServoReg.DECCEL_TIME and self.sync_param_process:
            self.sync_param_process = False
            if self.motor_switch.active:
                self.disable_buttons(False)

        self.check_param_equals()
        self.save_params()

    def servo_sync_params(self, instance):
        self.sync_param_process = True
        self.disable_buttons(True)
        registers = [ServoReg.SPEED, ServoReg.ACCEL_TIME, ServoReg.DECCEL_TIME]
        for register in registers:
            def check_answer(*args, **kwargs):
                try:
                    ans = kwargs['ans']
                    register = kwargs['register']
                    if ans[:7] == ':010302':
                        myApp.root_widget.set_param(register, int(ans[7:11], 16))
                except:
                    pass

            self.motor.get_param(register, check_answer)

    def add_preset_popup(self, instance):
        popup = AddPresetPopup()
        popup.open()

    def add_preset(self, name):
        preset = Preset(name, int(self.speed_input.text), int(self.accel_time_input.text),
                        int(self.deccel_time_input.text), int(self.work_time_input.text))
        if myApp.auto_mode:
            self.auto_presets.append(preset)
        else:
            self.manual_presets.append(preset)
        self.save_presets()
        self.update_presets_dropdown()

    def del_preset(self):
        if self.selected_preset >= 0:
            if myApp.auto_mode:
                del self.auto_presets[self.selected_preset]
            else:
                del self.manual_presets[self.selected_preset]
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
        if myApp.auto_mode:
            preset = self.auto_presets[self.selected_preset]
        else:
            preset = self.manual_presets[self.selected_preset]
        self.preset_button.text = instance.text
        self.speed_input.text = str(preset.speed)
        self.accel_time_input.text = str(preset.accel_time)
        self.deccel_time_input.text = str(preset.deccel_time)
        self.work_time_input.text = str(preset.work_time)
        self.dropdown.dismiss()
        self.check_param_equals()

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
        self.motor.connect(self.com_num, myApp)
        if not self.motor.is_connect:
            pass
        else:
            self.connect_button.text = 'Отключиться'
            self.motor_switch.disabled = False
            self.apply_param_button.disabled = False
            self.sync_params_button.disabled = False
        self.servo_sync_params(None)

    def disconnect(self):
        self.motor.disconnect()
        if not self.motor.is_connect:
            self.connect_button.text = 'Соединиться'
            self.motor_switch.active = False
            self.motor_switch.disabled = True
            self.apply_param_button.disabled = True
            self.sync_params_button.disabled = True
            self.disable_buttons(True)

    def disable_buttons(self, val):
        self.buttons_is_disable = val
        myApp.mode_widget.disable_buttons(val)

    def servo_shange_state(self, instance, value):
        if value:
            def check_motor_is_on(*args, **kwargs):
                ans = kwargs['ans']
                right_ans = kwargs['right_ans']
                if ans == right_ans:
                    myApp.root_widget.disable_buttons(not value)

            self.motor.servo_on(func=check_motor_is_on)
        else:
            self.motor.servo_off()
            self.disable_buttons(not value)

    def servo_set_params(self, instance):
        def apply_param(*args, **kwargs):
            ans = kwargs['ans']
            right_ans = kwargs['right_ans']
            if ans == right_ans:
                register = int(ans[5:9], 16)
                value = int(ans[9:13], 16)
                myApp.root_widget.set_param(register, value)

        speed = int(self.speed_input.text)
        accel_time = int(self.accel_time_input.text)
        deccel_time = int(self.deccel_time_input.text)
        values = [speed, accel_time, deccel_time]
        registers = [ServoReg.SPEED, ServoReg.ACCEL_TIME, ServoReg.DECCEL_TIME]
        self.sync_param_process = True
        self.disable_buttons(True)
        for i, val in enumerate(values):
            try:
                if val < 0:
                    val = 0
                if i == 0 and val == 0:
                    val = 100
                self.motor.set_param(register=registers[i], value=val, func=apply_param)
            except:
                pass
        try:
            self.work_time = int(self.work_time_input.text)
        except:
            pass
        self.save_params()

    def update_presets_dropdown(self):
        self.preset_button.text = 'Пресет'
        self.selected_preset = -1
        self.dropdown.clear_widgets()
        if myApp.auto_mode:
            presets = self.auto_presets
        else:
            presets = self.manual_presets
        for index, preset in enumerate(presets):
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

        self.motor_switch.bind(active=self.servo_shange_state)
        self.motor_switch.disabled = True

        self.dropdown = DropDown()
        self.update_presets_dropdown()
        self.preset_button.bind(on_release=self.dropdown.open)

        self.add_preset_button.bind(on_press=self.add_preset_popup)
        self.del_preset_button.bind(on_press=self.del_preset_btn)

        self.apply_param_button.bind(on_press=self.servo_set_params)
        self.apply_param_button.disabled = True
        self.sync_params_button.bind(on_press=self.servo_sync_params)
        self.sync_params_button.disabled = True


class ServolineMotorApp(App):
    auto_mode = True
    key_right = 275
    key_left = 276

    def keyboard_press(self, *args):
        if not self.auto_mode:
            key_code = args[1]
            if key_code == self.key_right and self.mode_widget.left_button.state != 'down':
                self.mode_widget.right_button.state = 'down'
            elif key_code == self.key_left and self.mode_widget.right_button.state != 'down':
                self.mode_widget.left_button.state = 'down'

    def keyboard_release(self, *args):
        if not self.auto_mode:
            key_code = args[1]
            if key_code == self.key_right:
                self.mode_widget.right_button.state = 'normal'
            elif key_code == self.key_left:
                self.mode_widget.left_button.state = 'normal'

    def change_mode(self, instance):
        self.auto_mode = not self.auto_mode
        self.root_widget.remove_widget(self.mode_widget)
        if self.auto_mode:
            self.build_auto_mode()
            speed = self.root_widget.auto_speed
            accel_time = self.root_widget.auto_accel_time
            deccel_time = self.root_widget.auto_deccel_time
            self.root_widget.work_time_input.disable = False
        else:
            self.build_manual_mode()
            speed = self.root_widget.manual_speed
            accel_time = self.root_widget.manual_accel_time
            deccel_time = self.root_widget.manual_deccel_time
            self.root_widget.work_time_input.disable = True

        self.root_widget.speed_input.text = str(speed)
        self.root_widget.accel_time_input.text = str(accel_time)
        self.root_widget.deccel_time_input.text = str(deccel_time)
        self.root_widget.add_widget(self.mode_widget)
        self.root_widget.servo_set_params(None)
        self.root_widget.update_presets_dropdown()

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

    def __init__(self):
        super().__init__()
        Window.bind(on_key_down=self.keyboard_press)
        Window.bind(on_key_up=self.keyboard_release)


myApp = ServolineMotorApp()

if __name__ == '__main__':
    myApp.run()
