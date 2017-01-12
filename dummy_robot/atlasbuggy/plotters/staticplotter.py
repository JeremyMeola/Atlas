from matplotlib import pyplot as plt
from atlasbuggy.plotters.baseplotter import BasePlotter
from atlasbuggy.plotters.robotplot import RobotPlot, RobotPlotCollection


class StaticPlotter(BasePlotter):
    def __init__(self, num_columns, *robot_plots, legend_args=None):
        super(StaticPlotter, self).__init__(num_columns, legend_args, *robot_plots)

        for plot in self.robot_plots:
            if isinstance(plot, RobotPlot):
                if plot.flat:
                    self.lines[plot.name] = None
                else:
                    self.lines[plot.name] = None
            elif isinstance(plot, RobotPlotCollection):
                self.lines[plot.name] = {}

                if plot.flat:
                    for subplot in plot.plots:
                        self.lines[plot.name][subplot.name] = None
                else:
                    for subplot in plot.plots:
                        self.lines[plot.name][subplot.name] = None

    def plot(self):
        if not self.plotter_enabled:
            return

        for plot in self.robot_plots:
            if isinstance(plot, RobotPlot):
                if plot.flat:
                    self.lines[plot.name] = self.axes[plot.name].plot(
                        plot.data[0], plot.data[1], **plot.properties)[0]
                else:
                    self.lines[plot.name] = self.axes[plot.name].plot(
                        plot.data[0], plot.data[1], plot.data[2], **plot.properties)[0]
            elif isinstance(plot, RobotPlotCollection):
                if plot.flat:
                    for subplot in plot.plots:
                        self.lines[plot.name][subplot.name] = self.axes[plot.name].plot(
                            subplot.data[0], subplot.data[1], **subplot.properties)[0]
                else:
                    for subplot in plot.plots:
                        self.lines[plot.name][subplot.name] = self.axes[plot.name].plot(
                            subplot.data[0], subplot.data[1], subplot.data[2], **subplot.properties)[0]
        for plot in self.robot_plots:
            if plot.flat:
                self.axes[plot.name].set_xlim(plot.x_range)
                self.axes[plot.name].set_ylim(plot.y_range)
            else:
                self.axes[plot.name].set_xlim3d(plot.x_range)
                self.axes[plot.name].set_ylim3d(plot.y_range)
                self.axes[plot.name].set_zlim3d(plot.z_range)

        self.init_legend()

    def show(self):
        plt.show()