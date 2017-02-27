from chomp import Decompose, cache
import pytest

EFFICIENCY_LIMIT = .8


class TestDecompose():
    def setup_method(self, method):
        cache.flush()

    def teardown_method(self, method):
        cache.flush()

    def test_ondemand_data(self):
        """Data from customer bike group, Jan 2015"""
        demand = [
            0, 0, 0, 0, 0, 0, 0, 5, 5, 7, 8, 6, 6, 7, 7, 7, 9, 9, 6, 5, 4, 4,
            0, 0
        ]
        min_length = 4
        max_length = 8
        d = Decompose(demand, min_length, max_length)
        d.calculate()
        d.validate()

        efficiency = d.efficiency()
        assert efficiency < EFFICIENCY_LIMIT

    # 10 min timeout (because it should hit subproblems)
    @pytest.mark.timeout(600)
    def test_big_on_demand(self):
        """Data from on demand client Jan 2015 (before splitting into roles)"""
        demand = [
            0, 0, 0, 0, 0, 0, 35, 35, 35, 34, 56, 59, 63, 70, 87, 107, 90, 61,
            44, 32, 28
        ]
        min_length = 4
        max_length = 8
        d = Decompose(demand, min_length, max_length)
        d.calculate()
        d.validate()

        efficiency = d.efficiency()
        assert efficiency < EFFICIENCY_LIMIT

    @pytest.mark.timeout(600)
    def test_doesnt_freak_out_with_interior_zero(self):
        """Add an interior zero and make sure the algorithm does not freak out."""
        # This is important becuase when bifurcating, an interior zero is possible
        # Here, it's infeasible unless the interior point is > 0
        demand = [1, 0, 1, 1, 2, 2, 2, 2, 3, 2, 2, 1]
        min_length = 2
        max_length = 4

        d = Decompose(demand, min_length, max_length)
        d.calculate()
        d.validate()

        efficiency = d.efficiency()
        assert efficiency < EFFICIENCY_LIMIT
