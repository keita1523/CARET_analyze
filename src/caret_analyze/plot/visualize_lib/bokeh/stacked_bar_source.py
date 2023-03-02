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

from typing import Dict, List, Optional, Sequence, Tuple, Union

from bokeh.models import HoverTool
from bokeh.plotting import ColumnDataSource

from .legend import HoverCreator, LegendKeys, LegendManager, LegendSource

from ....record import RecordsInterface
from ....runtime import CallbackBase, Communication, Publisher, Subscription

class StackedBarSource:
    """Class to generate stacked bar source"""

    def __init__(
        self,
        legend_manager: LegendManager,
        target_object,
        frame_min: float,
        xaxis_type: str,
    ) -> None:
        self._legend_keys = LegendKeys('stacked_bar', target_object)
        self._hover = HoverCreator(self._legend_keys)
        self._legend_source = LegendSource(legend_manager, self._legend_keys)
        self._frame_min = frame_min
        self._xaxis_type = xaxis_type

    def create_hover(self, options: dict = {}) -> HoverTool:
        """
        Create HoverTool based on the legend keys.

        Parameters
        ----------
        options : dict, optional
            Additional options, by default {}

        Returns
        -------
        HoverTool

        """
        return self._hover.create(options)

    @staticmethod
    def generate(
        data: Dict[str, list[float]],
        y_labels: List[str],
        bottom_labels: List[str],
        x_width_list: List[float],
    ) -> ColumnDataSource:
        source = ColumnDataSource(data)
        source.add(y_labels, 'legend')
        source.add(x_width_list, 'x_width_list')
        for y_label, bottom_label in zip(y_labels[1:], bottom_labels):
            source.add(data[y_label], bottom_label)
        return source
