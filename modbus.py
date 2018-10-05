import serial
from commands import *
import time

class Modbus:
    is_connect = False
    def connect(self, com_num):
        try:
            self.ser = serial.Serial('COM' + str(com_num), 9600, timeout=1, parity=serial.PARITY_ODD)
            self.is_connect = True
        except:
            self.is_connect = False

    def send_command(self, cm, right_ans):
        self.ser.write(cm.encode('utf-8'))
        ans = self.ser.read(1000).decode('utf-8')
        if ans is right_ans:
            return True
        else:
            return False

    def set_speed(self, value):
        cm = speed_command(value)
        return self.send_command(cm, cm)

    def set_acceleration_time(self, value):
        cm = start_acceleration_command(value)
        return self.send_command(cm, cm)

    def set_decceleration_time(self, value):
        cm = stop_acceleration_command(value)
        return self.send_command(cm, cm)

    def JOG_On(self):
        cm = JOG_on_command()
        return self.send_command(cm, '???')

    def JOG_Off(self):
        cm = JOG_off_command()
        return self.send_command(cm, '???')

    def servo_on(self):
        cm = servo_on_command()
        return self.send_command(cm, cm)

    def servo_off(self):
        cm = servo_off_command()
        return self.send_command(cm, cm)

    def servo_forward_start(self):
        cm = servo_forward_start_command()
        return self.send_command(cm, cm)

    def servo_forward_stop(self):
        cm = servo_forward_stop_command()
        return self.send_command(cm, cm)

    def servo_reverse_start(self):
        cm = servo_reverse_start_command()
        return self.send_command(cm, cm)

    def servo_reverse_stop(self):
        cm = servo_reverse_stop_command()
        return self.send_command(cm, cm)