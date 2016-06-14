"""
Written by Ben Warwick

data.py, written for RoboQuasar3.0
Version 3/6/2016
=========

Handles sensor data sorting, the command queue, and raw data storage.

Classes:
    SensorPool - parses and sorts the incoming packet by giving it to the
        correct sensor
    SerialObject - Internal. The superclass of Sensor and Command.
    Sensor - An object containing data read from the micro-controller with
        the matching sensor ID
    Command - An object that allows data to be sent to the micro-controller

Functions (use with python -i data.py):
    try_sensor - given a list of property names (strings), this function
        allows you to test what the output of your sensor would be
    try_command - this functions returns the packet that
        would be written to serial given typical inputs
"""

import math
import random
import struct
import time
from collections import OrderedDict
from sys import maxsize as MAXINT


class SensorPool(object):
    def __init__(self):
        """
        Constructor for SensorPool. Initializes sensor pool dictionary as empty

        :return: SensorPool object
        """

        self.invalid_packets = 0

        self.sensors = {}

    def add_sensor(self, sensor):
        """
        add sensors to self.sensors with non-repeating sensor IDs

        :param sensor: A sensor object
        :return: None
        """
        if sensor.object_id in list(self.sensors.keys()):
            raise Exception(
                "Sensor ID already taken: " + str(sensor.object_id))
        elif not isinstance(sensor, Sensor):
            raise TypeError(
                "Parameter is not of the type sensor: " + repr(sensor))
        else:
            self.sensors[sensor.object_id] = sensor

    def is_packet(self, packet):
        """
        Makes sure the packet is the right format and was safely delivered.
        A packet must be 5 characters or more, contain some or all of the
        following characters:
            0 1 2 3 4 5 6 7 8 9 a b c e d f i u \t
        has a \t character at index 2, and must only have the type identifying
        characters f, i, b, or u at index 3

        If any of these conditions are invalid, the packet is invalid

        :param packet: A string that may or may not be a valid packet
        :return: True or False depending on if the packet is valid
        """

        if len(packet) < 5:
            return False
        for c in packet:
            if c.lower() not in '0123456789abcedfiu\t':
                return False
        if packet[2] != '\t' and packet[3] not in 'fibu':
            return False

        return True

    def update(self, packet):
        """
        updates the sensors' data when called and, if correct, parses and
        replaces the old sensor data

        :param packet: A string that may or may not be a valid packet
        :return: None
        """

        packet = packet.decode('ascii')
        # print(self.is_packet(packet), packet)
        if self.is_packet(packet):
            sensor_id, data = int(packet[0:2], 16), packet[3:]
            if sensor_id in list(self.sensors.keys()):
                sensor = self.sensors[sensor_id]

                sensor._new_data_received = True
                sensor.sleep_time = time.time() - sensor.prev_time
                sensor.prev_time = time.time()

                sensor.parse(data)
                sensor.current_packet = packet

                return self.invalid_packets, sensor
            else:
                print("Sensor ID not found")
        else:
            print("Packet malformed")

        print("Invalid packet: " + repr(packet))
        self.invalid_packets += 1
        return self.invalid_packets, None


sensor_pool = SensorPool()
communicator = None


def try_sensor(sensor_id, properties):
    global sensor_pool
    # sensor_id = max(sensor_pool.sensors.keys()) + 1
    sensor_pool.sensors = {}
    exp_sensor = Sensor(sensor_id, 'exp_sensor', properties)
    if type(properties) is not list or type(properties) is not tuple:
        properties = [properties]

    packet = ""
    for _ in properties:
        data_type = random.choice(['i', 'u', 'f', 'b'])
        if data_type == 'u' or data_type == 'i':
            int_size = random.choice([8, 16, 32, 64])
            data = random.randint(0, 2 << (int_size - 1) - 1)
            packet += "%s%x\t" % (data_type, data)
        elif data_type == 'f':
            data = random.random() * 10000
            packet += "%s%0.8x\t" % (data_type,
                                     struct.unpack('<I',
                                                   struct.pack('<f', data))[0])
        elif data_type == 'b':
            data = random.choice([True, False])
            if data is True:
                data = random.randint(1, 15)
            else:
                data = 0
            packet += "%s%x\t" % (data_type, data)

    exp_sensor.parse(packet[:-1])

    return exp_sensor


