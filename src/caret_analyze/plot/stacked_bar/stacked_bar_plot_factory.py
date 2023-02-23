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

from .latency_stacked_bar import LatencyStackedBar
from .stacked_bar_plot import StackedBarPlot
from ..visualize_lib import VisualizeLibInterface
from ...exceptions import UnsupportedTypeError
from ...runtime import Path


class StackedBarPlotFactory:
    """Factory class to create an instance of StackedBarPlot."""

    @staticmethod
    def create_instance(
        target_objects: Path,
        visualize_lib: VisualizeLibInterface,
        metrics: str = 'latency',
    ) -> StackedBarPlot:
        """
        Create stacked bar class.

        Parameters
        ----------
        target_objects : Path
            Target path
        metrics : str
            Metrics for stacked bar graph.
            supported metrics: [latency]
        visualize_lib : VisualizeLibInterface
            Instance of VisualizeLibInterface used for visualization.

        Returns
        -------
        StackedBarPlot
            StackedBarPlot

        """
        if metrics == 'latency':
            metrics_ = LatencyStackedBar(target_objects)
            return StackedBarPlot(metrics_, visualize_lib)
        elif metrics == 'percentage':
            # TODO
            raise NotImplementedError()
        else:
            raise UnsupportedTypeError(
                'Unsupported metrics specified. '
                'Supported metrics: [latency]'
            )
