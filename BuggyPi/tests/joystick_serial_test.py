
import sys
import math

sys.path.insert(0, "../")

from microcontroller.data import *
from microcontroller.dashboard import *
from manual.wiiu_joystick import WiiUJoystick


def stick_to_servo(x):
    return int(-math.atan2(x, 1) * 180 / (math.pi * 1.85))

def main():
    leds = [Command(command_id, (0, 2)) for command_id in range(4)]
    servo = Command(4, (-90, 90))
    motors = Command(5, (-100, 100))

    encoder = Sensor(0, 'counts')
    imu = Sensor(2, 'yaw')

    joystick = WiiUJoystick()

    joystick.start()
    start()

##    reset(True)
    
    try:
        while True:
            if joystick.get_button('B'):
                print("Aborted by user")
                break

            servo.set(stick_to_servo(joystick.get_axis("left x")))
            motors.set(int(-joystick.get_axis("right y") * 100))
            
            if joystick.dpad[1] == 1:
                leds[0].set(2)
            if joystick.dpad[1] == -1:
                leds[1].set(2)
            if joystick.dpad[0] == 1:
                leds[2].set(2)
            if joystick.dpad[0] == -1:
                leds[3].set(2)

            print("%0.4f, %5.0i" % (imu.get('yaw'), encoder.get('counts')),end='\r')
    except KeyboardInterrupt:
        stop()


if __name__ == '__main__':
    main()
