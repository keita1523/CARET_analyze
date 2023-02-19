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
from ..record_factory import RecordsFactory
from ..record import Columns, ColumnValue
from ..record_factory import RecordFactory
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
        self._diff_response_time_name = '[worst - best] response time'
        rename_map: Dict[str, str] = \
            self._get_rename_column_map(self._records.columns)
        renamed_records: RecordsInterface = \
            self._rename_columns(self._records, rename_map)
        columns = list(rename_map.values())
        if len(columns) < 2:
            raise ValueError(f'Column size is {len(columns)} and must be more 2.')

        # output_dict: Dict[str, List[int]] = {}
        # # add x axis values
        # output_dict['start timestamp'] = renamed_records.get_column_series(columns[0])

        # add stacked bar data
        xlabel: str = 'start time'
        x_axis_values: RecordsInterface = self._get_x_axis_values(renamed_records, self._diff_response_time_name, xlabel)
        stacked_bar_records = self._to_stacked_bar_records(renamed_records, columns)
        stacked_bar_records = \
            self._append_column_series(
                stacked_bar_records,
                x_axis_values.get_column_series(xlabel),
                xlabel,
            )
        # stacked_bar_records.append_column(ColumnValue(x_axis_values.columns[0]), x_axis_values.get_column_series(x_axis_values.columns[0]))
        # stacked_bar_records = self._add_x_axis_keys(stacked_bar_records, 'start time')
        self._stacked_bar_dict = self._to_dict(stacked_bar_records)
        # output_dict.update(self._get_stacked_bar_dict(renamed_records, columns))
        self._columns = columns[:-1]

    def _get_x_axis_values(
        self,
        records: RecordsInterface,
        column: str,
        xlabel: str,
    ) -> RecordsInterface:
        # data = {column : records.get_column_series(column)}
        # label = 'start time'

        # record: RecordsInterface = \
        #     RecordsFactory.create_instance([], [ColumnValue(column)])
        series = records.get_column_series(column)
        record_dict = [{xlabel : _ } for _ in series]
        record = RecordsFactory.create_instance(record_dict, [ColumnValue(xlabel)])
        # records = self._append_column_series(records, records.get_column_series(column), column)

        return record

    @staticmethod
    def _add_x_axis_keys(
        records: RecordsInterface,
        x_key: str,
    ) -> RecordsInterface:
        record: RecordsInterface = \
            RecordsFactory.create_instance(records.get_row_series(0), )

    @property
    def get_stacked_dict(self) -> Dict[str, List[int]]:
        # return stacked bar data
        return self._stacked_bar_dict

    @property
    def get_columns(self) -> List[str]:
        return self._columns

    @staticmethod
    def _append_column_series(
        records: RecordsInterface,
        series: List[int],
        column: str,
    ) -> RecordsInterface:

        record_dict = [{column : t} for t in series]

        if len(records.data) == 0:
            new_records: RecordsInterface = \
                RecordsFactory.create_instance(record_dict, [ColumnValue(column)])
            records.concat(new_records)
        else:
            records.append_column(ColumnValue(column), series)
        return records
        # return new_records

    @staticmethod
    def _to_dict(records: RecordsInterface) -> Dict[str, List[int]]:
        columns = records.columns
        output_dict: Dict[str, List[int]] = {}
        for column in columns:
            output_dict[column] = records.get_column_series(column)
        return output_dict



    def _to_stacked_bar_records(
        self,
        records: RecordsInterface,
        columns: List[str],
    ) -> RecordsInterface:
        output_records: RecordsInterface = RecordsFactory.create_instance()
        record_size = len(records.data)
        for column in columns[:-1]:
            output_records.append_column(ColumnValue(column), [])

        for column_from, column_to in zip(columns[:-1], columns[1:]):
            latency_handler = Latency(records, column_from, column_to)
            assert record_size == len(latency_handler.to_records())

            latency_records = latency_handler.to_records()
            latency = latency_records.get_column_series('latency')

            output_records = self._append_column_series(output_records, list(latency), column_from)

        return output_records


    # @staticmethod
    def _get_rename_column_map(
        self,
        raw_columns: List[str],
    ) -> Dict[str, str]:

        rename_map: Dict[str, str] = {}
        end_word: str = '_min'
        for column in raw_columns:
            if column.endswith(end_word):
                rename_map[column] = self._diff_response_time_name
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
        # column_value = Columns(columns)
        output_records: RecordsInterface = RecordsFactory.create_instance([],[])
        # output_records.append_column(columns[:-1], [])

        for column_from, column_to in zip(columns[:-1], columns[1:]):
            latency = Latency(records, column_from, column_to)
            assert record_size == len(latency.to_records())
            latency_records = latency.to_records()
            # RecordFactory.create_instance()
            a = latency_records.get_column_series('latency')
            output_records.append_column(ColumnValue(column_from), [])
            output_dict[column_from] = latency_records.get_column_series('latency')
            # output_records.data[column_from] = latency_records.get_column_series('latency')
            output_records.append(ColumnValue(column_from), latency_records.get_column_series('latency'))
            # output_records.concat(latency_records.get_column_series('latency'))
        return dict(output_dict)