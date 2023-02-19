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
import pandas as pd

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

def get_data_set():
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

    return data, columns, expect_dict, expect_columns


class TestLatencyStackedBar:

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


    def test_empty_case(self, create_mock):
        data = []
        columns = []
        stacked_bar_plot: LatencyStackedBar = create_mock(data, columns)
        with pytest.raises(ValueError):
            stacked_bar_plot.to_stacked_bar_dict()


    def test_default_case(self, create_mock):
        data, columns, expect_dict, expect_columns = get_data_set()
        # create mock
        stacked_bar_plot: LatencyStackedBar = create_mock(data, columns)

        # create stacked bar data
        output_dict, output_columns = stacked_bar_plot.to_stacked_bar_dict()

        assert output_dict == expect_dict
        assert output_columns == expect_columns

    def test_to_dataframe(self, create_mock):
        data, columns, expect_dict, expect_columns = get_data_set()
        # create mock
        stacked_bar_plot: LatencyStackedBar = create_mock(data, columns)
        for column in expect_columns:
            expect_dict[column] = [timestamp * 1e-6 for timestamp in expect_dict[column]]
        expect_df = pd.DataFrame(expect_dict)


        # create stacked bar data
        output_df = stacked_bar_plot.to_dataframe()
        assert output_df.equals(expect_df)