def try_command(command_id, data_range, data=None):
    exp_command = Command(command_id, data_range)
    if data is None:
        data = random.randint(exp_command.range[0], exp_command.range[1])
        print("data:", data)

    exp_command.property_set(data)
    return exp_command.get_packet()


class SerialObject(object):
    def __init__(self, object_id, name):
        """
        Constructor for SerialObject.
        Takes a list of strings (properties) and creates an internal dictionary
        in which data will be stored.

        :param object_id: The unique SerialObject identifier. Used for matching
            serial packets to Sensors or allowing micro-controllers to identify
            Commands.
        :param properties: A list of strings containing the properties of the
            object
        :return: SerialObject
        """

        self.sleep_time = 0.0
        self.prev_time = time.time()

        self.object_id = object_id
        self.current_packet = ""

        self.name = name

        assert (type(object_id) == int)


class Sensor(SerialObject):
    def __init__(self, sensor_id, name, properties):
        """
        Constructor for Sensor. Inherits from SerialObject.
        Adds self to sensor_pool (a module internal object)

        :param sensor_id: The unique Sensor identifier. Used for matching
            serial packets to Sensors or allowing micro-controllers to identify
            Commands.
        :param properties: A list of strings containing the properties of the
            object
        :return: Sensor
        """
        super().__init__(sensor_id, name)
        self._new_data_received = False

        if type(properties) == str:
            properties = [properties]
        elif type(properties) != list:
            properties = list(properties)
        self._properties = self.init_properties(properties)

        sensor_pool.add_sensor(self)

    @staticmethod
    def init_properties(properties):
        dict_props = OrderedDict()
        for props in properties:
            dict_props[props] = 0

        return dict_props

    def __repr__(self):
        str_formats = str(self._properties)[1:-1]
        return "%s(%s, %s)" % (self.__class__.__name__, self.object_id,
                               str_formats)

    def get(self, item):
        return self._properties[item]

    def received(self):
        if self._new_data_received:
            self._new_data_received = False
            return True
        else:
            return False

    @staticmethod
    def format_hex(hex_string, data_format):
        """
        Formats each hex string according to what data format was given.
        f = float
        b = bool
        u = unsigned int
        i = int

        :param hex_string: A string of hex characters
        :param data_format: A string containing a data type format
        :return: a float, bool, or int depending on the input data type
        """
        if data_format == 'b':
            return bool(int(hex_string, 16))

        elif data_format == 'u':
            return int(hex_string, 16)

        elif data_format == 'i':
            bin_length = len(hex_string) * 4
            raw_int = int(hex_string, 16)
            if (raw_int >> (bin_length - 1)) == 1:
                raw_int -= 2 << (bin_length - 1)
            return int(raw_int)

        elif data_format == 'f':
            if len(hex_string) == 8:
                return struct.unpack('!f', bytes.fromhex(hex_string))[0]
            else:
                return None

        elif data_format == 'd':
            if len(hex_string) == 8:
                return struct.unpack('!d', bytes.fromhex(hex_string))[0]
            else:
                return None

        else:
            # raise ValueError("Invalid data type: %s", str(data_format))
            return None

    def parse(self, data_string):
        """
        a function to parse data, formatted into hex strings

        Assuming the sensor id and carriage return has been removed from the
        packet since SensorPool has already sorted the data to the appropriate
        sensor.

        :param data_string: A string of hex characters and data type identifiers
        :return: None
        """

        raw_data = data_string.split("\t")
        for index, key in enumerate(self._properties.keys()):
            if index < len(raw_data):
                data_type, raw_datum = raw_data[index][0], raw_data[index][1:]
                new_datum = self.format_hex(raw_datum, data_type)
                if new_datum is not None:
                    self._properties[key] = new_datum

    def __str__(self):
        to_string = "["
        for key, value in self._properties.items():
            to_string += "(%s: %s),\t" % (key, value)

        return to_string[:-2] + "]"


