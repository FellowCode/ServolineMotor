import kivy
from modbus import Modbus

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout

from serial.tools import list_ports

from kivy.uix.dropdown import DropDown
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.uix.popup import Popup

from kivy.config import Config

window_height = 320
window_width = 400



Config.set('graphics', 'resizable', 0)
Config.set('graphics', 'width', window_width)
Config.set('graphics', 'height', window_height)
Config.write()


class BaseLabel(Label):
    def __init__(self, text):
        super().__init__()
        self.size_hint = (None, None)
        self.width = 40
        self.height = 20
        self.font_size = '14sp'
        self.text = text

class ParamLabel(BaseLabel):
    def __init__(self, text):
        super().__init__(text)
        self.text_size = (200, 20)
        self.width = 120
        self.halign = 'right'

class ParamInput(TextInput):
    def __init__(self):
        super().__init__()
        self.size_hint = (None, None)
        self.width = 70
        self.height = 20
        self.font_size = '12sp'
        self.line_height = 20
        self.multiline = False
        self.padding = [6, 2]

class BasePopup(Popup):
    def __init__(self, title):
        super().__init__()
        self.title = title
        self.size_hint = (None, None)
        self.size = (150, 70)


class ServolineMotorApp(App):
    auto_mode = True
    fl_mode_manual = FloatLayout()
    fl_mode_auto = FloatLayout()

    disable_buttons = False

    com_num = 1
    motor = Modbus()

    speed = 0
    accel_time = 0
    deccel_time = 0
    work_time = 0

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
            self.com_num = int(value)
        except:
            instance.text = value[:-1]

        if len(instance.text)>2:
            instance.text = value[:-1]

    def change_connect(self, instance):
        if not self.motor.is_connect:
            self.connect()
        else:
            self.disconnect()

    def connect(self):
        self.motor.connect(self.com_num)
        if not self.motor.is_connect:
            popup = BasePopup('Error')
            bl = BoxLayout(orientation='vertical')
            bl.add_widget(Label(text='Connection error'))
            bl.add_widget(Button(text='Закрыть', on_press=popup.dismiss))
            popup.content = bl
            popup.open()
        else:
            self.connect_button.text = 'Отключиться'
            self.change_disable_buttons()

    def disconnect(self):
        self.motor.disconnect()
        if not self.motor.is_connect:
            self.connect_button.text = 'Соединиться'
            self.change_disable_buttons()


    def change_disable_buttons(self):
        dis = self.disable_buttons = not self.disable_buttons
        self.motor_switch.disabled = dis
        self.apply_param_button.disabled = dis
        try:
            self.start_button.disabled = dis
            self.stop_button.disabled = dis
            self.mode_button1.disabled = dis
        except:
            self.left_button.disabled = dis
            self.right_button.disabled = dis
            self.mode_button2.disabled = dis

    def change_motor_state(self, instance, value):
        if value:
            success = self.motor.servo_on()
        else:
            success = self.motor.servo_off()
        if not success:
            self.motor_switch.active = not value

    def params_changed(self, instance, value):
        try:
            val = int(value)
        except:
            instance.text = value[:-1]

        if len(instance.text)>4:
            instance.text = value[:-1]

    def set_params(self, instance):
        pass

    def build_auto_mode(self):
        fl_mode = FloatLayout()
        fl_mode.size_hint = (1, None)
        fl_mode.height = window_height - 255
        fl_mode.pos = (0, window_height - 255)

        start_button = Button()
        start_button.size_hint = (None, None)
        start_button.text = 'Старт'
        start_button.size = (90, 30)
        start_button.pos = (40, window_height - 265)
        self.start_button = start_button

        stop_button = Button()
        stop_button.size_hint = (None, None)
        stop_button.text = 'Стоп'
        stop_button.size = (90, 30)
        stop_button.pos = (140, window_height - 265)
        self.stop_button = stop_button

        mode_button = Button()
        mode_button.size_hint = (None, None)
        mode_button.text = 'Ручной режим'
        mode_button.size = (120, 30)
        mode_button.pos = (240, window_height - 265)
        mode_button.bind(on_press=self.change_mode)
        self.mode_button1 = mode_button

        fl_mode.add_widget(self.start_button)
        fl_mode.add_widget(self.stop_button)
        fl_mode.add_widget(self.mode_button1)

        self.fl_mode_auto.add_widget(fl_mode)

    def build_manual_mode(self):
        fl_mode = FloatLayout()
        fl_mode.size_hint = (1, None)
        fl_mode.height = window_height - 255
        fl_mode.pos = (0, window_height - 255)

        left_button = Button()
        left_button.size_hint = (None, None)
        left_button.text = '<--'
        left_button.size = (90, 30)
        left_button.pos = (40, window_height - 265)
        self.left_button = left_button

        right_button = Button()
        right_button.size_hint = (None, None)
        right_button.text = '-->'
        right_button.size = (90, 30)
        right_button.pos = (140, window_height - 265)
        self.right_button = right_button

        mode_button = Button()
        mode_button.size_hint = (None, None)
        mode_button.text = 'Авто режим'
        mode_button.size = (120, 30)
        mode_button.pos = (240, window_height - 265)
        mode_button.bind(on_press=self.change_mode)
        self.mode_button2 = mode_button

        fl_mode.add_widget(self.left_button)
        fl_mode.add_widget(self.right_button)
        fl_mode.add_widget(self.mode_button2)

        self.fl_mode_manual.add_widget(fl_mode)

    def build(self):
        floatlayout = FloatLayout()

        com_input = ParamInput()
        com_input.width = 30
        com_input.pos = (60, window_height-30)
        com_input.bind(text=self.com_changed)

        com_label = BaseLabel('COM')
        com_label.pos = (10, window_height-30)

        connect_button = Button()
        connect_button.size_hint = (None, None)
        connect_button.size = (90, 25)
        connect_button.text = 'Соединиться'
        connect_button.font_size = '12sp'
        connect_button.pos = (100, window_height-33)
        connect_button.padding = [5, 2]
        connect_button.bind(on_press=self.change_connect)
        self.connect_button = connect_button

        motor_state_label = BaseLabel('Motor')
        motor_state_label.pos = (window_width-150, window_height-30)

        motor_switch = Switch()
        motor_switch.active = False
        motor_switch.size_hint = (None, None)
        motor_switch.pos = (300, window_height-70)
        motor_switch.bind(active=self.change_motor_state)
        self.motor_switch = motor_switch

        speed_label = ParamLabel('Скорость (об/мин)')
        speed_label.pos = (30, window_height-80)

        speed_input = ParamInput()
        speed_input.pos = (210, window_height-80)

        acceleration_time_label = ParamLabel('Время ускорения (мс)')
        acceleration_time_label.pos = (30, window_height-110)

        acceleration_time_input = ParamInput()
        acceleration_time_input.pos = (210, window_height-110)

        decceleration_time_label = ParamLabel('Время торможения (мс)')
        decceleration_time_label.pos = (30, window_height-140)

        decceleration_time_input = ParamInput()
        decceleration_time_input.pos = (210, window_height-140)

        work_time_label = ParamLabel('Время работы (мс)')
        work_time_label.pos = (30, window_height-170)

        work_time_input = ParamInput()
        work_time_input.pos = (210, window_height-170)

        apply_param_button = Button()
        apply_param_button.text = 'Применить параметры'
        apply_param_button.size_hint = (.8, None)
        apply_param_button.height = 30
        apply_param_button.pos = (200 - 400*.8*.5, window_height - 220)
        self.apply_param_button = apply_param_button

        floatlayout.add_widget(com_input)
        floatlayout.add_widget(com_label)
        floatlayout.add_widget(motor_state_label)
        floatlayout.add_widget(self.motor_switch)
        floatlayout.add_widget(speed_label)
        floatlayout.add_widget(acceleration_time_label)
        floatlayout.add_widget(decceleration_time_label)
        floatlayout.add_widget(work_time_label)

        floatlayout.add_widget(speed_input)
        floatlayout.add_widget(acceleration_time_input)
        floatlayout.add_widget(decceleration_time_input)
        floatlayout.add_widget(work_time_input)

        floatlayout.add_widget(self.connect_button)
        floatlayout.add_widget(self.apply_param_button)

        self.build_auto_mode()
        floatlayout.add_widget(self.fl_mode_auto)
        floatlayout.add_widget(self.fl_mode_manual)
        # return a Button() as a root widget

        self.change_disable_buttons()

        return floatlayout


if __name__ == '__main__':
    ServolineMotorApp().run()