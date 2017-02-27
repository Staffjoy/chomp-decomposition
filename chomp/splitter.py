import copy

from chomp import logger
from chomp.decompose import Decompose
from chomp.exceptions import UnequalDayLengthException


class Splitter(object):
    """Take demand and turn it into subproblems for decompose.py

    This file is unitless and hypothetically support weeks of any length
    or days of any consistent length (e.g. 30 minute granularity)

    Demand is flattened then split into subproblems. The demand
    is considered circular such that, if a business is open from 8pm to 2am,
    then the final day of the week will wrap into the following week.

    24/7 demand is split day by day right now. In the future, splitting it into
    overlapping sections (e.g. a midnight->noon, 8am-4pm, and noon-midnight)
    may be best for handling large demand.
    """

    def __init__(self, week_demand, min_length, max_length):
        """Flatten demand and build helpers"""
        # week_demand is a list of lists

        # These are treated as unitless and should match the demand units
        logger.debug("Min %s max %s", min_length, max_length)
        self.min_length = int(min_length)
        self.max_length = int(max_length)

        self._shifts = []  # don't access directly!
        self._windows = []

        self.week_length = len(week_demand)

        # Validate that days are same length
        self.day_length = len(week_demand[0])
        for i in range(len(week_demand)):
            if self.day_length != len(week_demand[i]):
                raise UnequalDayLengthException()

        # 2) Flatten demand
        self.flat_demand = [
            item for day_demand in week_demand for item in day_demand
        ]

    def calculate(self):
        # Generate subproblems
        self._generate_windows()
        self._solve_windows()

    def get_shifts(self):
        # Remove window and return shifts day by day
        shifts = copy.copy(self._shifts)
        for shift in shifts:
            shift["day"] = self._flat_index_to_day(shift["start"])
            shift["start"] = self._flat_index_to_time(shift["start"])

        return shifts

    def _generate_windows(self):
        """Generate the demand subproblems to solve."""
        # Inclusive ->  Exclusive (python list syntax)

        # Check for 24/7 edge case
        if self._is_always_open():
            # Break it into day by day
            for i in range(self.week_length):
                start = i * self.day_length
                end = start + self.day_length
                self._add_window(start, end)

            return

        # Stop condition is based on start becuase of circular wraping
        for start in range(len(self.flat_demand)):
            if (self.flat_demand[start] is not 0) and (
                    start is 0 or self.flat_demand[start - 1] is 0):
                for end in range(start + 1,
                                 len(self.flat_demand) + self.max_length):

                    if self._get_flat_demand(end) is 0 and (
                            start == (end - 1) or
                            self._get_flat_demand(end - 1) is not 0):
                        # Add to window . . . mayb
                        # off by 1 becuase of exclusive
                        self._add_window(start, end)
                        break

    def _get_flat_demand(self, index):
        """Get flat demand at index - noting that it may be circular!"""
        return self.flat_demand[(index + 1) % len(self.flat_demand) - 1]

    def _add_window(self, start, end, raise_on_min_length=False):
        """Add a window - checking whether it violates rules"""

        length = end - start

        if length < self.min_length:
            # Only raise when recursing
            if raise_on_min_length:
                raise Exception("Min length constraint violated")

            if start == 0:
                # Expected
                logger.debug(
                    "Skipping circular wraparound at beginning of loop")
            else:
                # Bad user. Bad.
                logger.info("Skipping window less than min length")
            return
        if length > self.day_length:
            # Split in two - a floor and a ceiling
            # Hypothetically recurses
            logger.info("Splitting large window into subproblems")
            center = start + (end - start) / 2
            # It's possible the windows will violate min length constrainnts,
            # so we wrap in a try block
            try:
                self._add_window(start, center, raise_on_min_length=True)
                self._add_window(center, end, raise_on_min_length=True)
            except:
                self._windows.append((start, end))
            return

        self._windows.append((start, end))

    def _solve_windows(self):
        """Run windows through decompose to create shifts"""

        window_count = 0
        for (start, stop) in self._windows:
            window_count += 1
            logger.info("Starting window %s of %s (start %s stop %s) ",
                        window_count, len(self._windows), start, stop)

            # Need to wrap
            demand = self._get_window_demand(start, stop)
            d = Decompose(
                demand, self.min_length, self.max_length, window_offset=start)
            d.calculate()
            e = d.efficiency()
            logger.info("Window efficiency: Overage is %s percent",
                        (e * 100.0))
            self._shifts.extend(d.get_shifts())

    #
    # helper methods
    #

    def _is_always_open(self):
        """Detect whether the business is 24/7"""
        # Hacky fuzzing due to a client that MOSTLY 24/7
        i = -1
        for d in self.flat_demand:
            i += 1
            # Equal because max length is not possible
            if d is 0 and i >= self.max_length:
                return False
        return True

    def _flat_index_to_day(self, index):
        """Take the flat demand index and return the day integer"""
        if index is 0:
            return 0

        # Python 2.7 integer division returns integer (but not true in py3)
        return index / self.day_length

    def _flat_index_to_time(self, index):
        """Take the flat demand index and return the start time integer"""
        return index % self.day_length

    def _is_circular_necessary(self):
        """Return whether the demand must be calculated circularly"""
        # Think of a business open until 2am every day with min shift length 3
        # Loading demand at the beginning of the week will show 2 hours
        # orphaned. It should be pushed onto the last day's subproblem.

        # Find first zero index
        first_zero = -1
        for t in range(len(self.flat_demand)):
            if self.flat_demand[t] is 0:
                first_zero = t
                break

        return first_zero < self.min_length

    #
    # Validation functions - mainly for testing
    #

    def validate(self):
        """Check whether shifts meet demand. Used in testing."""
        expected_demand = copy.copy(self.flat_demand)
        sum_demand = [0] * len(self.flat_demand)

        logger.debug("Starting validation of %s shifts", len(self._shifts))

        for shift in self._shifts:
            # Inclusive range
            for t in range(shift["start"], shift["start"] + shift["length"]):
                # (circular)
                sum_demand[(t + 1) % len(self.flat_demand) - 1] += 1

        logger.debug("Expected demand: %s", expected_demand)
        logger.debug("Scheduled supply: %s", sum_demand)
        for t in range(len(expected_demand)):
            if sum_demand[t] < expected_demand[t]:
                logger.error(
                    "Demand not met at time %s (demand %s, supply %s)", t,
                    expected_demand[t], sum_demand[t])
                raise Exception("Demand not met at time %s" % t)
        return True

    def efficiency(self):
        """Return the overage as a float. 0 is perfect."""
        PERFECT_OPTIMALITY = 0.0

        # Check for divide by 0 error.
        if sum(self.flat_demand) == 0.0:
            return PERFECT_OPTIMALITY

        efficiency = (1.0 * sum(shift["length"] for shift in self._shifts) /
                      sum(self.flat_demand)) - 1

        logger.info("Efficiency: Overage is %s percent", efficiency * 100.0)
        return efficiency

    def _get_window_demand(self, start, stop):
        """Get circular start and stop (stop may wrap)"""
        if stop < len(self.flat_demand):
            return self.flat_demand[start:stop]
        return self.flat_demand[start:] + self.flat_demand[:stop % len(
            self.flat_demand)]
