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

from typing import List, Sequence, Union

import pandas as pd

from ..metrics_base import MetricsBase
from ...record import Latency, RecordsInterface
from ...runtime import CallbackBase, Communication, Path

from caret_analyze.record import ResponseTime
from collections import defaultdict


class LatencyStackedBar:
    def __init__(
        self,
        target_objects: Path
    ) -> None:
        self._target_objects = target_objects


    @property
    def target_objects(self) -> Path:
        return self._target_objects

    def to_stacked_bar_records_list(self):
        stacked_bar_records_list: List[RecordsInterface] = []
        output_list = defaultdict(list)
        object = self._target_objects
        response_time = ResponseTime(object.to_records(), columns=object.column_names)
        response_records = response_time.to_response_records() # include response time (min, max)
        columns = response_records.columns
        record_size = len(response_records.data)
        output_list2 = {}
        for column_from, column_to in zip(columns[:-1], columns[1:]):
            # diff = data.data[column_to] - data.data[column_from]
            latency = Latency(response_records, column_from, column_to)
            stacked_bar_records_list.append(latency.to_records())
            d = defaultdict(list)
            index = 0

            assert record_size == len(latency.to_records())
            for record in latency.to_records():
                # if '_min' in column_from: # if column_from includes '/topic1/rclcpp_publish_timestamp/0_max'
                #     d[record.data[column_from]].append(record.data['latency'])
                #     output_list[index] = [record.data['latency']]
                # else:
                #     output_list[index].append(record.data['latency'])
                # index += 1
                output_list[column_from].append(record.data['latency'])


        # for column in columns[:-1]:
        #     for stacked_bar_record in stacked_bar_records_list:
        #         output_list['']



        # for column_from, column_to in zip(columns[:-1], columns[1:]):




        # output_list['start timestamp'] = output_list[columns[0]]
        output_list['start timestamp'] = list(range(record_size))
        return output_list, columns[:-1]

    def to_dataframe(self):
        raise NotImplementedError()

