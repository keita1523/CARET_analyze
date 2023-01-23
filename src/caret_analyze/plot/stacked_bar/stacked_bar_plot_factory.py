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

from typing import Sequence, Union, Optional

from .stacked_bar_plot import StackedBarPlot
from .latency_stacked_bar import LatencyStackedBar
from ..metrics_base import MetricsBase
from ..visualize_lib import VisualizeLibInterface
from ...common import type_check_decorator
from ...exceptions import UnsupportedTypeError
from ...runtime import CallbackBase, Communication, Path, Publisher, Subscription


StackedBarTypes = Union[Path]

class StackedBarPlotFactory:
    """Factory class to create an instance of StackedBarPlot."""

    @staticmethod
    # @type_check_decorator
    def create_instance(
        target_objects: Path,
        visualize_lib: VisualizeLibInterface,
        metrics: str = 'latency',
        granularity: str = 'node',
    ) -> StackedBarPlot:
        """_summary_

        Parameters
        ----------
        target_objects : StackedBarTypes
            _description_
        metrics : str
            Metrics for stacked bar graph.
            supported metrics: [normal, percentage]
        visualize_lib : VisualizeLibInterface
            _description_

        Returns
        -------
        StackedBarPlot
            _description_
        """
        # metrics_: MetricsBase
        if metrics == 'latency':
            metrics_ = LatencyStackedBar(target_objects, granularity)
            return StackedBarPlot(metrics_, visualize_lib)
        elif metrics == 'percentage':
            # TODO
            raise NotImplementedError()
        else:
            raise UnsupportedTypeError(
                'Unsupported metrics specified. '
                'Supported metrics: [frequency/latency/period]'
            )
