import os
import logging

basedir = os.path.abspath(os.path.dirname(__file__))


class DefaultConfig:
    ENV = "prod"
    LOG_LEVEL = logging.INFO
    SYSLOG = True  # Send logs to syslog server
    # Logging - we use papertrail.com
    SYSLOG_SERVER = os.getenv("SYSLOG_SERVER")
    CALCULATION_TIMEOUT = 10 * 60  # 10 minutes, in seconds
    BIFURCATION_THRESHHOLD = 100  # Sum of demand needed before splitting

    # Scheduling constants
    DAYS_OF_WEEK = [
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
        "sunday"
    ]

    MEMCACHED_CONFIG = ['127.0.0.1:11211'
                        ]  # Localhost. May centralize in future.

    TASKING_FETCH_INTERVAL_SECONDS = 20
    STAFFJOY_API_KEY = os.environ.get("STAFFJOY_API_KEY")
    DEFAULT_TZ = "utc"

    # Used for searching for existing shifts
    MAX_SHIFT_LENGTH_HOURS = 23

    # Destroy container if there was an error
    KILL_ON_ERROR = True
    KILL_DELAY = 60  # To prevent infinite loop, sleep before kill


class StageConfig(DefaultConfig):
    ENV = "stage"


class DevelopmentConfig(DefaultConfig):
    ENV = "dev"
    LOG_LEVEL = logging.DEBUG
    SYSLOG = False
    TASKING_FETCH_INTERVAL_SECONDS = 5
    STAFFJOY_API_KEY = "staffjoydev"
    MAX_TUNING_TIME = 5 * 60  # 5 minutes
    THREADS = 2
    CALCULATION_TIMEOUT = 5 * 60  # 5 minutes, in seconds
    KILL_ON_ERROR = False


class TestConfig(DefaultConfig):
    ENV = "test"
    SYSLOG = False
    LOG_LEVEL = logging.DEBUG
    THREADS = 6
    CALCULATION_TIMEOUT = 5 * 60  # 5 minutes, in seconds
    KILL_ON_ERROR = False


config = {  # Determined in main.py
    "test": TestConfig,
    "dev": DevelopmentConfig,
    "stage": StageConfig,
    "prod": DefaultConfig,
}
