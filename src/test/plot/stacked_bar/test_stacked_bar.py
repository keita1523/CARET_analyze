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
from caret_analyze.runtime.path import ColumnMerger, RecordsMerged
# from caret_analyze.plot.stacked_bar import StackedBarPlot
from caret_analyze.plot.stacked_bar import LatencyStackedBar
from caret_analyze.record import ResponseTime, ColumnValue
from caret_analyze.record import RecordsFactory, RecordsInterface
# from caret_analyze.record.record_cpp_impl import RecordsCppImpl

# from collections import defaultdict, UserList
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
        # mocker.patch.object(stacked_bar_plot, '_get_rename_column_map', return_value=column_map)
        return stacked_bar_plot
    return _create_mock

class TestStackedBar:

    def test_flow(self):

        arch_file = "/home/emb4/tmp_tracedata/stacked_bar/arch_stacked_bar.yaml"
        # trace_data = "test03_main"
        trace_data = "/home/emb4/tmp_tracedata/test09"
        target_path1 = "target_path1"
        target_path2 = "target_path2"
        answer_path = "answer_path"

        arch = Architecture('yaml', arch_file)
        lttng = Lttng(trace_data)
        app = Application(arch, lttng)

        path1= arch.get_path(target_path1)
        path2 = arch.get_path(target_path2)
        answer = arch.get_path(answer_path)

        from caret_analyze.plot import Plot

        path1= arch.get_path(target_path1)
        path = app.get_path(target_path1)
        print(type(path))

        plot = Plot.create_response_time_stacked_bar_plot(path)
        plot.figure()


    def test_empty_case(self, mocker, create_mock):
        # columns = []
        # data = []

        # stacked_bar_plot: LatencyStackedBar = create_mock(data, columns)
        # with pytest.raises(ValueError):
        #     stacked_bar_plot.to_stacked_bar_records_dict()
        # column_merger_mock = mocker.Mock(spec=ColumnMerger)
        # mocker.patch('caret_analyze.runtime.path.ColumnMerger',
        #              return_value=column_merger_mock)

        # records_merged_mock = mocker.Mock(spec=RecordsMerged)
        # mocker.patch('caret_analyze.runtime.path.RecordsMerged',
        #              return_value=records_merged_mock)

        # records_mock = mocker.Mock(spec=RecordsInterface)
        # mocker.patch.object(records_mock, 'clone', return_value=records_mock)
        # mocker.patch.object(records_mock, 'columns', [])

        # mocker.patch.object(column_merger_mock, 'column_names', [])
        # mocker.patch.object(records_merged_mock, 'data', records_mock)

        # path_info_mock = mocker.Mock(spec=PathStructValue)
        # mocker.patch.object(path_info_mock, 'path_name', 'name')
        # path = Path(path_info_mock, [], None)
        # stacked_bar_plot = LatencyStackedBar(path)
        data = []
        columns = []
        stacked_bar_plot: LatencyStackedBar = create_mock(data, columns)
        with pytest.raises(ValueError):
            stacked_bar_plot.to_stacked_bar_records_dict()

    # def test_code(self, mocker):


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

    def test_normal_case(self, mocker, create_mock):
        columns = [
            '/columns_0/rclcpp_publish_timestamp/0_min',
            '/columns_1/rclcpp_publish_timestamp/0_max',
            '/columns_2/rcl_publish_timestamp/0',
            '/columns_3/dds_write_timestamp/0',
            '/columns_4/callback_0/callback_start_timestamp/0',
            '/columns_5/rclcpp_publish_timestamp/0_max',
            '/columns_6/rcl_publish_timestamp/0',
            '/columns_7/dds_write_timestamp/0',
            '/columns_8/callback_0/callback_start_timestamp/0',
        ]

        # create input and expect data
        # # columns | c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 |
        # # ======================================================
        # # data    | 0  | 1  | 2  | 3  | 4  | 5  | 6  | 7  | 8  |
        # #         | 1  | 2  | 3  | 4  | 5  | 6  | 7  | 8  | 9  |
        # #         | 2  | 3  | 4  | 5  | 6  | 7  | 8  | 9  | 10 |

        expect_dict = {
            '[worst - best] response time' : [1, 1, 1], # c1 - c0
            '/columns_1'                   : [3, 3, 3], # c4 - c1
            '/columns_4/callback_0'        : [1, 1, 1], # c5 - c4
            '/columns_5'                   : [3, 3, 3], # c8 - c5
            'start time'                   : [0, 1, 2], # c0
        }
        expect_columns = [
            '[worst - best] response time',
            '/columns_1',
            '/columns_4/callback_0',
            '/columns_5',
        ]

        data_num = 3
        data = []
        for i in range(data_num):
            d = {}
            for j in range(len(columns)):
                d[columns[j]] = i + j
            data.append(d)

        # create mock
        stacked_bar_plot: LatencyStackedBar = create_mock(data, columns)

        # create stacked bar data
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

