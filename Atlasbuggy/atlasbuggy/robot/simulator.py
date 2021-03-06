"""
RobotInterfaceSimulator imitates RobotInterface except its data source is a log file.
"""

from atlasbuggy.logfiles.parser import Parser
from atlasbuggy.robot.robotobject import RobotObject
from atlasbuggy.robot.robotcollection import RobotObjectCollection
from atlasbuggy.robot.errors import RobotObjectInitializationError

class RobotInterfaceSimulator:
    def __init__(self, file_name, directory, *robot_objects, start_index=0, end_index=-1):
        """
        :param file_name: log file name or number
        :param directory: directory to search in
        :param start_index:
        :param end_index:
        :param robot_objects:
        """
        self.objects = {}
        for robot_object in robot_objects:
            if isinstance(robot_object, RobotObject):
                self.objects[robot_object.whoiam] = robot_object
            elif isinstance(robot_object, RobotObjectCollection):
                for whoiam in robot_object.whoiam_ids:
                    self.objects[whoiam] = robot_object
            else:
                raise RobotObjectInitializationError(
                    "Object passed isn't a RobotObject or RobotObjectCollection:", repr(robot_object))
        self.parser = Parser(file_name, directory, start_index, end_index)
        self.current_index = 0

        self.ids_used = set()
        self.ids_received = set()
        self.prev_whoiam = None

        self.prev_percent = 0
        self.percent = 0

        self.dt = None

    def print_percent(self):
        percent = 100 * self.parser.index / len(self.parser.contents)
        self.percent = int(percent * 10)
        if self.percent != self.prev_percent:
            self.prev_percent = self.percent
            print(("%0.1f" % percent) + "%", end='\r')

    def object_packet(self, timestamp):
        pass

    def user_packet(self, timestamp, packet):
        pass

    def command_packet(self, timestamp, packet):
        pass

    def did_receive(self, arg):
        if isinstance(arg, RobotObject):
            self.ids_used.add(arg.whoiam)
            return arg.whoiam == self.prev_whoiam
        elif isinstance(arg, RobotObjectCollection):
            for whoiam in arg.whoiam_ids:
                if whoiam == self.prev_whoiam:
                    self.ids_used.add(whoiam)
                    return True
        else:
            self.ids_used.add(arg)
            return arg == self.prev_whoiam

    def run(self):
        for index, packet_type, timestamp, whoiam, packet in self.parser:
            self.dt = timestamp
            self.prev_whoiam = whoiam
            self.ids_received.add(whoiam)

            if whoiam in self.objects.keys():
                if timestamp == -1:
                    if isinstance(self.objects[whoiam], RobotObject):
                        self.objects[whoiam].receive_first(packet)
                    elif isinstance(self.objects[whoiam], RobotObjectCollection):
                        self.objects[whoiam].receive_first(whoiam, packet)
                    continue
                else:
                    if isinstance(self.objects[whoiam], RobotObject):
                        self.objects[whoiam].receive(timestamp, packet)
                    elif isinstance(self.objects[whoiam], RobotObjectCollection):
                        self.objects[whoiam].receive(timestamp, whoiam, packet)


            self.current_index = index

            if packet_type == "object":
                if self.object_packet(timestamp) is False:
                    break
            elif packet_type == "user":
                if self.user_packet(timestamp, packet) is False:
                    break
            elif packet_type == "command":
                if self.command_packet(timestamp, packet) is False:
                    break

        if self.ids_received != self.ids_used:
            if len(self.ids_received - self.ids_used) > 0:
                print("Warning IDs unused:")
                for id in self.ids_received - self.ids_used:
                    print("\t", id)
            if len(self.ids_used - self.ids_received) > 0:
                print("Warning IDs not in log file:")
                for id in self.ids_used - self.ids_received:
                    print("\t", id)

        self.close()

    def close(self):
        pass
