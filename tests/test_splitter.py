import pytest

from chomp import Splitter
from chomp.exceptions import UnequalDayLengthException


class TestDecompose():
    def setup_method(self, method):
        self.week_demand = [[1, 2, 3, 0], [1, 3, 1, 0], [1, 1, 1, 0]]
        self.expected_flat_week_demand = [1, 2, 3, 0, 1, 3, 1, 0, 1, 1, 1,
                                          0]  # len 12
        self.min_length = 3
        self.max_length = 4

    def teardown_method(self, method):
        pass

    def test_splitter_init(self):
        s = Splitter(self.week_demand, self.min_length, self.max_length)

        assert len(s.flat_demand) == len(self.week_demand) * len(
            self.week_demand[0])
        assert s.flat_demand == self.expected_flat_week_demand
        assert s.min_length == self.min_length
        assert s.max_length == self.max_length
        assert s.day_length == len(self.week_demand[0])

    def test_circular_get_window_demand(self):
        s = Splitter(self.week_demand, self.min_length, self.max_length)
        # For circular - I'll do one manual for sanity and a couple programmatic
        assert s._get_window_demand(1,
                                    4) == self.expected_flat_week_demand[1:4]
        assert s._get_window_demand(11, 13) == [0, 1]
        assert s._get_window_demand(11, 11) == []

    def test_circular_get_demand(self):
        s = Splitter(self.week_demand, self.min_length, self.max_length)
        # For circular - I'll do one manual for sanity and a couple programmatic
        assert s._get_flat_demand(13) == self.expected_flat_week_demand[1]
        for t in range(len(self.expected_flat_week_demand)):
            assert s._get_flat_demand(t) == self.expected_flat_week_demand[t]
            assert s._get_flat_demand(t + len(self.expected_flat_week_demand)
                                      ) == self.expected_flat_week_demand[t]

    def test_splitter_init_different_day_lengths(self):
        self.week_demand[1].pop()

        with pytest.raises(UnequalDayLengthException):

            Splitter(self.week_demand, self.min_length, self.max_length)

    def test_windowing_standard(self):
        s = Splitter(self.week_demand, self.min_length, self.max_length)
        s._generate_windows()
        expected_windows = [(0, 3), (4, 7), (8, 11)]

        assert s._windows == expected_windows

    def test_windowing_standard_again(self):
        self.week_demand = [[0, 2, 3, 4, 0, 3, 1, 8], [1, 2, 3, 0, 2, 3, 1, 8]]
        s = Splitter(self.week_demand, self.min_length, self.max_length)
        s._generate_windows()
        expected_windows = [(1, 4), (5, 11), (12, 16)]
        assert s._windows == expected_windows

    def test_windowing_always_open(self):
        self.week_demand = [[1, 2, 3, 4], [1, 3, 1, 8], [1, 1, 1, 2]]
        s = Splitter(self.week_demand, self.min_length, self.max_length)
        s._generate_windows()
        expected_windows = [(0, 4), (4, 8), (8, 12)]
        assert s._windows == expected_windows

    def test_windowing_short_subproblem(self):
        self.week_demand = [[1, 2, 0, 0], [1, 3, 1, 0], [0, 1, 1, 0]]
        s = Splitter(self.week_demand, self.min_length, self.max_length)
        s._generate_windows()
        expected_windows = [
            (4, 7),
        ]
        assert s._windows == expected_windows

    def test_windowing_circular(self):
        self.week_demand = [[1, 1, 0, 4], [1, 2, 1, 0], [0, 0, 1, 1]]
        s = Splitter(self.week_demand, self.min_length, self.max_length)
        s._generate_windows()
        expected_windows = [(3, 7), (10, 14)]
        assert s._windows == expected_windows

    def test_windowing_split_invalid_subproblem(self):
        # Window that is so large that it gets recursively split . . .
        # BUT one of the split problems is less the min length, so
        # it shoudl abandon the search
        self.week_demand = [[1, 1, 0, 4], [1, 2, 1, 0], [0, 1, 1, 1]]
        s = Splitter(self.week_demand, self.min_length, self.max_length)
        s._generate_windows()
        expected_windows = [(3, 7), (9, 14)]
        assert s._windows == expected_windows

    def test_windowing_split_valid_subproblem(self):
        # Window so large that it gets recursively split
        self.min_length = 2  # Update versus prior test
        self.week_demand = [[1, 0, 0, 4], [1, 2, 1, 0], [1, 1, 1, 1]]
        s = Splitter(self.week_demand, self.min_length, self.max_length)
        s._generate_windows()
        expected_windows = [(3, 7), (8, 10), (10, 13)]
        assert s._windows == expected_windows

    # helper methods
    def test_is_always_open_case_true(self):
        self.week_demand = [[1, 2, 3, 4], [1, 3, 1, 8], [1, 1, 1, 2]]
        s = Splitter(self.week_demand, self.min_length, self.max_length)
        assert s._is_always_open() is True

    def test_is_always_open_case_carryover_true(self):
        self.week_demand = [[0, 0, 0, 4], [1, 3, 1, 8], [1, 1, 1, 2]]
        s = Splitter(self.week_demand, self.min_length, self.max_length)
        assert s._is_always_open() is True

    def test_is_always_open_case_false(self):
        s = Splitter(self.week_demand, self.min_length, self.max_length)
        # Just going through this whole week, cause fuck it
        assert s._is_always_open() is False

    def test_flat_index_to_day(self):
        """Take the flat demand index and return the day integer"""
        s = Splitter(self.week_demand, self.min_length, self.max_length)
        flat_to_day = [
            (0, 0),
            (1, 0),
            (2, 0),
            (3, 0),
            (4, 1),
            (5, 1),
            (6, 1),
            (7, 1),
            (8, 2),
            (9, 2),
            (10, 2),
            (11, 2),
        ]

        for (flat, day) in flat_to_day:
            assert s._flat_index_to_day(flat) == day

    def test_flat_index_to_time(self):
        s = Splitter(self.week_demand, self.min_length, self.max_length)
        flat_to_time = [
            (0, 0),
            (1, 1),
            (2, 2),
            (3, 3),
            (4, 0),
            (5, 1),
            (6, 2),
            (7, 3),
            (8, 0),
            (9, 1),
            (10, 2),
            (11, 3),
        ]

        for (flat, time) in flat_to_time:
            assert s._flat_index_to_time(flat) == time

    def test_is_circular_necessary_case_false(self):
        s = Splitter(self.week_demand, self.min_length, self.max_length)
        assert s._is_circular_necessary() is False

    def test_is_circular_necessary_case_true(self):
        self.week_demand = [[1, 1, 0, 4], [1, 2, 1, 0], [1, 1, 1, 1]]
        s = Splitter(self.week_demand, self.min_length, self.max_length)
        assert s._is_circular_necessary() is True
