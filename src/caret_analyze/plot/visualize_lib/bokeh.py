# Copyright 2021 Research Institute of Systems Planning, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from collections import defaultdict
from logging import getLogger
from typing import Any, Dict, Generator, List, Optional, Sequence, Tuple, Union

from bokeh.colors import Color, RGB
from bokeh.models import (GlyphRenderer, HoverTool, Legend,
                          LinearAxis, Range1d, SingleIntervalTicker)
from bokeh.plotting import ColumnDataSource, Figure, figure

import colorcet as cc
import numpy as np

from .visualize_lib_interface import VisualizeLibInterface
from ..metrics_base import MetricsBase
from ...record import RecordsInterface
from ...runtime import (CallbackBase, Communication, Path, Publisher,
                        Subscription, SubscriptionCallback, TimerCallback)

# from caret_analyze.plot.stacked_bar.latency_stacked_bar import LatencyStackedBar
# from ..stacked_bar.latency_stacked_bar import LatencyStackedBar

TimeSeriesTypes = Union[CallbackBase, Communication, Union[Publisher, Subscription]]

logger = getLogger(__name__)


class Bokeh(VisualizeLibInterface):
    """Class that visualizes data using Bokeh library."""

    def __init__(self) -> None:
        pass

    @staticmethod
    def _figure_settings(
        xaxis_type: str,
        ywheel_zoom: bool,
    ):
        fig_args: Dict[str, Union[int, str, List[str]]] = \
            {'frame_height': 270, 'frame_width': 800}
        if ywheel_zoom:
            fig_args['active_scroll'] = 'wheel_zoom'
        else:
            fig_args['tools'] = ['xwheel_zoom', 'xpan', 'save', 'reset']
            fig_args['active_scroll'] = 'xwheel_zoom'

        if xaxis_type == 'system_time':
            fig_args['x_axis_label'] = 'system time [s]'
            x_label: str = 'start time'
        elif xaxis_type == 'sim_time':
            fig_args['x_axis_label'] = 'simulation time [s]'
            x_label: str = 'start time'
        else: # index
            fig_args['x_axis_label'] = xaxis_type
            x_label: str = 'index'

        fig_args['title'] = 'Stacked bar of Response Time.'
        return fig_args, x_label


    @staticmethod
    def _update_data_unit(
        data: Dict[str, List[int]],
        unit: float,
    ) -> Dict[str, List[float]]:
        for key in data.keys():
            data[key] = [d * unit for d in data[key]]
        return data

    @staticmethod
    def _update_timestamps_to_offset_time(
        x_values: List[float]
    ):
        new_values: List[float] = []
        first_time = x_values[0]
        for time in x_values:
            new_values.append(time - first_time)
        return new_values

    @staticmethod
    def _stacked_y_values(
        data: Dict[str, List[float]],
        y_values: List[str],
    ) -> Dict[str, List[float]]:
        for prev_, next_ in zip(reversed(y_values[:-1]), reversed(y_values[1:])):
            data[prev_] = [data[prev_][i] + data[next_][i] for i in range(len(data[next_]))]
        return data

    @staticmethod
    def _get_x_width_list(x_values: List[float]) -> List[float]:
        x_width_list: List[float] = [(x_values[i+1]-x_values[i]) * 0.99 for i in range(len(x_values)-1)]
        x_width_list.append(x_width_list[-1])
        return x_width_list

    @staticmethod
    def _side_shift(
        values: List[float],
        shift_values: List[float]
    ) -> List[float]:
        return [values[i] + shift_values[i] for i in range(len(values))]


    def _get_stacked_bar_data(
        self,
        data: Dict[str, List[int]],
        y_labels: List[str],
        x_label: str,
    ): # -> Dict[str, List[float]], List[str], List[float]
        output_data: Dict[str, List[float]] = {}
        x_width_list: List[float] = []

        # Convert the data unit to second
        output_data = self._update_data_unit(data, 1e-9)

        # Calculate the stacked y values
        output_data = self._stacked_y_values(output_data, y_labels)

        if x_label == 'system_time':
            # Update the timestamps from absolutely time to offset time
            output_data[x_label] = self._update_timestamps_to_offset_time(output_data[x_label])

            x_width_list = self._get_x_width_list(output_data[x_label])
            harf_width_list = [x / 2 for x in x_width_list]

            # Slide x axis values so that the bottom left of bars are the start time.
            output_data[x_label] = self._side_shift(output_data[x_label], harf_width_list)
        elif x_label == 'sim_time':
            NotImplementedError()
        else: # index
            output_data[x_label] = [i for i in range(len(output_data[y_labels[0]]))]
            x_width_list = self._get_x_width_list(output_data[x_label])

        return output_data, x_width_list

    @staticmethod
    def _create_source(
        data: Dict[str, list[float]],
        y_labels: List[str],
        x_width_list: List[float],
    ): # -> ColumnDataSource, List[str]
        source = ColumnDataSource(data)
        source.add(y_labels, 'legend')
        source.add(x_width_list, 'x_width_list')
        prev_y_labels: List[str] = []
        for y_label in y_labels[1:]:
            bottom_label = y_label + '_bottom'
            prev_y_labels.append(bottom_label)
            source.add(data[y_label], bottom_label)
        return source, prev_y_labels

    @staticmethod
    def _update_legend_setting(p):
        # Processing to move legends out of graph area
        # https://stackoverflow.com/questions/46730609/position-the-legend-outside-the-plot-area-with-bokeh
        new_legend = p.legend[0]
        p.legend[0] = None
        p.add_layout(new_legend, 'right')

        # click policy. 'mute' makes the graph translucent.
        p.legend.click_policy='mute' # or 'hide'
        return p

    def _create_bar_plot(
        self,
        fig_args: Dict[str, Union[int, str, List[str]]],
        source: ColumnDataSource,
        x_label: str,
        y_labels: List[str],
        prev_y_labels: list[str],
        full_legends: bool,
    ):
        def get_color_generator() -> Generator:
            color_palette = self._create_color_palette()
            color_idx = 0
            while True:
                yield color_palette[color_idx]
                color_idx = (color_idx + 1) % len(color_palette)

        p = figure(**fig_args)
        color_generator = get_color_generator()
        color: Sequence[Color] = next(color_generator)

        legend_manager = LegendManager()
        for y_label, bottom in zip(y_labels[:-1], prev_y_labels):
            renderer = p.vbar(
                x=x_label,
                top=y_label,
                width='x_width_list',
                source=source,
                color=color,
                bottom=bottom,
                legend_label=y_label,
            )
            color = next(color_generator)
            legend_manager.add_legend(y_label, renderer)

        renderer = p.vbar(
            x=x_label,
            top=y_labels[-1],
            width='x_width_list',
            source=source,
            color=color,
            legend_label=y_labels[-1],
        )
        legend_manager.add_legend(y_labels[-1], renderer)
        num_legend_threshold = 20
        legend_manager.draw_legends(p, num_legend_threshold, full_legends)

        return p

    def stacked_bar(
        self,
        metrics,
        xaxis_type: str,
        ywheel_zoom: bool,
        full_legends: bool, # NOTE: unused because LegendManager not apply stacked bar.
    ):

        # NOTE: relation betwenn stacked bar graph and data struct
        # # data = {
        # #     a : [a1, a2, a3],
        # #     b : [b1, b2, b3],
        # #     'start time': [s1, s2, s3]
        # # }
        # # y_labels = [a, b]

        # # ^               ^
        # # |               |       ^       [] a
        # # |       ^       |       |       [] b
        # # |       |       a2      |
        # # |       a1      ^       a3
        # # |       ^       |       ^
        # # |       |       |       |
        # # |       b1      b2      b3
        # # +-------s1------s2------s3---------->



        # get stacked bar data
        data: Dict[str, list[int]] = {}
        y_labels: List[str] = []
        fig_args: Dict[str, Union[int, str, List[str]]] = {}
        fig_args, x_label = self._figure_settings(xaxis_type, ywheel_zoom)


        data, y_labels = metrics.to_stacked_bar_records_dict()

        # data conversion to visualize data as stacked bar graph
        stacked_bar_data, x_width_list = self._get_stacked_bar_data(data, y_labels, x_label)
        source, prev_y_labels = self._create_source(stacked_bar_data, y_labels, x_width_list)

        p = self._create_bar_plot(
            fig_args,
            source,
            x_label,
            y_labels,
            prev_y_labels,
            full_legends,
        )
        p = self._update_legend_setting(p)



        return p


    def timeseries(
        self,
        metrics: MetricsBase,
        xaxis_type: str,
        ywheel_zoom: bool,
        full_legends: bool
    ) -> Figure:
        """
        Get a timeseries figure.

        Parameters
        ----------
        metrics : MetricsBase
            Metrics to be y-axis in visualization.
        xaxis_type : str
            Type of x-axis of the line graph to be plotted.
            "system_time", "index", or "sim_time" can be specified.
            The default is "system_time".
        ywheel_zoom : bool
            If True, the drawn graph can be expanded in the y-axis direction
            by the mouse wheel.
        full_legends : bool
            If True, all legends are drawn
            even if the number of legends exceeds the threshold.

        Returns
        -------
        bokeh.plotting.Figure
            Figure of timeseries.

        """
        target_objects = metrics.target_objects
        timeseries_records_list = metrics.to_timeseries_records_list(xaxis_type)

        # Initialize figure
        y_axis_label = timeseries_records_list[0].columns[1]
        fig_args = {'frame_height': 270,
                    'frame_width': 800,
                    'y_axis_label': y_axis_label}

        if xaxis_type == 'system_time':
            fig_args['x_axis_label'] = 'system time [s]'
        elif xaxis_type == 'sim_time':
            fig_args['x_axis_label'] = 'simulation time [s]'
        else:
            fig_args['x_axis_label'] = xaxis_type

        if ywheel_zoom:
            fig_args['active_scroll'] = 'wheel_zoom'
        else:
            fig_args['tools'] = ['xwheel_zoom', 'xpan', 'save', 'reset']
            fig_args['active_scroll'] = 'xwheel_zoom'

        if isinstance(target_objects[0], CallbackBase):
            fig_args['title'] = f'Time-line of callbacks {y_axis_label}'
        elif isinstance(target_objects[0], Communication):
            fig_args['title'] = f'Time-line of communications {y_axis_label}'
        else:
            fig_args['title'] = f'Time-line of publishes/subscribes {y_axis_label}'

        p = figure(**fig_args)

        # Apply xaxis offset
        frame_min, frame_max = self._get_range(target_objects)
        if xaxis_type == 'system_time':
            self._apply_x_axis_offset(p, 'x_axis_plot', frame_min, frame_max)

        # Draw lines
        def get_color_generator() -> Generator:
            color_palette = self._create_color_palette()
            color_idx = 0
            while True:
                yield color_palette[color_idx]
                color_idx = (color_idx + 1) % len(color_palette)

        legend_manager = LegendManager()
        line_source = LineSource(frame_min, xaxis_type, legend_manager)
        p.add_tools(line_source.create_hover(target_objects[0]))
        color_generator = get_color_generator()
        for to, timeseries in zip(target_objects, timeseries_records_list):
            renderer = p.line(
                'x', 'y',
                source=line_source.generate(to, timeseries),
                color=next(color_generator)
            )
            legend_manager.add_legend(to, renderer)

        # Draw legends
        num_legend_threshold = 20
        """
        In Autoware, the number of callbacks in a node is less than 20.
        Here, num_legend_threshold is set to 20 as the maximum value.
        """
        legend_manager.draw_legends(p, num_legend_threshold, full_legends)

        return p

    @staticmethod
    def _create_color_palette() -> Sequence[Color]:
        def from_rgb(r: float, g: float, b: float) -> RGB:
            r_ = int(r*255)
            g_ = int(g*255)
            b_ = int(b*255)

            return RGB(r_, g_, b_)

        return [from_rgb(*rgb) for rgb in cc.glasbey_bw_minc_20]

    @staticmethod
    def _get_range(target_objects: List[TimeSeriesTypes]) -> Tuple[int, int]:
        has_valid_data = False

        try:
            # NOTE:
            # If remove_dropped=True,
            # data in DataFrame may be lost due to drops in columns other than the first column.
            to_dfs = [to.to_dataframe(remove_dropped=False) for to in target_objects]
            to_dfs_valid = [to_df for to_df in to_dfs if len(to_df) > 0]

            # NOTE:
            # The first column is system time for now.
            # The other columns could be other than system time.
            # Only the system time is picked out here.
            base_series = [df.iloc[:, 0] for df in to_dfs_valid]
            min_series = [series.min() for series in base_series]
            max_series = [series.max() for series in base_series]
            valid_min_series = [value for value in min_series if not np.isnan(value)]
            valid_max_series = [value for value in max_series if not np.isnan(value)]

            has_valid_data = len(valid_max_series) > 0 or len(valid_min_series) > 0
            to_min = min(valid_min_series)
            to_max = max(valid_max_series)
            return to_min, to_max
        except Exception:
            msg = 'Failed to calculate interval of measurement time.'
            if not has_valid_data:
                msg += ' No valid measurement data.'
            logger.warning(msg)
            return 0, 1

    @staticmethod
    def _apply_x_axis_offset(
        fig: Figure,
        x_range_name: str,
        min_ns: float,
        max_ns: float
    ) -> None:
        offset_s = min_ns*1.0e-9
        end_s = (max_ns-min_ns)*1.0e-9

        fig.extra_x_ranges = {x_range_name: Range1d(start=min_ns, end=max_ns)}

        xaxis = LinearAxis(x_range_name=x_range_name)
        xaxis.visible = False  # type: ignore

        ticker = SingleIntervalTicker(interval=1, num_minor_ticks=10)
        fig.xaxis.ticker = ticker
        fig.add_layout(xaxis, 'below')

        fig.x_range = Range1d(start=0, end=end_s)

        fig.xgrid.minor_grid_line_color = 'black'
        fig.xgrid.minor_grid_line_alpha = 0.1

        fig.xaxis.major_label_overrides = {0: f'0+{offset_s}'}

