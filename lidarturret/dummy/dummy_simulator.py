from atlasbuggy import project
from atlasbuggy.plotter import PostPlotter

from dummy.dummy_bot import Dummy


class DummyPostPlotter(PostPlotter):
    def __init__(self, file_name, directory, enable_3d, use_pickled_data,
                 **plot_info):
        self.dummy = Dummy()
        super(DummyPostPlotter, self).__init__(
            file_name, directory, plot_info, enable_3d, use_pickled_data,
            self.dummy)

    def step(self, index, timestamp, whoiam, robot_object):
        if whoiam == self.dummy.whoiam:
            if not self.enable_3d:
                self.append_data(
                    "plot_dummy", robot_object.accel_x, robot_object.accel_y)
            else:
                self.append_data(
                    "plot_dummy", robot_object.accel_x, robot_object.accel_y,
                    robot_object.accel_z
                )


def simulate_dummy():
    file_name, directory = project.parse_arguments(-1, -2)
    DummyPostPlotter(file_name, directory,
                     enable_3d=True, use_pickled_data=False,
                     plot_dummy=dict(
                         color='red', label="dummy"
                     )).run()
