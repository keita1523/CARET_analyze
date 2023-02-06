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
from ...record import RecordsInterface, StackedBar
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
    ) -> RecordsInterface:
        response_time = ResponseTime(target_object.to_records(),
                                     columns=target_object.column_names)
        # include timestamp of response time (best, worst)
        return response_time.to_response_records()

    def to_stacked_bar_records_dict(
        self,
    ): # -> Dict[str, List[int]], List[str]
        response_records: RecordsInterface = \
            self._get_response_time_record(self._target_objects)

        # # rename columns to nodes and topics granularity
        # rename_map: Dict[str, str] = \
        #     self._get_rename_column_map(response_records.columns)
        # renamed_records: RecordsInterface = \
        #     self._rename_columns(response_records, rename_map)
        # columns = list(rename_map.values())
        # if len(columns) < 2:
        #     raise ValueError(f'Column size is {len(columns)} and must be more 2.')

        # # add x axis values
        # output_dict['start timestamp'] = renamed_records.get_column_series(columns[0])

        # # add stacked bar data
        # output_dict.update(self._get_stacked_bar_dict(renamed_records, columns))

        # # return stacked bar data and column_get_stacked_bar_dicts
        stacked_bar = StackedBar(response_records)
        return stacked_bar.get_dict, stacked_bar.get_columns

    def to_dataframe(self, xaxis_type: str = 'system_time'):
        stacked_bar_dict, columns = self.to_stacked_bar_records_dict()
        for column in columns:
            stacked_bar_dict[column] = [timestamp * 1e-6 for timestamp in stacked_bar_dict[column]]
        # df = pd.DataFrame(stacked_bar_dict, dtype='Int64')
        df = pd.DataFrame(stacked_bar_dict)
        return df