class LineSource:
    """Class that generate lines of timeseries data."""

    def __init__(
        self,
        frame_min,
        xaxis_type: str,
        legend_manager: LegendManager
    ) -> None:
        self._frame_min = frame_min
        self._xaxis_type = xaxis_type
        self._legend = legend_manager

    def create_hover(self, target_object: TimeSeriesTypes) -> HoverTool:
        """
        Create HoverTool for timeseries figure.

        Parameters
        ----------
        target_object : TimeSeriesTypes
            TimeSeriesPlotTypes = Union[
                CallbackBase, Communication, Union[Publisher, Subscription]
            ]

        Returns
        -------
        bokeh.models.HoverTool
            This contains information display when hovering the mouse over a drawn line.

        """
        source_keys = self._get_source_keys(target_object)
        tips_str = '<div style="width:400px; word-wrap: break-word;">'
        for k in source_keys:
            tips_str += f'@{k} <br>'
        tips_str += '</div>'

        return HoverTool(tooltips=tips_str, point_policy='follow_mouse')

    def generate(
        self,
        target_object: TimeSeriesTypes,
        timeseries_records: RecordsInterface,
    ) -> ColumnDataSource:
        """
        Generate a line source for timeseries figure.

        Parameters
        ----------
        target_object : TimeSeriesTypes
            TimeSeriesPlotTypes = Union[
                CallbackBase, Communication, Union[Publisher, Subscription]
            ]
        timeseries_records : RecordsInterface
            Records containing timeseries data.

        Returns
        -------
        bokeh.plotting.ColumnDataSource
            Line source for timeseries figure.

        """
        line_source = ColumnDataSource(data={
            k: [] for k in (['x', 'y'] + self._get_source_keys(target_object))
        })
        data_dict = self._get_data_dict(target_object)
        x_item, y_item = self._get_x_y(timeseries_records)
        for x, y in zip(x_item, y_item):
            line_source.stream({**{'x': [x], 'y': [y]}, **data_dict})  # type: ignore

        return line_source

    def _get_x_y(
        self,
        timeseries_records: RecordsInterface
    ) -> Tuple[List[Union[int, float]], List[Union[int, float]]]:
        def ensure_not_none(
            target_seq: Sequence[Optional[Union[int, float]]]
        ) -> List[Union[int, float]]:
            """
            Ensure the inputted list does not include None.

            Notes
            -----
            The timeseries_records is implemented not to include None,
            so if None is included, an AssertionError is output.

            """
            not_none_list = [_ for _ in target_seq if _ is not None]
            assert len(target_seq) == len(not_none_list)

            return not_none_list

        ts_column = timeseries_records.columns[0]
        value_column = timeseries_records.columns[1]
        timestamps = ensure_not_none(timeseries_records.get_column_series(ts_column))
        values = ensure_not_none(timeseries_records.get_column_series(value_column))
        if 'latency' in value_column.lower() or 'period' in value_column.lower():
            values = [v*10**(-6) for v in values]  # [ns] -> [ms]

        x_item: List[Union[int, float]]
        y_item: List[Union[int, float]] = values
        if self._xaxis_type == 'system_time':
            x_item = [(ts-self._frame_min)*10**(-9) for ts in timestamps]
        elif self._xaxis_type == 'index':
            x_item = list(range(0, len(values)))
        elif self._xaxis_type == 'sim_time':
            x_item = timestamps

        return x_item, y_item

    def _get_source_keys(
        self,
        target_object: TimeSeriesTypes
    ) -> List[str]:
        source_keys: List[str]
        if isinstance(target_object, CallbackBase):
            source_keys = ['legend_label', 'node_name', 'callback_name', 'callback_type',
                           'callback_param', 'symbol']
        elif isinstance(target_object, Communication):
            source_keys = ['legend_label', 'topic_name',
                           'publish_node_name', 'subscribe_node_name']
        elif isinstance(target_object, (Publisher, Subscription)):
            source_keys = ['legend_label', 'node_name', 'topic_name']
        else:
            raise NotImplementedError()

        return source_keys

    def _get_description(
        self,
        key: str,
        target_object: TimeSeriesTypes
    ) -> str:
        if key == 'callback_param':
            if isinstance(target_object, TimerCallback):
                description = f'period_ns = {target_object.period_ns}'
            elif isinstance(target_object, SubscriptionCallback):
                description = f'subscribe_topic_name = {target_object.subscribe_topic_name}'
        elif key == 'legend_label':
            label = self._legend.get_label(target_object)
            description = f'legend_label = {label}'
        else:
            raise NotImplementedError()

        return description

    def _get_data_dict(
        self,
        target_object: TimeSeriesTypes
    ) -> Dict[str, Any]:
        data_dict: Dict[str, Any] = {}

        for k in self._get_source_keys(target_object):
            try:
                data_dict[k] = [f'{k} = {getattr(target_object, k)}']
            except AttributeError:
                data_dict[k] = [self._get_description(k, target_object)]

        return data_dict


