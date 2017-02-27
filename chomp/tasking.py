from time import sleep
from copy import deepcopy
from datetime import timedelta
import traceback
import os

import pytz
import iso8601
from staffjoy import Client, NotFoundException

from chomp.helpers import week_day_range, normalize_to_midnight
from chomp import config, logger, Splitter


class Tasking():
    """Get tasks and process them"""

    REQUEUE_STATE = "chomp-queue"

    def __init__(self):
        self.client = Client(key=config.STAFFJOY_API_KEY, env=config.ENV)
        self.default_tz = pytz.timezone(config.DEFAULT_TZ)

        # To be defined later
        self.org = None
        self.loc = None
        self.role = None
        self.sched = None
        self.demand = None

    def server(self):
        previous_request_failed = False  # Have some built-in retries

        while True:
            # Get task
            try:
                task = self.client.claim_chomp_task()
                logger.info("Task received: %s", task.data)
                previous_request_failed = False
            except NotFoundException:
                logger.debug("No task found. Sleeping.")
                previous_request_failed = False
                sleep(config.TASKING_FETCH_INTERVAL_SECONDS)
                continue
            except Exception as e:
                if not previous_request_failed:
                    # retry, but info log it
                    logger.info("Unable to fetch chomp task - retrying")
                    previous_request_failed = True
                else:
                    logger.error(
                        "Unable to fetch chomp task after previous failure: %s",
                        e)

                # Still sleep so we avoid thundering herd
                sleep(config.TASKING_FETCH_INTERVAL_SECONDS)
                continue

            try:
                self._process_task(task)
                task.delete()
                logger.info("Task completed %s", task.data)
            except Exception as e:
                logger.error("Failed schedule %s:  %s %s",
                             task.data.get("schedule_id"), e,
                             traceback.format_exc())

                logger.info("Requeuing schedule %s",
                            task.data.get("schedule_id"))
                # self.sched set in process_task
                self.sched.patch(state=self.REQUEUE_STATE)

                # Sometimes rebooting Chomp helps with errors. For example, if
                # a Gurobi connection is drained then it helps to reboot.
                if config.KILL_ON_ERROR:
                    sleep(config.KILL_DELAY)
                    logger.info("Rebooting to kill container")
                    os.system("shutdown -r now")

    def _process_task(self, task):
        # 1. Fetch schedule
        self.org = self.client.get_organization(
            task.data.get("organization_id"))
        self.loc = self.org.get_location(task.data.get("location_id"))
        self.role = self.loc.get_role(task.data.get("role_id"))
        self.sched = self.role.get_schedule(task.data.get("schedule_id"))

        self._compute_demand()
        self._subtract_existing_shifts_from_demand()

        # Run the  calculation
        s = Splitter(self.demand,
                     self.sched.data.get("min_shift_length_hour"),
                     self.sched.data.get("max_shift_length_hour"))
        s.calculate()
        s.efficiency()

        # Naive becuase not yet datetimes
        naive_shifts = s.get_shifts()
        logger.info("Starting upload of %s shifts", len(naive_shifts))

        local_start_time = self._get_local_start_time()

        for shift in naive_shifts:
            # We have to think of daylight savings time here, so we need to
            # guarantee that we don't have any errors. We do this by overshooting
            # the timedelta by an extra two hours, then rounding back to midnight.

            logger.debug("Processing shift %s", shift)

            start_day = normalize_to_midnight(
                deepcopy(local_start_time) + timedelta(days=shift["day"]))

            # Beware of time changes - duplicate times are possible
            try:
                start = start_day.replace(hour=shift["start"])
            except pytz.AmbiguousTimeError:
                # Randomly pick one. Minor tech debt.
                start = start_day.replace(hour=shift["start"], is_dst=False)

            stop = start + timedelta(hours=shift["length"])

            # Convert to the strings we are passing up to the cLoUd
            utc_start_str = start.astimezone(self.default_tz).isoformat()
            utc_stop_str = stop.astimezone(self.default_tz).isoformat()

            logger.info("Creating shift with start %s stop %s", start, stop)
            self.role.create_shift(start=utc_start_str, stop=utc_stop_str)

    def _subtract_existing_shifts_from_demand(self):
        logger.info("Starting demand: %s", self.demand)
        demand_copy = deepcopy(self.demand)
        search_start = (self._get_local_start_time() - timedelta(
            hours=config.MAX_SHIFT_LENGTH_HOURS)).astimezone(self.default_tz)
        # 1 week
        search_end = (self._get_local_start_time() + timedelta(
            days=7, hours=config.MAX_SHIFT_LENGTH_HOURS)
                      ).astimezone(self.default_tz)

        shifts = self.role.get_shifts(start=search_start, end=search_end)

        logger.info("Checking %s shifts for existing demand", len(shifts))

        # Search hour by hour throughout the weeks
        for day in range(len(self.demand)):
            start_day = normalize_to_midnight(self._get_local_start_time() +
                                              timedelta(days=day))
            for start in range(len(self.demand[0])):

                # Beware of time changes - duplicate times are possible
                try:
                    start_hour = deepcopy(start_day).replace(hour=start)
                except pytz.AmbiguousTimeError:
                    # Randomly pick one - cause phucket. Welcome to chomp.
                    start_hour = deepcopy(start_day).replace(
                        hour=start, is_dst=False)

                try:
                    stop_hour = start_hour + timedelta(hours=1)
                except pytz.AmbiguousTimeError:
                    stop_hour = start_hour + timedelta(hours=1, is_dst=False)

                # Find shift
                current_staffing_level = 0
                for shift in shifts:
                    shift_start = iso8601.parse_date(
                        shift.data.get("start")).replace(
                            tzinfo=self.default_tz)
                    shift_stop = iso8601.parse_date(
                        shift.data.get("stop")).replace(tzinfo=self.default_tz)

                    if ((shift_start <= start_hour and shift_stop > stop_hour)
                            or
                        (shift_start >= start_hour and shift_start < stop_hour)
                            or
                        (shift_stop > start_hour and shift_stop <= stop_hour)):

                        # increment staffing level during that bucket
                        current_staffing_level += 1

                logger.debug("Current staffing level at day %s time %s is %s",
                             day, start, current_staffing_level)

                demand_copy[day][start] -= current_staffing_level
                # demand cannot be less than zero
                if demand_copy[day][start] < 0:
                    demand_copy[day][start] = 0

        logger.info("Demand minus existing shifts: %s", demand_copy)
        self.demand = demand_copy

    def _get_local_start_time(self):
        # Create the datetimes
        local_tz = pytz.timezone(self.loc.data.get("timezone"))
        utc_start_time = iso8601.parse_date(
            self.sched.data.get("start")).replace(tzinfo=self.default_tz)
        local_start_time = utc_start_time.astimezone(local_tz)
        return local_start_time

    def _compute_demand(self):
        weekday_demand = self.sched.data.get("demand")
        day_week_starts = self.org.data.get("day_week_starts")
        # flatten days from dict to list
        demand = []
        for day in week_day_range(day_week_starts):
            demand.append(weekday_demand[day])

        self.demand = demand
