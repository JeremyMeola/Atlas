import sys

sys.path.insert(0, '../')

from microcontroller.data import *
from microcontroller.logger import get_map
from navigation.buggypi_filter import BuggyPiFilter


class Robot:
    def __init__(self, properties):
        #       ----- initial state -----
        self.initial_long = self.get_property(
            properties, 'initial_long', ('checkpoint', 0))
        self.initial_lat = self.get_property(
            properties, 'initial_lat', ('checkpoint', 0))
        self.initial_heading = self.get_property(
            properties, 'initial_heading', 0.0)

        #       ----- physical properties -----
        self.counts_per_rotation = self.get_property(
            properties, 'counts_per_rotation', ValueError)

        self.wheel_radius = self.get_property(
            properties, 'wheel_radius', ValueError)

        self.front_back_dist = self.get_property(
            properties, 'front_back_dist', ValueError)

        self.max_speed = self.get_property(
            properties, 'max_speed', ValueError)

        self.left_angle_limit = self.get_property(
            properties, 'left_angle_limit', ValueError)

        self.right_angle_limit = self.get_property(
            properties, 'right_angle_limit', ValueError)

        self.left_servo_limit = self.get_property(
            properties, 'left_servo_limit', ValueError)

        self.right_servo_limit = self.get_property(
            properties, 'right_servo_limit', ValueError)

        #       ----- map -----
        self.map_file = self.get_property(properties, 'map_file')
        self.map_dir = self.get_property(properties, 'map_dir')

        #       ----- checkpoints -----
        self.checkpoints_file = self.get_property(
            properties, 'checkpoints_file', "checkpoints.txt")
        self.checkpoints_dir = self.get_property(
            properties, 'checkpoints_dir', ":maps")

        #
        # ----- initialize internal properties ----- #
        #

        #       ----- checkpoints -----
        self.checkpoint_num = 0
        self.checkpoints = get_map(self.checkpoints_file, self.checkpoints_dir)

        # ----- Map -----
        self.map = get_map(self.map_file, self.map_dir)

        #       ----- Filter -----
        if self.initial_long[0] == 'checkpoint':
            self.initial_long = self.checkpoints[self.initial_long[1]][0]
        elif self.initial_long[0] == 'map':
            self.initial_long = self.map[self.initial_long[1]][0]
        elif self.initial_long == 'gps':
            pass  # wait for later
        elif type(self.initial_long) == float:
            pass  # already assigned 
        else:
            raise ValueError("Please provide an initial longitude")

        if self.initial_lat[0] == 'checkpoint':
            self.initial_lat = self.checkpoints[self.initial_lat[1]][1]
        elif self.initial_lat[0] == 'map':
            self.initial_lat = self.map[self.initial_lat[1]][1]
        elif self.initial_lat == 'gps':
            pass  # wait for later
        elif type(self.initial_lat) == float:
            pass  # already assigned 
        else:
            raise ValueError("Please provide an initial latitude")

        if self.initial_long == 'gps':
            self.initial_long = 0
        if self.initial_lat == 'gps':
            self.initial_lat = 0

        self.filter = BuggyPiFilter(
            self.initial_long, self.initial_lat, self.initial_heading,
            self.counts_per_rotation, self.wheel_radius,
            self.front_back_dist, self.max_speed,
            self.left_angle_limit, self.right_angle_limit,
            self.left_servo_limit, self.right_servo_limit
        )

        #       ----- Start joystick and comm threads -----

        self.time_start = time.time()
        self.running = True

    def get_state(self):
        return self.filter.state

    def get_property(self, properties, key, default=None):
        if key in properties:
            if properties[key] is None:
                return default
            else:
                return properties[key]
        elif default is ValueError:
            raise ValueError("Please provide value for property " + key)
        else:
            return default

    @staticmethod
    def log_folder():
        month = time.strftime("%b")
        day = time.strftime("%d")
        year = time.strftime("%Y")
        return "%s %s %s" % (month, day, year)

    def angle_to_servo(self, angle):
        return int(((self.left_servo_limit - self.right_servo_limit) /
                    (self.left_angle_limit - self.right_angle_limit) *
                    (angle - self.right_angle_limit) + self.right_servo_limit))

    def __str__(self):
        return "(%0.6f, %0.6f, %0.4f)\t(%0.4f, %0.4f)" % (
            self.get_state()["x"], self.get_state()["y"], self.get_state()["angle"],
            self.get_state()["vx"], self.get_state()["vy"])
