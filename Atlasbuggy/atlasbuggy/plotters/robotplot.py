"""
Contains the RobotPlot and RobotPlotCollection classes. These class define a subplot's properties.
    RobotPlot defines a single line on a plot, its color, if it's a 2D plot, window range, etc.
    RobotPlotCollection defines a subplot with multiple RobotPlot lines.
"""

import mpl_toolkits.mplot3d.axes3d  # loads 3D modules


class RobotPlot:
    def __init__(self, plot_name, plot_enabled=True, flat_plot=True,
                 x_range=None, y_range=None, z_range=None, range_offset=0,
                 x_lim=None, y_lim=None, z_lim=None, skip_count=0,
                 max_length=None, **plot_properties):
        """
        :param plot_name: plot title and internal reference name. Make sure its unique
        :param plot_enabled: Turn plots on and off easily with this flag
        :param flat_plot: 2D if True, 3D if False
        :param x_range: x axis range. If None, the axis will be unconstrained
        :param y_range: y axis range. If None, the axis will be unconstrained
        :param z_range: z axis range. If None, the axis will be unconstrained
        :param range_offset: amount of trim to give to the range
        :param x_lim: x bounds on axis range. If None, the axis will be unbounded
        :param y_lim: y bounds on axis range. If None, the axis will be unbounded
        :param z_lim: z bounds on axis range. If None, the axis will be unbounded
        :param skip_count: Amount of data points to skip (improves performance)
        :param max_length: Limit the amount of data points a plot has (improves performance)
        :param plot_properties: parameters to supply to matplotlib's plot function (color, marker type, etc.)
        """
        self.name = plot_name
        self.flat = flat_plot
        self.enabled = plot_enabled
        self.max_length = max_length
        self.skip_count = skip_count
        self.skip_counter = 0

        self.properties = plot_properties

        if x_range is not None:
            x_range = list(x_range)
            assert len(x_range) == 2
        if y_range is not None:
            y_range = list(y_range)
            assert len(y_range) == 2
        if z_range is not None:
            z_range = list(z_range)
            assert len(z_range) == 2

        self.ranges = [x_range, y_range, z_range]
        self.ranges_contrained = []
        for r in self.ranges:
            self.ranges_contrained.append(False if r is None else True)
        self.range_offset = range_offset

        if x_lim is not None:
            x_lim = list(x_lim)
            assert len(x_lim) == 2
        if y_lim is not None:
            y_lim = list(y_lim)
            assert len(y_lim) == 2
        if z_lim is not None:
            z_lim = list(z_lim)
            assert len(z_lim) == 2
        self.limits = [x_lim, y_lim, z_lim]

        self.data = [[] for _ in range(2 if flat_plot else 3)]

    def update(self, xs, ys, zs=None):
        """
        Update the plot's data using the input lists if it is enabled

        :param xs: a list of new values for the x axis
        :param ys: a list of new values for the y axis
        :param zs: a list of new values for the z axis
        :return: None
        """
        if not self.enabled:
            return

        self.skip_counter += 1
        if self.skip_count > 0 and self.skip_counter % self.skip_count != 0:
            return

        # Collect values into a list for convenience
        if self.flat:
            assert len(xs) == len(ys)
            values = [xs, ys]
        else:
            assert len(xs) == len(ys) == len(zs)
            values = [xs, ys, zs]

        # Replace the old data and update the range if it's not None
        for axis_num in range(len(values)):
            self.data[axis_num] = values[axis_num]

            if self.ranges[axis_num] is not None and len(values[axis_num]) > 0:
                # self.ranges[axis_num][0] = min(values[axis_num])
                # self.ranges[axis_num][1] = max(values[axis_num])
                #
                # if self.limits[axis_num] is not None:
                #     if self.ranges[axis_num][0] > self.limits[axis_num][0]:
                #         self.ranges[axis_num][0] = self.limits[axis_num][0]
                #     if self.ranges[axis_num][1] > self.limits[axis_num][1]:
                #         self.ranges[axis_num][1] = self.limits[axis_num][1]
                self._update_range(min(values[axis_num]), axis_num)
                self._update_range(max(values[axis_num]), axis_num)

    def append(self, x, y, z=None):
        """
        Append new values to the plot if it is enabled

        :param x: A float value to append to the x axis
        :param y: A float value to append to the y axis
        :param z: A float value to append to the z axis
        :return: None
        """
        if not self.enabled:
            return

        self.skip_counter += 1
        if self.skip_count > 0 and self.skip_counter % self.skip_count != 0:
            return

        self._append_x(x)
        self._append_y(y)
        if not self.flat:
            self._append_z(z)

    def _update_range(self, value, axis_num):
        """
        Determine if the new value is less than the minimum or greater than maximum.
        If it is, update the range for the corresponding axis

        :param value: new value added
        :param axis_num: axis number to update
        :return: None
        """
        if self.ranges[axis_num] is None:
            if self.range_offset == 0:
                offset = 0.001
            else:
                offset = self.range_offset
            self.ranges[axis_num] = [value - offset, value + offset]

        if value < self.ranges[axis_num][0]:
            self.ranges[axis_num][0] = value - self.range_offset
        if value > self.ranges[axis_num][1]:
            self.ranges[axis_num][1] = value + self.range_offset

        if self.limits[axis_num] is not None:
            if self.ranges[axis_num][0] > self.limits[axis_num][0]:
                self.ranges[axis_num][0] = self.limits[axis_num][0]
            if self.ranges[axis_num][1] > self.limits[axis_num][1]:
                self.ranges[axis_num][1] = self.limits[axis_num][1]

    def _append_to_axis(self, datum, axis_num):
        """
        Append a new value to an axis number

        :param datum: A floating point number
        :param axis_num: Axis number to append the value to
        :return: None
        """
        self.data[axis_num].append(datum)
        self._update_range(datum, axis_num)

        if self.max_length is not None and len(self.data[axis_num]) > self.max_length:
            self.data[axis_num].pop(0)
            if not self.ranges_contrained[axis_num]:
                self.ranges[axis_num][0] = min(self.data[axis_num])
                self.ranges[axis_num][1] = max(self.data[axis_num])

    def ranges_set(self):
        for r in self.ranges:
            if r is None:
                return False

        return True

    def _append_x(self, x):
        self._append_to_axis(x, 0)

    def _append_y(self, y):
        self._append_to_axis(y, 1)

    def _append_z(self, z):
        self._append_to_axis(z, 2)

    @property
    def x_range(self):
        return self.ranges[0]

    @property
    def y_range(self):
        return self.ranges[1]

    @property
    def z_range(self):
        return self.ranges[2]


