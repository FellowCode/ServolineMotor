def speed_command(value):
    if value >= 0 and value <= 1500:
        return ':01060132' + get_value_hex(value) + get_control_hex(198, value) + '\r\n'

def start_acceleration_command(value):
    if value >= 0 and value <= 5000:
        return ':0106012F' + get_value_hex(value) + get_control_hex(201, value) + '\r\n'

def stop_acceleration_command(value):
    if value >= 0 and value <= 5000:
        return ':01060130' + get_value_hex(value) + get_control_hex(200, value) + '\r\n'

def get_value_hex(value):
    value = hex(value)[2:].upper()
    while len(value) < 4:
        value = '0' + value
    return value

def get_control_hex(shift, value):
    if value < shift+1:
        control_value = shift - value
    else:
        control_value = 255-((value-shift + value//256-1)%256)
    control_value = hex(control_value).upper()[2:]
    while len(control_value)<2:
        control_value = '0'+control_value
    return control_value

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