"""
A general class for handling all the properties, communications, and
algorithms of the robot
"""

from autobuggy.microcontroller.comm import *
from autobuggy.microcontroller.data import *
from autobuggy import project


class Robot:
    def __init__(self, sensors, commands, address=None,
                 exclude_addresses=None, filter=None, joystick=None,
                 pipeline=None, capture=None, close_fn=None, log_data=True,
                 log_name=None, log_dir=None):
        # an instance of a filter class. For generic use
        self.filter = filter

        # an instance of BuggyJoystick
        self.joystick = joystick

        # a class that handles all the computer vision algorithms
        self.pipeline = pipeline

        # an instance of Capture. Can be a video or a live feed
        self.capture = capture

        # a function specifying extra closing behavior
        self.close_fn = close_fn

        # Initialize all sensors given in the sensor properties dictionary
        self.sensor_pool = SensorPool()
        self.sensors = {}
        for name, sensor_properties in sensors.items():
            sensor = Sensor(sensor_properties['sensor_id'],
                            name, sensor_properties['update_fn'],
                            sensor_properties['properties'])
            self.sensor_pool.add_sensor(sensor)
            self.sensors[name] = sensor

        # Initialize communications with the micropython board
        self.log_data = log_data
        self.communicator = Communicator(
            self.sensor_pool, address=address,
            exclude_addresses=exclude_addresses, log_data=self.log_data,
            log_name=log_name, log_dir=log_dir)
        if not self.communicator.initialized:
            raise Exception("Communicator not initialized...")

        # Initialize all commands given in the command properties dictionary
        # Commands require a Communicator class and the Communicator class
        # requires a SensorPool class
        self.commands = {}
        for name, command_properties in commands.items():
            if 'command_array' in command_properties:
                command_ids = command_properties['command_array']
                command_range = command_properties['range']
                del command_properties['command_array']
                del command_properties['range']

                command = CommandArray(command_ids, name, command_range,
                                       self.communicator,
                                       **command_properties)
            else:
                command_id = command_properties['command_id']
                command_range = command_properties['range']
                del command_properties['command_id']
                del command_properties['range']

                command = Command(command_id, name, command_range,
                                  self.communicator,
                                  **command_properties)

            self.commands[name] = command

        self.time_start = time.time()

        self.started = False

    def start(self):
        """Initialize all threads (communications, joystick, and capture)"""
        self.communicator.start()
        if self.joystick is not None:
            print("Starting joystick")
            self.joystick.start()
        if self.capture is not None:
            print("Starting capture")
            self.capture.start()

        self.started = True

    def record(self, name, value=None, **values):
        """Log data to the current log file"""
        self.communicator.record(name, value, **values)

    def get_state(self):
        """Return the robot's current state as determined by the filter"""
        if self.filter is not None:
            return self.filter.state
        else:
            return None

    def close(self):
        """All method calls necessary to shutdown the robot cleanly"""

        # stop the capture feed if it was initialized
        if self.capture is not None:
            self.capture.stop()
        time.sleep(0.005)

        # stop the joystick thread if it was initialized
        if self.joystick is not None:
            self.joystick.stop()
        time.sleep(0.005)

        # end communications with the micropython board
        self.communicator.stop()

        # an extra closing behavior as defined by the user
        if self.close_fn is not None:
            self.close_fn()

    def should_stop(self):
        """Check if the robot's threads are still running"""
        if self.communicator.exit_flag:
            return True
        if self.capture is not None and \
                self.capture.stopped:
            return True
        if self.joystick is not None and \
                self.joystick.exit_flag:
            return True

        return False

    def run(self):
        if not self.started:
            self.start()
        try:
            while True:
                self.main()
                if self.should_stop():
                    break
        except:
            traceback.print_exc()
        finally:
            self.close()

    def main(self):
        pass