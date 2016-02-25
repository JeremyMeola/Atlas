import struct
import array
from sys import maxsize as MAXINT


class SensorQueue(object):
    def __init__(self, *sensors):
        self.sensor_index = 0
        self.sensors = {}

        for sensor in sensors:
            if sensor.object_id in list(self.sensors.keys()):
                raise Exception(
                        "Sensor ID already taken: " + str(sensor.object_id))
            else:
                self.sensors[sensor.object_id] = sensor

        self.sensor_ids = sorted(self.sensors.keys())

    def current_index(self):
        sensor_id = self.sensor_ids[self.sensor_index]
        self.sensor_index = (self.sensor_index + 1) % len(self.sensor_ids)
        return sensor_id

    def get(self):
        return self.sensors[self.current_index()].get_packet()


class CommandPool(object):
    def __init__(self, *commands):
        self.commands = {}

        for command in commands:
            if command.object_id in list(self.commands.keys()):
                raise Exception(
                        "Command ID already taken: " + str(command.object_id))
            else:
                self.commands[command.object_id] = command

    @staticmethod
    def is_hex(character):
        return (ord('0') <= ord(character) <= ord('9') or
                ord('a') <= ord(character) <= ord('f') or
                ord('A') <= ord(character) <= ord('F'))

    @staticmethod
    def is_packet(packet):
        if len(packet) < 7: return False
        for index in [0, 1, 3, 4] + list(range(6, len(packet) - 1)):
            if not CommandPool.is_hex(packet[index]):
                return False
        return True

    def update(self, packet):
        if self.is_packet(packet):
            command_id = int(packet[0:2], 16)
            data_len = int(packet[3:5], 16)
            hex_data = packet[6: data_len + 6]

            if len(hex_data) == data_len:
                data = self.commands[command_id].format_data(hex_data)
                self.commands[command_id].callback(data)


class SerialObject(object):
    def __init__(self, object_id, formats):
        self.formats = formats

        self.object_id = object_id

        self.data = []
        self.data_len = 0
        self.format_len = []
        for data_format in formats:
            if data_format[0] == 'u' or data_format[0] == 'i':
                self.data.append(0)
                self.format_len.append(int(data_format[1:]) // 4)
                self.data_len += int(data_format[1:])
            elif data_format[0] == 'f':
                self.data.append(0.0)
                self.format_len.append(8)
                self.data_len += 8
            elif data_format[0] == 'd':
                self.data.append(0.0)
                self.format_len.append(16)
                self.data_len += 16
            elif data_format[0] == 'b':
                self.data.append(False)
                self.format_len.append(1)
                self.data_len += 1
            else:
                raise ValueError("Invalid format: %s", str(data_format))


class Sensor(SerialObject):
    def __init__(self, sensor_id, *formats):
        super().__init__(sensor_id, formats)

    def to_hex(self, data, length=0):
        if type(data) == int:
            if data < 0 and length > 0:
                data += (2 << (length * 4 - 1))
            # data %= MAXINT

            hex_format = "0.%sx" % length
            return ("%" + hex_format) % data
        else:
            raise Exception("Data not int type")

    def float_to_hex(self, data):
        return "%0.8x" % (struct.unpack('<I', bytes(array.array('f', [data]))))

    def format_data(self):
        hex_string = ""
        # length of data should equal number of formats
        for index in range(len(self.formats)):
            hex_string += self.formats[index][0]
            if self.formats[index][0] == 'f' or self.formats[index][0] == 'd':
                hex_string += self.float_to_hex(self.data[index])
            else:
                hex_string += self.to_hex(self.data[index],
                                          self.format_len[index])
            hex_string += '\t'

        return hex_string[:-1]

    def update_data(self):
        pass

    def get_packet(self):
        self.data = self.update_data()
        try:
           _ = (e for e in self.data)
        except TypeError:
           # print(self.data, 'is not iterable')
           self.data = [self.data]
        return "%s\t%s\r" % (self.to_hex(self.object_id, 2),
                             self.format_data())


class Command(SerialObject):
    def __init__(self, command_id, format):
        super().__init__(command_id, [format])

    def format_data(self, hex_string):
        if self.formats[0] == 'b':
            return bool(int(hex_string, 16))

        elif self.formats[0][0] == 'u':
            return int(hex_string, 16)

        elif self.formats[0][0] == 'i':
            bin_length = len(hex_string) * 4
            raw_int = int(hex_string, 16)
            if (raw_int >> (bin_length - 1)) == 1:
                raw_int -= 2 << (bin_length - 1)
            return int(raw_int)

        elif self.formats[0][0] == 'f':
            # assure length of 8
            input_str = "0" * (8 - len(hex_string)) + hex_string

            return struct.unpack('!f', input_str.decode('hex'))[0]
        elif self.formats[0][0] == 'd':
            # assure length of 16
            input_str = "0" * (16 - len(hex_string)) + hex_string

            return struct.unpack('!d', input_str.decode('hex'))[0]

    def callback(self, data):
        pass