class LegendManager:
    """Class that manages legend in Bokeh figure."""

    def __init__(self) -> None:
        self._legend_count_map: Dict[str, int] = defaultdict(int)
        self._legend_items: List[Tuple[str, List[GlyphRenderer]]] = []
        self._legend: Dict[Any, str] = {}

    def add_legend(
        self,
        target_object: Any,
        renderer: GlyphRenderer
    ) -> None:
        """
        Store a legend of the input object internally.

        Parameters
        ----------
        target_object : Any
            Instance of any class.
        renderer : bokeh.models.GlyphRenderer
            Instance of renderer.

        """
        label = self.get_label(target_object)
        self._legend_items.append((label, [renderer]))
        self._legend[target_object] = label

    def draw_legends(
        self,
        figure: Figure,
        max_legends: int = 20,
        full_legends: bool = False
    ) -> None:
        """
        Add legends to the input figure.

        Parameters
        ----------
        figure : Figure
            Target figure.
        max_legends : int, optional
            Maximum number of legends to display, by default 20.
        full_legends : bool, optional
            Display all legends even if they exceed max_legends, by default False.

        """
        for i in range(0, len(self._legend_items)+10, 10):
            if not full_legends and i >= max_legends:
                logger.warning(
                    f'The maximum number of legends drawn by default is {max_legends}. '
                    'If you want all legends to be displayed, '
                    'please specify the `full_legends` option to True.'
                )
                break
            figure.add_layout(Legend(items=self._legend_items[i:i+10]), 'right')

        figure.legend.click_policy = 'hide'

    def get_label(self, target_object: Any) -> str:
        if target_object in self._legend:
            return self._legend[target_object]

        class_name = type(target_object).__name__
        label = f'{class_name.lower()}{self._legend_count_map[class_name]}'
        self._legend_count_map[class_name] += 1
        self._legend[target_object] = label

        return label