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

import datetime
from logging import getLogger
from typing import Dict, List, Sequence, Union

from bokeh.models import AdaptiveTicker, Arrow, LinearAxis, NormalHead, Range1d
from bokeh.plotting import Figure, figure
from bokeh.plotting import ColumnDataSource # TODO: delete

import pandas as pd

from .bokeh_source import (CallbackSchedBarSource, CallbackSchedRectSource, LegendManager,
                           LineSource)
from .color_selector import ColorSelectorFactory
from ..visualize_lib_interface import VisualizeLibInterface
from ...metrics_base import MetricsBase
from ....common import Util
from ....record import Clip, Range
from ....runtime import (CallbackBase, CallbackGroup, Communication, Publisher, Subscription,
                         TimerCallback)

TimeSeriesTypes = Union[CallbackBase, Communication, Union[Publisher, Subscription]]

logger = getLogger(__name__)


class Bokeh(VisualizeLibInterface):
    """Class that visualizes data using Bokeh library."""

    def __init__(self) -> None:
        pass


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


        data, y_labels = metrics.to_stacked_bar_dict()

        # data conversion to visualize data as stacked bar graph
        stacked_bar_data, x_width_list = self._get_stacked_bar_data(data, y_labels, x_label)
        bottom_labels = self._get_bottom_labels(y_labels)
        bottom_labels = bottom_labels[1:]
        source = self._create_source(stacked_bar_data, y_labels, bottom_labels, x_width_list)

        p = self._create_bar_plot(
            fig_args,
            source,
            x_label,
            y_labels,
            bottom_labels,
            full_legends,
        )
        p = self._update_legend_setting(p)

        return p

    @staticmethod
    def _figure_settings(
        xaxis_type: str,
        ywheel_zoom: bool,
    ):
        # TODO: bundle this function with timeseries and callback scheduling
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

    def _get_stacked_bar_data(
        self,
        data: Dict[str, List[int]],
        y_labels: List[str],
        x_label: str,
    ): # -> Dict[str, List[float]], List[str], List[float]
        """
        Caluclate stacked bar data.

        Parameters
        ----------
        data : Dict[str, List[int]]
            Source data.
        y_labels : List[str]
            Y axis labels that are Node/Topic name.
        x_label : str
            X axis label that is 'start time'.

        Returns
        -------
        Dict[str, List[float]]
            Stacked bar data.
        List[float]
            Width list of bars.
        """
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
            output_data[x_label] = self._add_shift_value(output_data[x_label], harf_width_list)
        elif x_label == 'sim_time':
            NotImplementedError()
        else: # index
            output_data[x_label] = [i for i in range(len(output_data[y_labels[0]]))]
            x_width_list = self._get_x_width_list(output_data[x_label])

        return output_data, x_width_list


    @staticmethod
    def _update_data_unit(
        data: Dict[str, List[int]],
        unit: float,
    ) -> Dict[str, List[float]]:
        # TODO: make timeseries and callback scheduling function use this function.
        #       create bokeh_util.py
        for key in data.keys():
            data[key] = [d * unit for d in data[key]]
        return data

    @staticmethod
    def _stacked_y_values(
        data: Dict[str, List[float]],
        y_values: List[str],
    ) -> Dict[str, List[float]]:
        for prev_, next_ in zip(reversed(y_values[:-1]), reversed(y_values[1:])):
            data[prev_] = [data[prev_][i] + data[next_][i] for i in range(len(data[next_]))]
        return data


    @staticmethod
    def _update_timestamps_to_offset_time(
        x_values: List[float]
    ):
        # TODO: merge to '_apply_x_axis_offset' function.
        new_values: List[float] = []
        first_time = x_values[0]
        for time in x_values:
            new_values.append(time - first_time)
        return new_values


    @staticmethod
    def _get_x_width_list(x_values: List[float]) -> List[float]:
        """
        Get width between a x value and next x value

        Parameters
        ----------
        x_values : List[float]
            X values list.

        Returns
        -------
        List[float]
            Width list.
        """
        # TODO: create bokeh_util.py and move this.
        x_width_list: List[float] = [(x_values[i+1]-x_values[i]) * 0.99 for i in range(len(x_values)-1)]
        x_width_list.append(x_width_list[-1])
        return x_width_list

    @staticmethod
    def _add_shift_value(
        values: List[float],
        shift_values: List[float]
    ) -> List[float]:
        """
        Add shift values to target values.

        Parameters
        ----------
        values : List[float]
            Target values.
        shift_values : List[float]
            Shift values

        Returns
        -------
        List[float]
            Updated values.
        """
        # TODO: create bokeh_util.py and move this.
        return [values[i] + shift_values[i] for i in range(len(values))]

    @staticmethod
    def _get_bottom_labels(labels: List[str]) -> List[str]:
        return [label + '_bottom' for label in labels]

    @staticmethod
    def _create_source(
        data: Dict[str, list[float]],
        y_labels: List[str],
        bottom_labels: List[str],
        # unused: List[str],
        x_width_list: List[float],
    ): # -> ColumnDataSource, List[str]
        """_summary_

        Parameters
        ----------
        data : Dict[str, list[float]]
            Original data.
        y_labels : List[str]
            Y axis labels
        x_width_list : List[float]
            Width list of bars.

        Returns
        -------
        source : ColumnDataSource
            Source data.
        bottom_labels : List[str]
            Bottom labels of each
        """

        # TODO: move this to bokeh_source.py
        source = ColumnDataSource(data)
        source.add(y_labels, 'legend')
        source.add(x_width_list, 'x_width_list')
        for y_label, bottom_label in zip(y_labels[1:], bottom_labels):
            # bottom_label = y_label + '_bottom'
            # bottom_labels.append(bottom_label)
            source.add(data[y_label], bottom_label)
        return source

    def _create_bar_plot(
        self,
        fig_args: Dict[str, Union[int, str, List[str]]],
        source: ColumnDataSource,
        x_label: str,
        y_labels: List[str],
        bottom_labels: list[str],
        full_legends: bool,
        coloring_rule: str = 'unique',
    ):
        """_summary_

        Parameters
        ----------
        fig_args : Dict[str, Union[int, str, List[str]]]
            Figure settings.
        source : ColumnDataSource
            Source data.
        x_label : str
            X axis label that is 'start time'.
        y_labels : List[str]
            Y axis labels.
        bottom_labels : list[str]
            _description_
        full_legends : bool
            If True, all legends are drawn
            even if the number of legends exceeds the threshold.
        """
        # def get_color_generator() -> Generator:
        #     color_palette = self._create_color_palette()
        #     color_idx = 0
        #     while True:
        #         yield color_palette[color_idx]
        #         color_idx = (color_idx + 1) % len(color_palette)

        p = figure(**fig_args)
        # color_generator = get_color_generator()
        # color: Sequence[Color] = next(color_generator)

        color_selector = ColorSelectorFactory.create_instance(coloring_rule)

        # TODO: apply to legend manager as folloing code.
        # legend_manager = LegendManager()
        for y_label, bottom in zip(y_labels[:-1], bottom_labels):
            color = color_selector.get_color(y_label)
            renderer = p.vbar(
                x=x_label,
                top=y_label,
                width='x_width_list',
                source=source,
                color=color,
                bottom=bottom,
                legend_label=y_label,
            )
            # color = next(color_generator)
            # TODO: apply to legend manager as folloing code.
            # legend_manager.add_legend(y_label, renderer)


        color = color_selector.get_color(y_label[-1])
        renderer = p.vbar(
            x=x_label,
            top=y_labels[-1],
            width='x_width_list',
            source=source,
            color=color,
            legend_label=y_labels[-1],
        )

        # TODO: apply to legend manager as folloing code.
        # legend_manager.add_legend(y_labels[-1], renderer)
        # num_legend_threshold = 20
        # legend_manager.draw_legends(p, num_legend_threshold, full_legends)

        return p


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


    def callback_scheduling(
        self,
        callback_groups: Sequence[CallbackGroup],
        xaxis_type: str,
        ywheel_zoom: bool,
        full_legends: bool,
        coloring_rule: str,
        lstrip_s: float = 0,
        rstrip_s: float = 0
    ) -> Figure:
        """
        Get callback scheduling figure.

        Parameters
        ----------
        callback_groups : Sequence[CallbackGroup]
            The target callback groups.
        xaxis_type : str, optional
            Type of x-axis of the line graph to be plotted.
            "system_time", "index", or "sim_time" can be specified.
            The default is "system_time".
        ywheel_zoom : bool, optional
            If True, the drawn graph can be expanded in the y-axis direction
            by the mouse wheel.
        full_legends : bool, optional
            If True, all legends are drawn
            even if the number of legends exceeds the threshold.
        coloring_rule : str, optional
            The unit of color change
            There are there rules which are [callback/callback_group/node], by default 'callback'
        lstrip_s : float, optional
            Start time of cropping range, by default 0.
        rstrip_s: float, optional
            End point of cropping range, by default 0.

        Returns
        -------
        bokeh.plotting.Figure

        """
        # Initialize figure
        fig_args = {
            'y_axis_label': '', 'width': 1200,
            'title': 'Callback Scheduling in '
                     f"[{'/'.join([cbg.callback_group_name for cbg in callback_groups])}]."
        }

        if xaxis_type == 'system_time':
            fig_args['x_axis_label'] = 'system time [s]'
        elif xaxis_type == 'sim_time':
            fig_args['x_axis_label'] = 'simulation time [s]'

        if ywheel_zoom:
            fig_args['active_scroll'] = 'wheel_zoom'
        else:
            fig_args['tools'] = ['xwheel_zoom', 'xpan', 'save', 'reset']
            fig_args['active_scroll'] = 'xwheel_zoom'

        p = figure(**fig_args)
        p.sizing_mode = 'stretch_width'  # type: ignore

        # Apply xaxis offset
        callbacks: List[CallbackBase] = Util.flatten(
            cbg.callbacks for cbg in callback_groups if len(cbg.callbacks) > 0)
        records_range = Range([cb.to_records() for cb in callbacks])
        range_min, range_max = records_range.get_range()
        clip_min = int(range_min + lstrip_s*1.0e9)
        clip_max = int(range_max - rstrip_s*1.0e9)
        clip = Clip(clip_min, clip_max)
        if xaxis_type == 'sim_time':
            # TODO(hsgwa): refactor
            converter = callbacks[0]._provider.get_sim_time_converter()
            frame_min = converter.convert(clip.min_ns)
            frame_max = converter.convert(clip.max_ns)
        else:
            converter = None
            frame_min = clip.min_ns
            frame_max = clip.max_ns
        x_range_name = 'x_plot_axis'
        self._apply_x_axis_offset(p, x_range_name, frame_min, frame_max)

        # Draw callback scheduling
        color_selector = ColorSelectorFactory.create_instance(coloring_rule)
        legend_manager = LegendManager()
        rect_source_gen = CallbackSchedRectSource(legend_manager, callbacks[0], clip, converter)
        bar_source_gen = CallbackSchedBarSource(legend_manager, callbacks[0], frame_min, frame_max)

        for cbg in callback_groups:
            for callback in cbg.callbacks:
                color = color_selector.get_color(
                    callback.node_name,
                    cbg.callback_group_name,
                    callback.callback_name
                )
                rect_source = rect_source_gen.generate(callback)
                rect = p.rect(
                    'x', 'y', 'width', 'height',
                    source=rect_source,
                    color=color,
                    alpha=1.0,
                    hover_fill_color=color,
                    hover_alpha=1.0,
                    x_range_name=x_range_name
                )
                legend_manager.add_legend(callback, rect)
                p.add_tools(rect_source_gen.create_hover(
                    {'attachment': 'above', 'renderers': [rect]}
                ))
                bar = p.rect(
                    'x', 'y', 'width', 'height',
                    source=bar_source_gen.generate(callback, rect_source_gen.rect_y_base),
                    fill_color=color,
                    hover_fill_color=color,
                    hover_alpha=0.1,
                    fill_alpha=0.1,
                    level='underlay',
                    x_range_name=x_range_name
                )
                p.add_tools(bar_source_gen.create_hover(
                    {'attachment': 'below', 'renderers': [bar]}
                ))

                if isinstance(callback, TimerCallback) and len(rect_source.data['y']) > 1:
                    # If the response time exceeds this value, it is considered a delay.
                    delay_threshold = 500000
                    y_start = rect_source.data['y'][1]+0.9
                    y_end = rect_source.data['y'][1]+rect_source_gen.RECT_HEIGHT
                    timer_df = callback.timer.to_dataframe()  # type: ignore
                    for row in timer_df.itertuples():
                        timer_stamp = row[1]
                        callback_start = row[2]
                        response_time = callback_start - timer_stamp
                        if pd.isna(response_time):
                            continue
                        p.add_layout(Arrow(
                            end=NormalHead(
                                fill_color='red' if response_time > delay_threshold else 'white',
                                line_width=1, size=10
                            ),
                            x_start=(timer_stamp - frame_min) * 1.0e-9, y_start=y_start,
                            x_end=(timer_stamp - frame_min) * 1.0e-9, y_end=y_end
                        ))

                rect_source_gen.update_rect_y_base()

        # Draw legends
        num_legend_threshold = 20
        """
        In Autoware, the number of callbacks in a node is less than 20.
        Here, num_legend_threshold is set to 20 as the maximum value.
        """
        legends = legend_manager.create_legends(num_legend_threshold, full_legends)
        for legend in legends:
            p.add_layout(legend, 'right')
        p.legend.click_policy = 'hide'

        p.ygrid.grid_line_alpha = 0
        p.yaxis.visible = False

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
        records_range = Range([to.to_records() for to in target_objects])
        frame_min, frame_max = records_range.get_range()
        if xaxis_type == 'system_time':
            self._apply_x_axis_offset(p, 'x_axis_plot', frame_min, frame_max)

        # Draw lines
        color_selector = ColorSelectorFactory.create_instance(coloring_rule='unique')
        legend_manager = LegendManager()
        line_source = LineSource(legend_manager, target_objects[0], frame_min, xaxis_type)
        p.add_tools(line_source.create_hover())
        for to, timeseries in zip(target_objects, timeseries_records_list):
            renderer = p.line(
                'x', 'y',
                source=line_source.generate(to, timeseries),
                color=color_selector.get_color()
            )
            legend_manager.add_legend(to, renderer)

        # Draw legends
        num_legend_threshold = 20
        """
        In Autoware, the number of callbacks in a node is less than 20.
        Here, num_legend_threshold is set to 20 as the maximum value.
        """
        legends = legend_manager.create_legends(num_legend_threshold, full_legends)
        for legend in legends:
            p.add_layout(legend, 'right')
        p.legend.click_policy = 'hide'

        return p

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

        ticker = AdaptiveTicker(min_interval=0.1, mantissas=[1, 2, 5])
        fig.xaxis.ticker = ticker
        fig.add_layout(xaxis, 'below')

        fig.x_range = Range1d(start=0, end=end_s)

        fig.xgrid.minor_grid_line_color = 'black'
        fig.xgrid.minor_grid_line_alpha = 0.1

        datetime_s = datetime.datetime.fromtimestamp(offset_s).strftime('%Y-%m-%d %H:%M:%S')
        fig.xaxis.major_label_overrides = {0: datetime_s}

        # # Code to display hhmmss for x-axis
        # from bokeh.models import FuncTickFormatter
        # fig.xaxis.formatter = FuncTickFormatter(
        #     code = '''
        #     let time_ms = (tick + offset_s) * 1e3;
        #     let date_time = new Date(time_ms);
        #     let hh = date_time.getHours();
        #     let mm = date_time.getMinutes();
        #     let ss = date_time.getSeconds();
        #     return hh + ":" + mm + ":" + ss;
        #     ''',
        #     args={"offset_s": offset_s})
