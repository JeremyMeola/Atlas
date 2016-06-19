
from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import sys
import pygame
import os
import traceback

sys.path.insert(0, "../")

from microcontroller.data import *
from microcontroller.dashboard import *
from manual.wiiu_joystick import WiiUJoystick
# from manual.gc_joystick import GCjoystick


def stick_to_servo(x):
    return int(-math.atan2(x, 1) * 180 / (math.pi * 1.85))


def main():
    camera = PiCamera()
    camera.resolution = (640, 480)
    camera.framerate = 32
    rawCapture = PiRGBArray(camera, size=(640, 480))

    time.sleep(0.1)

    leds = [Command(command_id, "led " + str(command_id), (0, 2)) for command_id in range(4)]
    servo = Command(4, 'servo', (-90, 90))
    motors = Command(5, 'motors', (-100, 100))

    counts = Sensor(0, 'encoder')
    gps = Sensor(1, 'gps', ['lat', 'long', 'altitude', 'found'])
    yaw = Sensor(2, 'imu')
    altitude = Sensor(3, 'altitude')
    checkpoint_num = 0

    pygame.init()
    pygame.joystick.init()
    joystick = WiiUJoystick()

    joystick.start()
    start(log_data=False, soft_reboot=False)    

    try:
        for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            # grab the raw NumPy array representing the image, then initialize the timestamp
            # and occupied/unoccupied text
            image = frame.array

            # show the frame
            cv2.imshow("Frame", image)
            key = cv2.waitKey(1) & 0xFF

            # clear the stream in preparation for the next frame
            rawCapture.truncate(0)

            # if the `q` key was pressed, break from the loop
            if key == ord("q"):
                print("Aborted by user")
                break

            if joystick.get_button('B'):
                print("Aborted by user")
                break

            servo.set(stick_to_servo(joystick.get_axis("left x")))
            value = -joystick.get_axis("left y")
            if value != 0 and abs(value) < 0.8:
                value = 0.8 * ((value > 0) - (value < 0))
            motors.set(int(value * 100))

##            if joystick.dpad[1] == 1:
##                leds[0].set(1)
##            else:
##                leds[0].set(0)
##
##            if joystick.dpad[1] == -1:
##                leds[1].set(1)
##            else:
##                leds[1].set(0)
##
##            if joystick.dpad[0] == 1:
##                leds[2].set(1)
##            else:
##                leds[2].set(1)
##
##            if joystick.dpad[0] == -1:
##                leds[3].set(1)
##            else:
##                leds[3].set(0)
            print("%0.4f, %5.0i, (%0.6f, %0.6f, %0.6f, %i), motors: %3.0i, servo: %3.0i, %3.6fm    " % (yaw.get(), counts.get(),
                  gps.get('lat'), gps.get('long'), gps.get('altitude'), gps.get('found'), motors.get(), servo.get(), altitude.get()), end='\r')

            if joystick.get_button('A'):  # TODO: switch to a event based system (becomes false after access)
                record('checkpoint reached!', checkpoint_num)
                checkpoint_num += 1
    except:
        trackback.print_exc()
        
    joystick.stop()
    stop()

if __name__ == '__main__':
    main()
