from chomp import logger


class ShiftCollection(object):
    """A group of shifts"""

    def __init__(self, min_length, max_length, demand=None, shifts=None):
        if demand is None:
            demand = []

        if shifts is None:
            shifts = []
        self._demand = demand
        self.demand_length = len(self._demand)
        self._coverage = [0] * self.demand_length

        # Used for annealing
        self.min_length = min_length
        self.max_length = max_length

        # initiate as empty
        self._shifts = []

        # Add in shifts so coverage cache is populated
        for shift in shifts:
            self.add_shift(shift)

    @property
    def shifts(self):
        return self._shifts

    @shifts.setter
    def shifts(self):
        raise Exception("use addShift method to add a shift")

    def add_shift(self, shift):
        """Add a shift, which is a tuple of start and length"""
        start, length = shift
        end_index = start + length
        if start < 0 or end_index > self.demand_length:
            raise Exception(
                "Shift lies outside demand bounds (demand length %s, shift start %s, shift end %s,",
                self.demand_length,
                start,
                end_index,
            )

        for t in range(start, end_index):
            self._coverage[t] += 1

        self._shifts.append(shift)

    def get_demand_minus_coverage(self, t):
        """Return needs vs. shift coverage at time"""
        # If > 0 then underscheduled
        # if = 0 then optimal
        # if < 0 then overscheduled
        return self._demand[t] - self._coverage[t]

    @property
    def coverage_sum(self):
        return sum(self._coverage)

    @property
    def best_possible_coverage(self):
        """Look at current shift + demand needing to be covered"""
        best_possible = sum(self._demand)
        for t in range(self.demand_length):
            delta = self.get_demand_minus_coverage(t)
            if delta < 0:
                best_possible += abs(delta)

        return best_possible

    @property
    def demand_is_met(self):
        """Has a solution been found?"""
        for t in range(self.demand_length):
            if self.get_demand_minus_coverage(t) > 0:
                return False

        return True

    @property
    def shift_count(self):
        """Return how many shifts we have"""
        return len(self._shifts)

    def get_first_time_demand_not_met(self):
        """Find the first time the demand is not met"""
        for t in range(self.demand_length):
            if self._demand[t] > self._coverage[t]:
                return t

        raise Exception(
            "Infeasible answer- demand is met %s %s %s"
            % (self.demand_is_met, self._demand, self._coverage)
        )

    @property
    def is_optimal(self):
        for t in range(self.demand_length):
            delta = self.get_demand_minus_coverage(t)
            if delta != 0:
                return False

            if delta < 0:
                return False

        return True

    def anneal(self):
        """Look for overages and try to fix them"""
        if not self.demand_is_met:
            raise Exception("Cannot anneal an unfeasible demand")

        if self.is_optimal:
            # noop
            return

        # Run on loop until no more improvements
        improvement_made = True
        time_saved = 0
        while improvement_made:
            improvement_made = False

            # Find times that are overscheduled
            for t in range(self.demand_length):
                if self.get_demand_minus_coverage(t) < 0:
                    # Then it's unoptimal - look for shifts that start or end there, and try to roll back
                    for i in range(len(self._shifts)):
                        start, length = self._shifts[i]
                        end = start + length
                        if start == t and length > self.min_length:
                            self._shifts[i] = (start + 1, length - 1)
                            self._coverage[t] -= 1
                            time_saved += 1
                            improvement_made = True

                        if end == t and length > self.max_length:
                            self._shifts[i] = (start, length - 1)
                            self._coverage[t] -= 1
                            time_saved += 1
                            improvement_made = True

        if time_saved > 0:
            logger.info("Annealing removed %s units", time_saved)

        if self.is_optimal:
            logger.info("Annealing reached optimality")
