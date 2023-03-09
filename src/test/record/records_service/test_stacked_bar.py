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

from caret_analyze.record import ColumnValue
from caret_analyze.record import RecordsFactory, RecordsInterface
from caret_analyze.record import StackedBar

import pytest


def create_records(data, columns):
    records = RecordsFactory.create_instance(data, [ColumnValue(column) for column in columns])
    return records


def to_dict(records):
    return [record.data for record in records]


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
        '[worst - best] response time': [1, 1, 1],  # c1 - c0
        '/columns_1':                   [3, 3, 3],  # c4 - c1
        '/columns_4/callback_0':        [1, 1, 1],  # c5 - c4
        '/columns_5':                   [3, 3, 3],  # c8 - c5
        'start time':                   [0, 1, 2],  # c0
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

    return columns, data, expect_columns, expect_dict


class TestStackedBar:

    def test_empty_case(self):
        records: RecordsInterface = create_records([], [])
        with pytest.raises(ValueError):
            StackedBar(records)

    def test_columns(self):
        columns, data, expect_columns, _ = get_data_set()
        records: RecordsInterface = create_records(data, columns)

        stacked_bar = StackedBar(records)
        assert stacked_bar.columns == expect_columns

    def test_to_dict(self):
        columns, data, _, expect_dict = get_data_set()
        records: RecordsInterface = create_records(data, columns)

        stacked_bar = StackedBar(records)
        assert stacked_bar.to_dict() == expect_dict

    def test_records(self):
        columns, data, expect_columns, pre_expect_dict = get_data_set()
        records: RecordsInterface = create_records(data, columns)
        expect_columns += ['start time']
        expect_dict = []
        for i in range(len(pre_expect_dict[expect_columns[0]])):
            d = {}
            for column in expect_columns:
                d[column] = pre_expect_dict[column][i]
            expect_dict.append(d)

        stacked_bar = StackedBar(records)
        result = to_dict(stacked_bar.records)
        assert result == expect_dict

    # def test_flow(self):
    #     from caret_analyze import Architecture, Lttng, Application
    #     arch_file = "/home/emb4/tmp_tracedata/stacked_bar/arch_stacked_bar.yaml"
    #     # trace_data = "test03_main"
    #     trace_data = "/home/emb4/tmp_tracedata/test09"
    #     target_path1 = "target_path1"
    #     target_path2 = "target_path2"
    #     answer_path = "answer_path"
    #     arch = Architecture('yaml', arch_file)
    #     lttng = Lttng(trace_data)
    #     app = Application(arch, lttng)
    #     path1= arch.get_path(target_path1)
    #     path2 = arch.get_path(target_path2)
    #     answer = arch.get_path(answer_path)
    #     from caret_analyze.plot import Plot
    #     path1= arch.get_path(target_path1)
    #     path = app.get_path(target_path1)
    #     print(type(path))
    #     plot = Plot.create_response_time_stacked_bar_plot(path, case='best')
    #     plot.figure()

    # def test_timeseres(self):
    #     from caret_analyze import Lttng, LttngEventFilter
    #     from caret_analyze.plot import Plot
    #     from caret_analyze import Architecture, Lttng, Application
    #     arch_file = "/home/emb4/tmp_tracedata/stacked_bar/arch_stacked_bar.yaml"
    #     # trace_data = "test03_main"
    #     trace_data = "/home/emb4/tmp_tracedata/test09"
    #     target_path1 = "target_path1"
    #     target_path2 = "target_path2"
    #     answer_path = "answer_path"

    #     arch = Architecture('yaml', arch_file)
    #     lttng = Lttng(trace_data, event_filters=[
    #         LttngEventFilter.duration_filter(10, 5)])
    #     app = Application(arch, lttng)

    #     plot = Plot.create_callback_period_plot(app.callbacks)
    #     plot.show()