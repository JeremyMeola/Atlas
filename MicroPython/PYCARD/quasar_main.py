
from objects import *
from comm import Communicator

for _ in range(15):
    pyb.LED(3).toggle()
    pyb.delay(50)
pyb.LED(3).on()

leds = [LEDcommand(index, index + 1) for index in range(3)]
blue_led = BlueLEDcommand(3)

gps = GPS(1, 6, 4)
imu = IMU(2, 2, 11)

communicator = Communicator(*leds, blue_led, uart_bus=1)

# sensor_updated = False

while True:
    communicator.read_command()

    if imu.recved_data():
        # sensor_updated = True
        communicator.write_packet(imu)

    if gps.recved_data():
        # sensor_updated = True
        communicator.write_packet(gps)
        pyb.LED(3).toggle()

    # if sensor_updated:
    #    sensor_updated = False
    #    print("%0.5f, %0.6f, %0.6f" % (
    #        imu.data[0], gps.data[0], gps.data[1]), end='\r')

    pyb.delay(1)

    if communicator.should_reset():
        gps.reset()
        imu.reset()

        communicator.write_packet(gps)
        communicator.write_packet(imu)