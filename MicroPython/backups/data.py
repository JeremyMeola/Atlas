import array
import struct


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
        # for index in [0, 1, 3, 4] + list(range(6, len(packet) - 1)):
        for index in range(len(packet) - 1):
            if packet[index] != '\t' and not CommandPool.is_hex(packet[index]):
                return False
        return True

    def update(self, packet):
        if self.is_packet(packet):
            command_id = int(packet[0:2], 16)
            data_len = int(packet[3:5], 16)
            hex_data = packet[6: data_len + 6]

            if len(hex_data) == data_len and command_id in self.commands.keys():
                self.commands[command_id].current_packet = packet
                data = self.commands[command_id].format_data(hex_data)
                self.commands[command_id].callback(data)


class SerialObject(object):
    def __init__(self, object_id, formats, log_names=None):
        if isinstance(formats, list) or isinstance(formats, tuple):
            self.formats = formats
        else:
            self.formats = [formats]

        self.object_id = object_id

        self.current_packet = ""

        if log_names is None:
            self.log_names = []
        else:
            if isinstance(log_names, list) or isinstance(log_names, tuple):
                self.log_names = log_names
            else:
                self.log_names = [log_names]

        self.data = []
        self.data_len = 0
        self.format_len = []
        for data_format in self.formats:
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

    def update_log(self):
        return []

    def reset(self):
        pass


class Sensor(SerialObject):
    def __init__(self, sensor_id, formats, log_names=None):
        super().__init__(sensor_id, formats, log_names)

    def to_hex(self, data, length=0):
        if type(data) == int:
            if data < 0 and length > 0:
                data += (2 << (length * 4 - 1))
            # data %= MAXINT

            hex_format = "0.%sx" % length
            return ("%" + hex_format) % data
        else:
            raise Exception("Data not int type")

    @staticmethod
    def float_to_hex(data):
        return "%0.8x" % (struct.unpack('<I', bytes(array.array('f', [data]))))

    def format_data(self):
        hex_string = ""
        # length of data should equal number of formats
        for index in range(len(self.formats)):
            hex_string += self.formats[index][0]
            if self.formats[index][0] == 'f' or self.formats[index][0] == 'd':
                hex_string += Sensor.float_to_hex(self.data[index])
            elif self.formats[index][0] == 'b':
                hex_string += "1" if bool(self.data[index]) else "0"
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
        self.current_packet = "%s\t%s\r" % (self.to_hex(self.object_id, 2),
                                            self.format_data())
        return self.current_packet

    def recved_data(self):
        pass


class Command(SerialObject):
    def __init__(self, command_id, format, log_names=None):
        super().__init__(command_id, [format], log_names)

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

            return struct.unpack('!f', bytes.fromhex(hex_string))[0]
        elif self.formats[0][0] == 'd':
            # assure length of 16
            input_str = "0" * (16 - len(hex_string)) + hex_string

            return struct.unpack('!d', bytes.fromhex(hex_string))[0]

    def callback(self, data):
        pass
