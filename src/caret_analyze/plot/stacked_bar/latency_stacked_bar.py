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
    ) -> None:
        self._target_objects = target_objects


    @property
    def target_objects(self) -> Path:
        return self._target_objects

    @staticmethod
    def _get_response_time_record(
        target_object: Path
    ) -> List[RecordsInterface]:
        response_time = ResponseTime(target_object.to_records(),
                                     columns=target_object.column_names)
        # include timestamp of response time (best, worst)
        return response_time.to_response_records()

    @staticmethod
    def _get_rename_column_map(
        raw_columns: List,
    ) -> Dict:

        rename_map = {}
        for column in raw_columns:
            # if '0_min' in column:
            if column.endswith('_min'):
                rename_map[column] = '/response_time'
                # new_clumns.append('response time')
            elif 'rclcpp_publish' in column:
                topic_name = column.split('/')[:-2]
                rename_map[column] = '/'.join(topic_name)
            elif 'callback_start' in column:
                node_name = column.split('/')[:-2]
                rename_map[column] = '/'.join(node_name)

        # new_clumns.append(raw_columns[-1])
        return rename_map

    @staticmethod
    def _rename_columns(
        records: RecordsInterface,
        rename_map: Dict[str, str],
    ):
        for before, after in rename_map.items():
            records.rename_columns({before : after})
        return records

    @staticmethod
    def _get_start_timestamps(
        records: RecordsInterface,
        first_tracepoint: str,
    ) -> List:
        timestamps = []
        for record in records:
            timestamps.append(record.data[first_tracepoint])
        return timestamps

    def to_stacked_bar_records_list(
        self,
    ):
        stacked_bar_records_list: List[RecordsInterface] = []
        output_dict = defaultdict(list)
        # output_dict = {}
        # object = self._target_objects
        # response_time = ResponseTime(object.to_records(), columns=object.column_names)
        # response_records = response_time.to_response_records() # include timestamp of response time (best, worst)
        response_records = self._get_response_time_record(self._target_objects)
        # raw_columns = response_records.columns
        rename_map = self._get_rename_column_map(response_records.columns)
        response_records = self._rename_columns(response_records, rename_map)
        columns = list(rename_map.values())
        # for before, after in column_map.items():
        #     response_records.rename_columns({before : after})
        # columns = response_records.columns



        assert len(columns) >= 2
        record_size = len(response_records.data)
        start_timestamps = []
        output_dict['start timestamp'] = self._get_start_timestamps(response_records, columns[0])

        for column_from, column_to in zip(columns[:-1], columns[1:]):
            latency = Latency(response_records, column_from, column_to)
            # stacked_bar_records_list.append(latency.to_records())
            assert record_size == len(latency.to_records())
            for record in latency.to_records():
                if '/response_time' in column_from:
                    start_timestamps.append(record.data[columns[0]])
                output_dict[column_from].append(record.data['latency'])


        # output_list['start timestamp'] = list(range(record_size))
        # return dict(output_dict), columns[:-1]
        return dict(output_dict), columns[:-1]

    def to_dataframe(self):
        raise NotImplementedError()

