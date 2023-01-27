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

    def test_stacked_bar(self, mocker):
        target_objects = mocker.Mock(spec=Path)
        # records = mocker.Mock(spec=RecordsInterface)
        columns = [
            'columns_0_min',
            'columns_0_max',
            'columns_1',
            'columns_2',
        ]
        # columns = [ColumnValue(column) for column in columns]

        num = 3
        data = []
        for i in range(num):
            # d = defaultdict(int)
            d = {}
            for j in range(len(columns)):
                d[columns[j]] = i + j
            data.append(d)
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
        coloumn_map = {}
        for column in columns:
            coloumn_map[column] = column + '_renamed'


        records = RecordsFactory.create_instance(data, [ColumnValue(column) for column in columns])



        # mocker.patch.object(target_objects, 'to_records', columns)
        # mocker.patch.object(target_objects, 'column_names', columns)

        # mocker.patch.object(target_objects, 'to_records')
        records_cpp_impl = mocker.Mock(spec=RecordInterface)
        mocker.patch.object(records_cpp_impl, 'columns', columns)
        mocker.patch.object(records_cpp_impl, 'data', [data])



        # response_time = mocker.Mock(spec=ResponseTime)
        # mocker.patch.object(response_time, '_get_response_time_record', records_cpp_impl)

        stacked_bar_plot = LatencyStackedBar(target_objects)
        mocker.patch.object(stacked_bar_plot, '_get_response_time_record', return_value=records)
        mocker.patch.object(stacked_bar_plot, '_get_rename_column_map', return_value=coloumn_map)
        # mocker.patch.object(stacked_bar_plot, '_rename_columns', return_value=coloumn_map)
        output_dict, output_columns = stacked_bar_plot.to_stacked_bar_records_list()
        # expect_dict = {}
        assert output_dict == expect_dict
        assert output_columns == expect_columns

    def test_get_target_columns(self, mocker):
        target_objects = mocker.Mock(spec=Path)
        stacked_bar_plot = LatencyStackedBar(target_objects)
        columns = [
            'columns_0_min',
            'columns_0_max',
            'columns_1',
            'columns_2',
        ]
        expect_columns = []
        output_columns = stacked_bar_plot._get_columns_map(columns)
        assert output_columns == expect_columns



