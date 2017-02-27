import pytest

from chomp import Splitter, cache

EFFICIENCY_LIMIT = .8
PERFECT_OPTIMALITY = 0.0


class TestSplitter():
    def setup_method(self, method):
        cache.flush()

    def teardown_method(self, method):
        cache.flush()

    def test_succeeds_with_zero_demand(self):
        # yapf: disable
        demand = [
            [0]*24,
            [0]*24,
            [0]*24,
            [0]*24,
            [0]*24,
            [0]*24,
            [0]*24,
        ]
        # yapf: enable

        min_length = 4
        max_length = 8

        s = Splitter(demand, min_length, max_length)
        s.calculate()
        s.validate()

        efficiency = s.efficiency()
        assert efficiency == PERFECT_OPTIMALITY

    @pytest.mark.timeout(1600)
    def test_on_demand_old(self):
        """Old on demand data - good test of wrap-around"""
        # yapf: disable
        demand = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 4, 4, 6, 6, 7, 7, 5, 2],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 4, 5, 3, 3, 4, 4, 7, 6, 5, 4, 2],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 5, 4, 5, 4, 5, 5, 7, 6, 6, 5, 3],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 3, 3, 5, 5, 2, 5, 6, 7, 6, 6, 5, 3],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 4, 4, 3, 5, 4, 6, 5, 6, 8, 5, 4, 4],
            [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 4, 5, 3, 4, 5, 6, 7, 8, 6, 6, 5, 2],
            [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 4, 5, 5, 5, 4, 6, 6, 11, 8, 6, 4, 2],
        ]
        # yapf: enable

        min_length = 4
        max_length = 8

        s = Splitter(demand, min_length, max_length)
        s.calculate()
        s.validate()

        efficiency = s.efficiency()
        assert efficiency < EFFICIENCY_LIMIT

    @pytest.mark.timeout(1600)
    def test_la(self):
        """24/7 LA client data"""
        # yapf: disable
        demand = [
            # They sometimes have leading zeros
            [0, 0, 3, 3, 3, 3, 4, 4, 4, 4, 4, 3, 3, 3, 3, 4, 4, 4, 4, 4, 3, 3, 3, 1],
            [1, 1, 1, 1, 3, 3, 4, 4, 4, 4, 4, 3, 3, 3, 3, 4, 4, 4, 4, 4, 3, 3, 3, 3],
            [4, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4],
            [3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 3, 3, 3, 3, 4, 4, 4, 4, 4, 3, 3, 3, 3],
            [3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4],
            [4, 3, 3, 3, 3, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
            [4, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4],
        ]
        # yapf: enable
        min_length = 6
        max_length = 8

        s = Splitter(demand, min_length, max_length)
        s.calculate()
        s.validate()
        assert s.efficiency() < 0.08

    @pytest.mark.timeout(1600)
    def test_call_center(self):
        """See if it chokes for call center client data"""
        # yapf: disable
        demand = [
            [0, 0, 0, 0, 0, 0, 0, 0, 15, 15, 15, 15, 15, 15, 15, 15, 15, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 15, 15, 15, 15, 15, 15, 15, 15, 15, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 15, 15, 15, 15, 15, 15, 15, 15, 15, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 15, 15, 15, 15, 15, 15, 15, 15, 15, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 15, 15, 15, 15, 15, 15, 15, 15, 15, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 15, 15, 15, 15, 15, 15, 15, 15, 15, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 15, 15, 15, 15, 15, 15, 15, 15, 15, 0, 0, 0, 0, 0, 0, 0],
        ]
        # yapf: enable
        min_length = 9
        max_length = 9

        s = Splitter(demand, min_length, max_length)
        s.calculate()
        s.validate()
        # For these, we really need perfect efficiency
        assert s.efficiency() < 0.001

    @pytest.mark.timeout(1600)
    def test_london_on_demand_two(self):
        """Test on demand trial data that supposedly had low efficiency"""
        # yapf: disable
        demand = [
            [0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 4, 8, 12, 10, 9, 8, 9, 15, 15, 20,
             17, 14, 7, 4],
            [0, 0, 0, 0, 0, 0, 0, 0, 3, 4, 6, 10, 14, 14, 9, 9, 9, 12, 20, 25,
             20, 12, 9, 5],
            [0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 7, 12, 15, 12, 10, 9, 12, 12, 16,
             21, 20, 12, 9, 4],
            [0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 7, 10, 13, 13, 9, 9, 11, 15, 17, 24,
             23, 14, 7, 5],
            [0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 7, 10, 13, 13, 11, 11, 11, 12, 25,
             29, 29, 20, 12, 9],
            [6, 0, 0, 0, 0, 0, 0, 0, 3, 6, 6, 12, 19, 18, 17, 16, 16, 18, 24,
             25, 25, 18, 11, 7],
            [4, 0, 0, 0, 0, 0, 0, 0, 3, 6, 7, 12, 19, 19, 17, 16, 16, 18, 23,
             29, 26, 14, 9, 5],
        ]
        # yapf: enable
        min_length = 4
        max_length = 14

        s = Splitter(demand, min_length, max_length)
        s.calculate()
        s.validate()
        # For these, we really need perfect efficiency
        assert s.efficiency() < 0.01

    def test_online_store_prod_failure(self):
        """This data caused a production error"""
        # yapf: disable
        demand = [
            [8, 8, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 8, 8, 8, 8, 8, 8],
            [8, 8, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 8, 8, 8, 8, 8, 8],
            [8, 8, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 8, 8, 8, 8, 8, 8],
            [8, 8, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 8, 8, 8, 8, 8, 8],
            [8, 8, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 8, 8, 8, 8, 8, 8],
        ]
        # yapf: enable
        min_length = 8
        max_length = 8

        s = Splitter(demand, min_length, max_length)
        s.calculate()
        s.validate()

# We commented out this test because it's making Travis-ci.org time out. 
# Yes, it's ironic that the slow test causes failure because it's slow, but in our internal
# tests the processors were fast enough in CI and prod for an acceptable run time of this
# problem :-)
"""
    def test_labs_slow(self):
        # yapf: disable
        demand = [
                [0, 0, 0, 0, 1, 1, 4, 4, 2, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 2, 2, 2, 0, 0],
                [0, 0, 0, 0, 2, 6, 10, 12, 14, 12, 17, 15, 16, 19, 14, 11, 9, 10, 9, 5, 5, 4, 2, 2],
                [1, 2, 1, 2, 2, 6, 9, 10, 11, 13, 12, 13, 14, 11, 12, 12, 9, 5, 4, 2, 2, 0, 0, 0],
                [2, 1, 1, 1, 2, 6, 8, 9, 11, 16, 16, 11, 16, 15, 11, 16, 11, 17, 7, 13, 7, 5, 5, 2],
                [1, 0, 1, 1, 2, 5, 9, 15, 17, 15, 13, 14, 13, 13, 13, 9, 10, 11, 6, 6, 6, 4, 1, 2],
                [1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 0, 0, 0, 0, 1, 4, 2, 1, 1, 1, 2, 2, 2],
                [0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
        ]
        # yapf: enable
        min_length = 4
        max_length = 8

        s = Splitter(demand, min_length, max_length)
        s.calculate()
        s.validate()
"""