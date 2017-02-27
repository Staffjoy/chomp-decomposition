from chomp import Decompose, cache


class TestDecompose():
    def setup_method(self, method):
        cache.flush()

    def teardown_method(self, method):
        cache.flush()

    def test_init_no_shifts(self):
        demand = [1, 2, 3, 2, 1]
        min_length = 1
        max_length = 2

        d = Decompose(demand, min_length, max_length)

        assert d.demand == demand
        assert d.min_length == min_length
        assert d.max_length == max_length
        assert d.window_offset == 0  # No windowing

    def test_lagging_zeros_windowing(self):
        demand = [1, 2, 3, 2, 1, 0, 0]
        expected_processed_demand = [1, 2, 3, 2, 1]
        min_length = 1
        max_length = 2

        d = Decompose(demand, min_length, max_length)

        assert d.demand == expected_processed_demand
        assert d.min_length == min_length
        assert d.max_length == max_length
        assert d.window_offset == 0  # No windowing

    def test_leading_zeros_windowing(self):
        demand = [0, 0, 0, 1, 2, 3, 2, 1]
        expected_processed_demand = [1, 2, 3, 2, 1]
        min_length = 1
        max_length = 2

        d = Decompose(demand, min_length, max_length)

        assert d.demand == expected_processed_demand
        assert d.min_length == min_length
        assert d.max_length == max_length
        assert d.window_offset == 3  # Windowing

    def test_combined_windowing(self):
        demand = [0, 0, 0, 0, 1, 0, 2, 3, 0, 2, 1, 0, 0]
        expected_processed_demand = [1, 0, 2, 3, 0, 2, 1]
        min_length = 1
        max_length = 2

        d = Decompose(demand, min_length, max_length)

        assert d.demand == expected_processed_demand
        assert d.window_offset == 4  # Windowing
        assert d.min_length == min_length
        assert d.max_length == max_length

    def test_subproblem_generation(self):
        demand = [0, 1, 2, 3, 4, 2]
        min_length = 1
        max_length = 2

        expected_window_offset = 1
        expected_windowed_demand = [1, 2, 3, 4, 2]
        expected_round_up = [1, 1, 2, 2, 1]
        expected_round_down = [0, 1, 1, 2, 1]

        d = Decompose(demand, min_length, max_length)

        actual_round_up = d._split_demand(round_up=True)
        actual_round_down = d._split_demand(round_up=False)
        actual_window_offset = d.window_offset

        assert actual_round_up == expected_round_up
        assert actual_round_down == expected_round_down
        assert actual_window_offset == expected_window_offset

        # Check that we exactly split demand in 2 (no overage or underage)
        recombined = [
            up + down for up, down in zip(actual_round_up, actual_round_down)
        ]
        assert recombined == expected_windowed_demand

    def test_edge_smoothing(self):
        demand = [3, 3, 2, 2, 4, 2, 3, 1, 3]
        min_length = 3
        max_length = 4
        expected_demand = [3, 3, 3, 2, 4, 3, 3, 3, 3]
        d = Decompose(demand, min_length, max_length)
        assert d.demand == expected_demand
