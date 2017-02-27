from chomp.shift_collection import ShiftCollection

import pytest


class TestShiftCollection():
    def setup_method(self, method):
        self.min_length = 5
        self.max_length = 6
        self.demand = [1, 2, 3, 4, 5, 4, 3, 2, 1]
        self.demand_sum = sum(self.demand)
        self.collection = ShiftCollection(
            self.min_length, self.max_length, demand=self.demand)

    def teardown_method(self, method):
        pass

    def test_init_noshifts(self):
        assert self.collection.shifts == []

        for t in range(len(self.demand)):
            assert self.collection.get_demand_minus_coverage(t) == self.demand[
                t]

        assert self.collection.coverage_sum == 0
        assert len(self.demand) == self.collection.demand_length
        assert self.collection.best_possible_coverage == self.demand_sum
        assert self.collection.demand_is_met == False
        assert self.collection.shift_count == 0
        assert self.collection.get_first_time_demand_not_met() == 0
        assert self.collection.is_optimal == False

    def test_add_a_shift(self):
        # We intentionally add it from second time to end time
        start = 1
        length = 8
        shift = (start, length)
        expected_demand_minus_coverage = [1, 1, 2, 3, 4, 3, 2, 1, 0]

        self.collection.add_shift(shift)

        assert self.collection.shifts == [shift]

        for t in range(len(self.demand)):
            assert self.collection.get_demand_minus_coverage(
                t) == expected_demand_minus_coverage[t]

        assert self.collection.coverage_sum == length

        # No overage
        assert self.collection.best_possible_coverage == self.demand_sum
        assert self.collection.demand_is_met == False
        assert self.collection.shift_count == 1
        assert self.collection.get_first_time_demand_not_met() == 0
        assert self.collection.is_optimal == False

    def test_add_three_shifts(self):

        # Remember that they are (start, length)
        shifts = [(0, 3), (0, 3), (3, 4)]
        expected_demand_minus_coverage = [-1, 0, 1, 3, 4, 3, 2, 2, 1]

        for shift in shifts:
            self.collection.add_shift(shift)

        assert self.collection.shifts == shifts

        for t in range(len(self.demand)):
            assert self.collection.get_demand_minus_coverage(
                t) == expected_demand_minus_coverage[t]

        assert self.collection.coverage_sum == 10

        # We have triggered 1 overage, so it shoudl be demand plus length
        assert self.collection.best_possible_coverage == self.demand_sum + 1
        assert self.collection.demand_is_met == False
        assert self.collection.shift_count == 3
        assert self.collection.get_first_time_demand_not_met() == 2
        assert self.collection.is_optimal == False

    def test_add_overage_shifts(self):

        # Remember that they are (start, length)
        shifts = [(0, 9)] * 5
        expected_demand_minus_coverage = [-4, -3, -2, -1, 0, -1, -2, -3, -4]

        for shift in shifts:
            self.collection.add_shift(shift)

        assert self.collection.shifts == shifts

        for t in range(len(self.demand)):
            assert self.collection.get_demand_minus_coverage(
                t) == expected_demand_minus_coverage[t]

        assert self.collection.coverage_sum == 9 * 5

        # We have triggered 20 overage, so it should be demand plus length
        assert self.collection.best_possible_coverage == self.demand_sum + 20
        assert self.collection.demand_is_met == True
        assert self.collection.shift_count == 5
        with pytest.raises(Exception):
            assert self.collection.get_first_time_demand_not_met() == 2
        assert self.collection.is_optimal == False

    def test_add_optimal_shifts(self):

        # Remember that they are (start, length)
        shifts = [(0, 5), (1, 5), (2, 5), (3, 5), (4, 5)]

        for shift in shifts:
            self.collection.add_shift(shift)

        assert self.collection.shifts == shifts

        for t in range(len(self.demand)):
            # Optimal
            assert self.collection.get_demand_minus_coverage(t) == 0

        assert self.collection.coverage_sum == self.demand_sum

        assert self.collection.best_possible_coverage == self.demand_sum

        assert self.collection.demand_is_met == True
        assert self.collection.shift_count == 5
        with pytest.raises(Exception):
            assert self.collection.get_first_time_demand_not_met() == 2
        assert self.collection.is_optimal == True

        # Now we anneal and asser that nothing's done
        self.collection.anneal()
        assert self.collection.shifts == shifts
        assert self.collection.demand_is_met == True
        assert self.collection.is_optimal == True

    def test_adding_shift_below_range_triggers_exception(self):
        too_short_shift = (-1, 3)
        with pytest.raises(Exception):
            self.collection.add_shift(too_short_shift)

    def test_adding_shift_above_bounds_triggers_exception(self):
        too_long_shift = (5, 5)
        with pytest.raises(Exception):
            self.collection.add_shift(too_long_shift)

    def test_must_be_feasible_for_annealing(self):
        with pytest.raises(Exception):
            self.collection.anneal()

    def test_annealing_succeeds(self):
        # Similar to optimal shifts
        shifts = [(0, 5), (1, 5), (1, 6), (3, 5), (4, 5)]

        expected_annealed_shifts = [(0, 5), (1, 5), (2, 5), (3, 5), (4, 5)]

        for shift in shifts:
            self.collection.add_shift(shift)

        self.collection.anneal()
        assert self.collection.shifts == expected_annealed_shifts

    def test_annealing_min_shift_length_noop(self):
        # Basically re-run last test but with longer min shift length

        demand = [1, 2, 3, 4, 4, 4, 3, 2, 1]
        self.collection = ShiftCollection(5, 5, demand=demand)
        shifts = [(0, 5), (1, 5), (2, 5), (3, 5), (4, 5)]

        for shift in shifts:
            self.collection.add_shift(shift)

        self.collection.anneal()
        assert self.collection._shifts == shifts
