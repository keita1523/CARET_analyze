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


# from ..column import ColumnValue
from ..interface import RecordsInterface
# from ..record_factory import RecordsFactory
from .latency import Latency


from typing import Dict, List, Sequence, Tuple, Union

import pandas as pd

# from ...record import Latency, RecordsInterface
# from ...runtime import CallbackBase, Communication, Path

# from caret_analyze.record import ResponseTime
from collections import defaultdict

class StackedBar:
    def __init__(
        self,
        records: RecordsInterface,
) -> None:
        # rename columns to nodes and topics granularity
        self._records = records
        rename_map: Dict[str, str] = \
            self._get_rename_column_map(self._records.columns)
        renamed_records: RecordsInterface = \
            self._rename_columns(self._records, rename_map)
        columns = list(rename_map.values())
        if len(columns) < 2:
            raise ValueError(f'Column size is {len(columns)} and must be more 2.')

        output_dict: Dict[str, List[int]] = {}
        # add x axis values
        output_dict['start timestamp'] = renamed_records.get_column_series(columns[0])

        # add stacked bar data
        output_dict.update(self._get_stacked_bar_dict(renamed_records, columns))

        self._stacked_bar_dict = output_dict
        self._columns = columns[:1]

    def get_dict(self) -> RecordsInterface:


        # return stacked bar data
        return self._stacked_bar_dict

    def get_columns(self) -> List[str]:
        return self._columns


    @staticmethod
    def _get_rename_column_map(
        raw_columns: List[str],
    ) -> Dict[str, str]:

        rename_map: Dict[str, str] = {}
        for column in raw_columns:
            if column.endswith('_min'):
                rename_map[column] = '/'
            elif 'rclcpp_publish' in column:
                topic_name = column.split('/')[:-2]
                rename_map[column] = '/'.join(topic_name)
            elif 'callback_start' in column:
                node_name = column.split('/')[:-2]
                rename_map[column] = '/'.join(node_name)

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
    def _get_stacked_bar_dict(
        records: RecordsInterface,
        columns: List[str],
    ) -> Dict[str, List[int]]:
        output_dict = defaultdict(list)
        record_size = len(records.data)

        for column_from, column_to in zip(columns[:-1], columns[1:]):
            latency = Latency(records, column_from, column_to)
            assert record_size == len(latency.to_records())
            latency_records = latency.to_records()
            output_dict[column_from] = latency_records.get_column_series('latency')

        return dict(output_dict)