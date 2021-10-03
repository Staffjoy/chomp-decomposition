import logging
from logging.handlers import SysLogHandler
import sys
import os

from .config import config
from .cache import Cache

# This file initializes the Chomp package.
#
# Within the chomp files, you want to import these:
#
# * logger - for logging
# * config - for getting different configurations

# Now when things import, we load the settings based on their env
config = config[os.environ.get("ENV", "dev")]

# Logging configuration
logger = logging.getLogger(__name__)


class ContextFilter(logging.Filter):
    hostname = "chomp-%s" % config.ENV

    def filter(self, record):
        record.hostname = self.hostname
        return True


f = ContextFilter()
logger.setLevel(config.LOG_LEVEL)
logger.addFilter(f)

if config.SYSLOG:
    # Send to syslog / papertrail server
    syslog_tuple = config.SYSLOG_SERVER.split(":")
    handler = SysLogHandler(address=(syslog_tuple[0], int(syslog_tuple[1])))
else:
    # Just print to standard out
    handler = logging.StreamHandler(sys.stdout)

formatter = logging.Formatter(
    "%(asctime)s %(hostname)s chomp %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
handler.setFormatter(formatter)
handler.setLevel(config.LOG_LEVEL)
logger.addHandler(handler)

# Set up caching client
cache = Cache(config, logger)

# Import things we are exporting
from .decompose import Decompose
from .splitter import Splitter
from .tasking import Tasking

logger.info("Initialized environment %s", config.ENV)
