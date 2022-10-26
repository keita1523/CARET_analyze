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

from typing import List, Optional

from .column import ColumnValue
from .interface import RecordsInterface
from .record_factory import RecordFactory, RecordsFactory


class Latency:

    def __init__(
        self,
        records: RecordsInterface,
        start_column: Optional[str] = None,
        end_column: Optional[str] = None
    ) -> None:
        """
        Constructor.

        Parameters
        ----------
        records : RecordsInterface
            records to calculate latency.
        start_column : Optional[str], optional
            Column name of start timestamps used in the calculation, by default None
            If None, the first column of records is selected.
        end_column : Optional[str], optional
            Column name of end timestamps used in the calculation, by default None
            If None, the last column of records is selected.

        """
        self._start_column = start_column or records.columns[0]
        self._end_column = end_column or records.columns[-1]

        self._start_timestamps: List[int] = []
        self._end_timestamps: List[int] = []
        for record in records:
            if (self._start_column not in record.columns or
                    self._end_column not in record.columns):
                continue
            start_ts = record.get(self._start_column)
            self._start_timestamps.append(start_ts)
            end_ts = record.get(self._end_column)
            self._end_timestamps.append(end_ts)

    def to_records(self) -> RecordsInterface:
        """
        Calculate latency records.

        Returns
        -------
        RecordsInterface
            latency records.
            Columns
            - {start_timestamp_column}
            - {latency_column}

        """
        records = self._create_empty_records()

        for start_ts, end_ts in zip(self._start_timestamps, self._end_timestamps):
            records.append(RecordFactory.create_instance(
                {self._start_column: start_ts,
                 'latency': end_ts - start_ts}
            ))

        return records

    def _create_empty_records(
        self
    ) -> RecordsInterface:
        return RecordsFactory.create_instance(columns=[
            ColumnValue(self._start_column), ColumnValue('latency')
        ])