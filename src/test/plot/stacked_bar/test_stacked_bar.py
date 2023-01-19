

class TestStackedBar:

    def test_stacked_bar(self):
        from caret_analyze import Architecture, Lttng, Application
        from caret_analyze.value_objects import PathStructValue
        from caret_analyze.runtime import NodePath

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

