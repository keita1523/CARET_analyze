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

from typing import Union

from bokeh.plotting import Figure

import pandas as pd

from ..metrics_base import MetricsBase
from ..plot_base import PlotBase
from ..visualize_lib import VisualizeLibInterface
from ...exceptions import UnsupportedTypeError
from ...runtime import CallbackBase, Communication, Publisher, Subscription, Path

from caret_analyze.runtime.path import Path
from caret_analyze.record.record_factory import RecordsFactory
from caret_analyze.record.column import ColumnValue
from caret_analyze.record import ResponseTime
from .latency_stacked_bar import LatencyStackedBar

StackedBarTypes = Union[Path]
# https://qiita.com/nkay/items/a9cac036d648084196f4


class StackedBarPlot(PlotBase):
    """
    Class that provides API of Stacked Bar graph.

    Parameters
    ----------
    PlotBase : _type_
        _description_
    """

    def __init__(
        self,
        metrics: LatencyStackedBar,
        visualize_lib: VisualizeLibInterface
    ) -> None:
        self._metrics = metrics
        self._visualize_lib = visualize_lib

    def figure(
        self,
        xaxis_type: str = 'system_time',
        ywheel_zoom: bool = True,
        full_legends: bool = False,
    ) -> Figure:
        return self._visualize_lib.stacked_bar(
            self._metrics,
            xaxis_type,
            ywheel_zoom,
            full_legends,
        )

    def to_dataframe(self, xaxis_type: str = 'system_time') -> pd.DataFrame:
        # return super().to_dataframe(xaxis_type)
        return self._metrics.to_dataframe(xaxis_type)