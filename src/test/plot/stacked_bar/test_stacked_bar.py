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

from caret_analyze import Architecture, Lttng, Application
from caret_analyze.value_objects import PathStructValue
from caret_analyze.runtime import NodePath, Path
from caret_analyze.plot.stacked_bar import StackedBarPlot
from caret_analyze.plot.stacked_bar import LatencyStackedBar
from caret_analyze.record import ResponseTime, ColumnValue
from caret_analyze.record import RecordsFactory, RecordInterface, RecordsInterface
from caret_analyze.record.record_cpp_impl import RecordsCppImpl

from collections import defaultdict, UserList
import pytest

@pytest.fixture
def create_mock(mocker):
    def _create_mock(data, columns):
        records = RecordsFactory.create_instance(data, [ColumnValue(column) for column in columns])
        target_objects = mocker.Mock(spec=Path)
        stacked_bar_plot = LatencyStackedBar(target_objects)
        column_map = {}
        for column in columns:
            column_map[column] = column + '_renamed'
        mocker.patch.object(stacked_bar_plot, '_get_response_time_record', return_value=records)
        mocker.patch.object(stacked_bar_plot, '_get_rename_column_map', return_value=column_map)
        return stacked_bar_plot
    return _create_mock

class TestStackedBar:

    def test_empty_case(self, create_mock):
        columns = []
        data = []

        stacked_bar_plot: LatencyStackedBar = create_mock(data, columns)
        with pytest.raises(ValueError):
            stacked_bar_plot.to_stacked_bar_records_dict()

    def test_normal(self, create_mock):
        columns = [
            'columns_0_min',
            'columns_0_max',
            'columns_1',
            'columns_2',
        ]

        # create data
        # # data[0] = {
        # #     'columns_0_min' : 1,
        # #     'columns_0_max' : 2,
        # #     'columns_1' : 3,
        # #     'columns_2' : 4,
        # # }
        # # data[1] = {
        # #     'columns_0_min' : 2,
        # #     'columns_0_max' : 3,
        # #     'columns_1' : 4,
        # #     'columns_2' : 5,
        # # }
        # # data[2] = {
        # #     'columns_0_min' : 3,
        # #     'columns_0_max' : 4,
        # #     'columns_1' : 5,
        # #     'columns_2' : 6,
        # # }
        data_num = 3
        data = []
        for i in range(data_num):
            d = {}
            for j in range(len(columns)):
                d[columns[j]] = i + j
            data.append(d)

        # create expected outputs
        expect_dict = {
            'start timestamp' : [0, 1, 2],
            'columns_0_min_renamed': [1, 1, 1],
            'columns_0_max_renamed': [1, 1, 1],
            'columns_1_renamed': [1, 1, 1],
        }
        expect_columns = [
            'columns_0_min_renamed',
            'columns_0_max_renamed',
            'columns_1_renamed',
        ]

        # main
        stacked_bar_plot: LatencyStackedBar = create_mock(data, columns)
        output_dict, output_columns = stacked_bar_plot.to_stacked_bar_records_dict()

        assert output_dict == expect_dict
        assert output_columns == expect_columns

    def test_get_target_columns(self, mocker):
        target_objects = mocker.Mock(spec=Path)
        stacked_bar_plot = LatencyStackedBar(target_objects)
        columns = [
            'columns_0/rclcpp_publish/0_min',
            'columns_1/rclcpp_publish/0_max',
            'columns_2/callback_start/0',
            'columns_3/rclcpp_publish/0',
            'columns_4/rcl_publish/0',
            'columns_5/dds_write/0',
            'columns_6/callback_start/0',
        ]
        expect_map = {
            'columns_0/rclcpp_publish/0_min' : '/response_time',
            'columns_1/rclcpp_publish/0_max' : 'columns_1',
            'columns_2/callback_start/0' : 'columns_2',
            'columns_3/rclcpp_publish/0' : 'columns_3',
            'columns_6/callback_start/0' : 'columns_6',
        }
        output_map = stacked_bar_plot._get_rename_column_map(columns)
        assert output_map == expect_map