class RobotPlotCollection:
    def __init__(self, collection_name, *robot_plots, plot_enabled=True, flat_plot=True):
        """
        If you want to plot multiple lines on one subplot, pass your robot plot objects to a collection.
        Each robot plot will be treated as one line on the subplot.

        :param collection_name: plot title and internal reference name. Make sure its unique
        :param robot_plots: RobotPlot instances
        :param plot_enabled: Turn collections on and off easily with this flag. If False, all subplots will be disabled
        :param flat_plot: 2D if True, 3D if False. All subplots will be assigned this value
        """
        self.name = collection_name
        self.plots = []

        # unify key properties between all subplots
        self.flat = flat_plot
        self.enabled = plot_enabled
        for plot in robot_plots:
            if plot.enabled:
                plot.flat = self.flat
                plot.properties["label"] = plot.name
                self.plots.append(plot)

        if len(self.plots) == 0:
            self.enabled = False

    def ranges_set(self):
        for plot in self.plots:
            if not plot.ranges_set():
                return False
        return True

    @property
    def x_range(self):
        x_min = min(self.plots, key=lambda plot: plot.x_range[0]).x_range[0]
        x_max = max(self.plots, key=lambda plot: plot.x_range[1]).x_range[1]
        return x_min, x_max

    @property
    def y_range(self):
        y_min = min(self.plots, key=lambda plot: plot.y_range[0]).y_range[0]
        y_max = max(self.plots, key=lambda plot: plot.y_range[1]).y_range[1]
        return y_min, y_max

    @property
    def z_range(self):
        z_min = min(self.plots, key=lambda plot: plot.z_range[0]).z_range[0]
        z_max = max(self.plots, key=lambda plot: plot.z_range[1]).z_range[1]
        return z_min, z_max
