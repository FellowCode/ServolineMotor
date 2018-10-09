def get_LRC(message):
    if message[0] == ':':
        message = message[1:]
    lrc = 0
    while len(message)>0:
        hexi = message[:2]
        message = message[2:]
        lrc += int(hexi, 16)
        if lrc>int('ff', 16):
            lrc -= int('ff', 16) + 1
    lrc = hex(int('ff', 16) - lrc + 1).upper()[2:]
    if len(lrc)==1:
        lrc = '0' + lrc
    elif len(lrc)==3:
        lrc = lrc[1:]
    return lrc

def get_value_hex(value):
    value = hex(value)[2:].upper()
    while len(value) < 4:
        value = '0' + value
    return value

def set_param_command(register, value):
    msg = ':0106' + get_value_hex(register) + get_value_hex(value)
    return msg + get_LRC(msg) + '\r\n'

def JOG_on_command():
    return ':010301320001C8\r\n'

def JOG_off_command():
    return ':01100900000306000000000000DD\r\n'

def servo_off_command():
    return ':010609000000F0\r\n'

def servo_on_command():
    return ':010609000001EF\r\n'

def servo_forward_start_command():
    return ':010609010001EE\r\n'

def servo_forward_stop_command():
    return ':010609010000EF\r\n'

def servo_reverse_start_command():
    return ':010609020001ED\r\n'

def servo_reverse_stop_command():
    return ':010609020000EE\r\n'