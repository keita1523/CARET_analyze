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

from typing import Dict, List, Sequence, Tuple, Union

import pandas as pd

from ..metrics_base import MetricsBase
from ...record import Latency, RecordsInterface
from ...runtime import CallbackBase, Communication, Path

from caret_analyze.record import ResponseTime
from collections import defaultdict


class LatencyStackedBar:
    def __init__(
        self,
        target_objects: Path,
        granularity: str = 'node',
    ) -> None:
        self._target_objects = target_objects
        self._granularity = granularity


    @property
    def target_objects(self) -> Path:
        return self._target_objects

    def to_stacked_bar_records_list(
        self,
    ):
        stacked_bar_records_list: List[RecordsInterface] = []
        output_list = defaultdict(list)
        object = self._target_objects
        response_time = ResponseTime(object.to_records(), columns=object.column_names)
        response_records = response_time.to_response_records() # include timestamp of response time (best, worst)
        raw_columns = response_records.columns

        if self._granularity == 'node':
            new_clumns = []
            for column in raw_columns:
                if '0_min' in column:
                    new_clumns.append(column)
                elif 'rclcpp_publish' in column:
                    new_clumns.append(column)
                elif 'callback_start' in column:
                    new_clumns.append(column)
            new_clumns.append(raw_columns[-1])
            columns = new_clumns
        else:
            columns = raw_columns

        assert len(columns) >= 2
        record_size = len(response_records.data)
        x_label = []
        for column_from, column_to in zip(columns[:-1], columns[1:]):
            latency = Latency(response_records, column_from, column_to)
            # stacked_bar_records_list.append(latency.to_records())

            assert record_size == len(latency.to_records())
            for record in latency.to_records():
                if '0_max' in column_to:
                    x_label.append(record.data[columns[0]] * 10e-9)
                output_list[column_from].append(record.data['latency'] * 10e-9)



        # output_list['start timestamp'] = list(range(record_size))
        output_list['start timestamp'] = x_label
        return output_list, columns[:-1]

    def to_dataframe(self):
        raise NotImplementedError()

