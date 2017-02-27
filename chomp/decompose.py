import math
import copy
from copy import deepcopy
from datetime import datetime, timedelta

from chomp import logger, cache, config
from chomp.helpers import reverse_inclusive_range
from chomp.shift_collection import ShiftCollection


class Decompose:
    """Class for decomposing demand into shifts"""

    def __init__(self, demand, min_length, max_length, window_offset=0):
        self.demand = demand  # Set this raw value for testing purposes
        self.min_length = min_length
        self.max_length = max_length
        self.window_offset = window_offset
        self._process_demand()  # This is the demand used for calculations

        # Preface with underscore bc this should never be accessed directly
        # - instead use  get_shifts() to apply offset
        self._shifts = []

    def _process_demand(self):
        """Apply windowing to demand"""

        demand = copy.copy(self.demand)

        # 1) Remove any lagging zeros. This affects nothing.
        while demand[-1] is 0:
            demand.pop()  # remove last element

        # 2) Remove any leading zeros andtrack with offset
        offset = 0
        while demand[0] is 0:
            demand.pop(0)  # remove first element
            offset += 1

        # TODO - edge smoothing algorithms

        # Smooth beginning edge
        # (TODO - search past to max_length and manually strip out shifts)
        peak = 0
        for t in range(self.min_length):
            if demand[t] > peak:
                peak = demand[t]
            elif demand[t] < peak:
                demand[t] = peak

        peak = 0
        for t in reversed(
                range((len(demand) - self.min_length - 1), len(demand))):
            if demand[t] > peak:
                peak = demand[t]
            elif demand[t] < peak:
                demand[t] = peak

        self.demand = demand
        self.window_offset += offset

        logger.debug("Windowing removed %s leading zeros", offset)
        logger.debug("Processed demand: %s", self.demand)

    def _split_demand(self, round_up=True):
        """Return unprocessed demand in half for subproblems"""
        halfsies = []
        for val in self.demand:
            half = val / 2.0
            if round_up:
                # Round up
                half = math.ceil(half)
            else:
                # Round down
                half = math.floor(half)

            # Round to avoid weird floating point issues (e.g. 7.999999)
            halfsies.append(int(round(half)))

        return halfsies

    def get_shifts(self):
        """Return de-windowed shifts"""
        shifts = copy.copy(self._shifts)
        for shift in shifts:
            shift["start"] += self.window_offset

        return shifts

    def validate(self):
        """Check whether shifts meet demand. Used in testing."""
        expected_demand = [0] * len(self.demand)
        sum_demand = copy.copy(expected_demand)

        logger.debug("Starting validation of %s shifts", len(self._shifts))

        for shift in self._shifts:
            for t in range(shift["start"], shift["start"] + shift["length"]):
                # Remove window
                sum_demand[t] += 1

        logger.debug("Expected demand: %s", expected_demand)
        logger.debug("Scheduled supply: %s", sum_demand)
        for t in range(len(expected_demand)):
            if sum_demand[t] < expected_demand[t]:
                logger.error(
                    "Demand not met at time %s (demand %s, supply %s)",
                    t + self.window_offset, expected_demand[t], sum_demand[t])
                raise Exception("Demand not met at time %s" % t)
        return True

    def efficiency(self, shifts=None):
        """Return the overage as a float. 0 is perfect."""
        if shifts is None:
            shifts = self._shifts

        efficiency = (1.0 * sum(shift["length"]
                                for shift in shifts) / sum(self.demand)) - 1

        return efficiency

    def _set_cache(self):
        cache.set(
            demand=self.demand,
            min_length=self.min_length,
            max_length=self.max_length,
            shifts=self._shifts)

    def calculate(self):
        if len(self._shifts) > 0:
            raise Exception("Shifts already calculated")

        # Try checking cache. Putting the check here means it even works for
        # subproblems!
        cached_shifts = cache.get(
            demand=self.demand,
            min_length=self.min_length,
            max_length=self.max_length)
        if cached_shifts:
            logger.info("Hit cache")
            self._shifts = cached_shifts
            return

        # Subproblem splitting
        demand_sum = sum(self.demand)
        if demand_sum > config.BIFURCATION_THRESHHOLD:
            # Subproblems. Split into round up and round down.
            logger.info("Initiating split (demand sum %s, threshhold %s)",
                        demand_sum, config.BIFURCATION_THRESHHOLD)
            # Show parent demand sum becuase it can recursively split
            demand_up = self._split_demand(round_up=True)
            demand_low = self._split_demand(round_up=False)

            d_up = Decompose(demand_up, self.min_length, self.max_length)
            d_low = Decompose(demand_low, self.min_length, self.max_length)

            logger.info(
                "Beginning upper round subproblem (parent demand sum: %s)",
                demand_sum)
            d_up.calculate()

            logger.info(
                "Beginning lower round subproblem (parent demand sum: %s)",
                demand_sum)
            d_low.calculate()

            self._shifts.extend(d_up.get_shifts())
            self._shifts.extend(d_low.get_shifts())
            self._set_cache()  # Set cache for the parent problem too!
            return

        self._calculate()
        self._set_cache()

    def _calculate(self):
        """Search that tree"""
        # Not only do we want optimality, but we want it with
        # longest shifts possible. That's why we do DFS on long shifts.

        starting_solution = self.use_heuristics_to_generate_some_solution()

        # Helper variables for branch and bound
        best_known_coverage = starting_solution.coverage_sum
        best_known_solution = starting_solution
        best_possible_solution = sum(self.demand)

        logger.debug("Starting with known coverage %s vs best possible %s",
                     best_known_coverage, best_possible_solution)

        # Branches to search
        # (We want shortest shifts retrieved first, so 
        # we add shortest and pop() to git last in)
        # (a LIFO queue using pop is more efficient in python
        # than a FIFO queue using pop(0))

        stack = []

        logger.info("Demand: %s", self.demand)
        empty_collection = ShiftCollection(
            self.min_length, self.max_length, demand=self.demand)
        stack.append(empty_collection)

        start_time = datetime.utcnow()

        while len(stack) != 0:
            if start_time + timedelta(
                    seconds=config.CALCULATION_TIMEOUT) < datetime.utcnow():
                logger.info("Exited due to timeout (%s seconds)",
                            (datetime.utcnow() - start_time).total_seconds())
                break

            # Get a branch
            working_collection = stack.pop()

            if working_collection.is_optimal:
                # We have a complete solution
                logger.info("Found an optimal collection. Exiting.")
                self.set_shift_collection_as_optimal(working_collection)
                return

            if working_collection.demand_is_met:
                if working_collection.coverage_sum < best_known_coverage:
                    logger.info(
                        "Better solution found (previous coverage %s / new coverage %s / best_possible %s)",
                        best_known_coverage, working_collection.coverage_sum,
                        best_possible_solution)

                    # Set new best possible solution
                    best_known_solution = working_collection
                    best_known_coverage = working_collection.coverage_sum
                else:
                    logger.debug("Found less optimal solution - continuing")
                    # discard
                del working_collection

            else:

                # New branch to explore - else discard
                if working_collection.best_possible_coverage < best_known_coverage:
                    # Gotta add more shifts!
                    t = working_collection.get_first_time_demand_not_met()

                    # Get shift start time
                    start = t
                    for length in reverse_inclusive_range(self.min_length,
                                                          self.max_length):
                        # Make sure we aren't off edge
                        end_index = start + length

                        # Our edge smoothing means this will always work
                        if end_index <= len(self.demand):
                            shift = (start, length)
                            new_collection = deepcopy(working_collection)
                            new_collection.add_shift(shift)

                            if new_collection.demand_is_met:
                                new_collection.anneal()

                            if new_collection.best_possible_coverage < best_known_coverage:

                                # Only save it if it's an improvement
                                stack.append(new_collection)

        self.set_shift_collection_as_optimal(best_known_solution)

    def use_heuristics_to_generate_some_solution(self):
        """Use heuristics to generate some feasible solution."""
        # (Used for branch and bound)

        # Heuristic: Fill in only shifts of smallest shift len

        collection = ShiftCollection(
            self.min_length, self.max_length, demand=self.demand)

        # Add shifts for the end

        length = self.min_length
        start = len(self.demand) - length
        end_shift = (start, length)
        for _ in range(self.demand[-1]):
            collection.add_shift(end_shift)

        # And now, go through time and add shifts
        for t in range(len(self.demand)):
            delta = collection.get_demand_minus_coverage(t)

            start = t
            length = self.min_length

            # On short problems we can exceed end
            if start + length > len(self.demand):
                start = len(self.demand) - length

            shift = (start, length)

            for _ in range(delta):
                collection.add_shift(shift)

        if not collection.demand_is_met:
            raise Exception("Heuristic for finding demand failed")

        return collection

    def set_shift_collection_as_optimal(self, collection):
        """Update decomposition model with our results"""
        # We need to unpack the collection shift models to the
        # external shifts model
        for shift in collection.shifts:
            start, length = shift
            self._shifts.append({
                "start": start,
                "length": length,
            })
        self._set_cache()
