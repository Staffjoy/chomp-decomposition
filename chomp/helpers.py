DAYS_OF_WEEK = [
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
    "sunday"
]


def week_day_range(start_day="monday"):
    """ Return list of days of week in order from start day """
    start_index = DAYS_OF_WEEK.index(start_day)
    return DAYS_OF_WEEK[start_index:] + DAYS_OF_WEEK[:start_index]


def normalize_to_midnight(dt_obj):
    """Take a datetime and round it to midnight"""
    return dt_obj.replace(hour=0, minute=0, second=0, microsecond=0)


def inclusive_range(start, end):
    """Get start to end, inclusive to inclusive"""
    # Note that python range is inclusive to exclusive
    return range(start, end + 1)


def reverse_inclusive_range(low, high):
    """Get decreasing range from high to low, inclusive to inclusive"""
    # Note that python range is inclusive to exclusive
    return range(high, low - 1, -1)
