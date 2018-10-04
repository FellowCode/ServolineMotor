import serial
from commands import *
import time

ser = serial.Serial('COM6', 9600, timeout=1, parity=serial.PARITY_ODD)
print(ser)

#ser.write(':010307120001E2\r\n'.encode('utf-8'))
ser.write(speed_command(50).encode('utf-8'))
print('send', speed_command(50))
print(repr(ser.read(1000)))

#:0106012F0BB806
#
#ser.write(start_acceleration_command(3050).encode('utf-8'))
#print('send', start_acceleration_command(3050))
#print(repr(ser.read(1000)))

#:010601300BB805
#
#ser.write(stop_acceleration_command(3050).encode('utf-8'))
#print('send', stop_acceleration_command(3050))
#print(repr(ser.read(1000)))

ser.write(JOG_on_command().encode('utf-8'))
print('send', 'JOG On')
print(repr(ser.read(1000)))

ser.write(servo_off_command().encode('utf-8'))
print('send', 'Servo Off')
print(repr(ser.read(1000)))

time.sleep(1)

ser.write(servo_on_command().encode('utf-8'))
print('send', 'Servo On')
print(repr(ser.read(1000)))

time.sleep(1)
ser.write(servo_forward_start_command().encode('utf-8'))
print('send', 'Start forward')
print(repr(ser.read(1000)))

time.sleep(10)

ser.write(servo_forward_stop_command().encode('utf-8'))
print('send', 'Stop forward')
print(repr(ser.read(1000)))

time.sleep(1)

ser.write(servo_off_command().encode('utf-8'))
print('send', 'Servo Off')
print(repr(ser.read(1000)))

ser.write(JOG_off_command().encode('utf-8'))
print('send', 'JOG Off')
print(repr(ser.read(1000)))