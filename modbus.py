import serial
from commands import *
from threading import Thread
from queue import Queue
import time

q = Queue()

class Command:
    def __init__(self, cm, right_ans, error_func):
        self.cm = cm
        self.right_ans = right_ans
        self.error_func = error_func

    def error(self):
        if self.error_func:
            self.error_func()

class SendCommandThread(Thread):
    work = True

    def __init__(self, ser):
        """Инициализация потока"""
        Thread.__init__(self)
        self.ser = ser

    def run(self):
        while self.work:
            time.sleep(0.2)
            if q.not_empty:
                command = q.get()
                self.ser.write(command.cm.encode('utf-8'))
                ans = self.ser.read(100).decode('utf-8')[:-2]
                if command.right_ans != ans:
                    command.error_func()
                q.task_done()


class Modbus:
    is_connect = False

    def connect(self, com_num):
        if not self.is_connect:
            try:
                self.ser = serial.Serial('COM' + str(com_num), 57600, timeout=1, parity=serial.PARITY_ODD)
                print(self.ser)
                self.is_connect = True
                self.command_worker = SendCommandThread(self.ser)
                self.command_worker.start()
                self.JOG_On()
                if self.is_connect:
                    self.servo_off()
            except:
                self.is_connect = False

    def disconnect(self):
        if self.is_connect:
            self.servo_off()
            self.JOG_Off()
            time.sleep(0.4)
            self.command_worker.work = False
            self.ser.close()
            self.is_connect = False

    def send_command(self, cm, right_ans, error_func=None):
        command = Command(cm, right_ans, error_func)
        q.put(command)

    def set_param(self, register, value, error_func=None):
        cm = set_param_command(register, value)
        return self.send_command(cm, cm, error_func)

    def JOG_On(self):
        cm = JOG_on_command()
        return self.send_command(cm, ':0103020032C8')

    def JOG_Off(self):
        cm = JOG_off_command()
        return self.send_command(cm, ':011009000003E3')

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