class Command(SerialObject):
    used_ids = []

    def __init__(self, command_id, name, data_range, bound=False, initial=None):
        """
        Constructor for Command. Inherits from SerialObject.

        :param command_id: The unique Command identifier. Allows
            micro-controllers to identify Commands.
        :param data_range: The range of values that the command can send. This
            determines the data type and size. It doesn't matter if the smaller
            value is first or second.
        :param bound: The value bound type. If True and a value outside
            data_range is given, it will be truncated to that bound, if False
            and a value outside data_range is given, it will wrap around to the
            appropriate value (kind of like overflow or modulo)
        :return: Command object
        """
        self.data_type, self.data_len, self.range = self.get_type_size(
            data_range)
        super().__init__(command_id, name)

        self.packet_info = "%s\t%s\t" % (self.to_hex(self.object_id, 2),
                                         self.to_hex(self.data_len, 2))
        self.bound = bound

        self.value = initial

        if command_id in Command.used_ids:
            raise ValueError("Command ID already in use:", command_id)
        else:
            Command.used_ids.append(command_id)

    def get(self):
        return self.value

    def set(self, value):
        """
        Commands values to serial from the microcontroller to act upon

        :param key: A string with the name of the property
        :param value: A number to send via the command object
        :return: None
        """

        global communicator
        self.property_set(value)

        current_time = time.time()

        if communicator.log_data:
            communicator.log.enq(self.name, self.value)
        communicator.put(self.get_packet())
        time.sleep(0.004)

        self.prev_time = current_time

    @staticmethod
    def wrap(num, lower, upper):
        while num > upper:
            num -= abs(upper - lower)
        while num < lower:
            num += abs(upper - lower)
        return num

    def property_set(self, value):
        if self.bound:  # bound by self.data_range
            if value > self.range[1]:
                value = self.range[1]
            elif value < self.range[0]:
                value = self.range[0]
        else:  # Wraps out of bound value to self.data_range (modulo)
            value = self.wrap(value, self.range[0], self.range[1])

        self.value = value

    @staticmethod
    def get_data_size(data_range):
        """
        Gets the number of digits of a hexidecimal number

        :param data_range: The range of values as supplied by the constructor
        :return: Number of digits of the input
        """
        length = abs(data_range[1] - data_range[0])

        if length == 0:
            return 8
        else:
            int_length = int(math.log(length, 16)) + 1
            return int_length

    @staticmethod
    def get_type_size(data_range):
        """
        Get the data type of the command based on the command range

        :param data_range: The range of values as supplied by the constructor
        :return: The data type, the data length, and the data range
            (this method swaps the values if the larger value comes first)
        """
        assert len(data_range) == 2
        assert type(data_range[0]) == type(data_range[1])
        if data_range[0] > data_range[1]:
            data_range = (data_range[1], data_range[0])

        if type(data_range[0]) == int:
            if data_range[0] < 0 or data_range[1] < 0:
                data_type = 'i'
            else:
                data_type = 'u'
            data_len = Command.get_data_size(data_range)
        elif type(data_range[0]) == bool:
            data_type = 'b'
            data_len = Command.get_data_size(data_range)
        elif type(data_range[0]) == float:
            data_type = 'f'
            data_len = 64
        else:
            raise ValueError("Range invalid. Invalid data type: %s",
                             str(data_range))
        return data_type, data_len, data_range

    @staticmethod
    def to_hex(decimal, length):
        hex_format = "0.%sx" % length
        return ("%" + hex_format) % decimal

    def format_data(self, data):
        """
        formats data for sending over serial

        :param data: A number that matches the command's data type (exception:
            you may supply integers for booleans. They will be interpreted
            according to python's bool() function)
        :return: A hex string containing the formatted number
        """

        if self.data_type == 'b':
            assert (type(data) == bool or type(data) == int)
            return str(int(bool(data)))

        elif self.data_type == 'u':
            assert (type(data) == int)
            data %= MAXINT
            return self.to_hex(data, self.data_len)

        elif self.data_type == 'i':
            assert (type(data) == int)
            if data < 0:
                data += (2 << (self.data_len * 4 - 1))
            data %= MAXINT
            return self.to_hex(data, self.data_len)

        elif self.data_type == 'f':
            assert (type(data) == float)
            return "%0.8x" % struct.unpack('<I', struct.pack('<f', data))[0]

        elif self.data_type == 'd':
            assert (type(data) == float)
            return "%0.16x" % struct.unpack('<Q', struct.pack('<d', data))[0]

    def get_packet(self):
        """
        creates the packet to send
        :return: A string containing a value packet to send over serial
        """

        self.current_packet = self.packet_info + \
                              self.format_data(self.value) + "\r"

        return self.current_packet
