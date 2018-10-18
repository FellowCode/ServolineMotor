import serial
from commands import *
from threading import Thread
from queue import Queue
import time

q = Queue()

class Command:
    right_func = None
    error_func = None
    def func(self, *args, **kwargs):
        if self.right_func:
            self.right_func(*args, **kwargs)

    def __init__(self, cm, right_ans=None, func=None, error_func=None, register=None):
        self.cm = cm
        self.right_ans = right_ans
        self.error_func = error_func
        self.right_func = func
        self.register = register

    def error(self, *args, **kwargs):
        if self.error_func:
            self.error_func(*args, **kwargs)

class SendCommandThread(Thread):
    work = True

    def __init__(self, ser, app):
        """Инициализация потока"""
        Thread.__init__(self)
        self.ser = ser
        self.app = app

    def run(self):
        while self.work:
            time.sleep(0.03)
            if q.not_empty:
                try:
                    command = q.get()
                    self.ser.write(command.cm.encode('utf-8'))
                    ans = self.ser.read(50).decode('utf-8')[:-2]
                    print(ans)
                    if command.right_ans:
                        right_ans = command.right_ans[:-2]
                    else:
                        right_ans = None
                    command.func(ans=ans, right_ans=right_ans, register=command.register)
                    if command.right_ans and command.right_ans[:-2] != ans:
                        command.error()
                    q.task_done()
                except:
                    self.app.root_widget.error('Потеряно соединение с двигателем')
                    q.empty()


class Modbus:
    is_connect = False

    def connect(self, com_num, app):
        if not self.is_connect:
            try:
                self.ser = serial.Serial('COM' + str(com_num), 57600, timeout=1, parity=serial.PARITY_ODD)
                print(self.ser)
                self.is_connect = True
                self.command_worker = SendCommandThread(self.ser, app)
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

    def send_command(self, cm, right_ans=None, error_func=None):
        command = Command(cm=cm, right_ans=right_ans, error_func=error_func)
        q.put(command)

    def set_param(self, register, value, func=None, error_func=None):
        cm = set_param_command(register, value)
        command = Command(cm=cm, right_ans=cm, func=func, error_func=error_func)
        q.put(command)

    def get_param(self, register, func):
        cm = get_param_command(register)
        command = Command(cm=cm, func=func, register=register)
        q.put(command)

    def JOG_On(self):
        cm = JOG_on_command()
        self.send_command(cm, ':0103020032C8')

    def JOG_Off(self):
        cm = JOG_off_command()
        self.send_command(cm, ':011009000003E3')

    def servo_on(self, func=None):
        cm = servo_on_command()
        command = Command(cm=cm, right_ans=cm, func=func)
        q.put(command)

    def servo_off(self):
        cm = servo_off_command()
        self.send_command(cm, cm)

    def servo_forward_start(self):
        cm = servo_forward_start_command()
        self.send_command(cm, cm)

    def servo_forward_stop(self):
        cm = servo_forward_stop_command()
        self.send_command(cm, cm)

    def servo_reverse_start(self):
        cm = servo_reverse_start_command()
        self.send_command(cm, cm)

    def servo_reverse_stop(self):
        cm = servo_reverse_stop_command()
        self.send_command(cm, cm)