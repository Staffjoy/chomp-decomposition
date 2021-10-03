import memcache
import json
import hashlib


class Cache:
    """Subproblem caching"""

    def __init__(self, config, logger):
        self.mc = memcache.Client(config.MEMCACHED_CONFIG)
        self.config = config
        self.logger = logger

    def set(self, shifts=None, **subproblem):
        """Given a subproblem's inputs, store the results"""
        if shifts is None or len(shifts) is 0:
            raise Exception("Do not set an empty cache")

        self.mc.set(self._subproblem_to_key(subproblem), shifts)

    def get(self, **subproblem):
        """Check cache for a subproblem"""
        return self.mc.get(self._subproblem_to_key(subproblem))

    def flush(self):
        """Flush all caches. Mainly used for testing."""
        # Set to warning becuase this probably shouldn't happen in prod
        self.logger.warning("Cache flushed")
        self.mc.flush_all()

    @staticmethod
    def _subproblem_to_key(subproblem):
        """Convert a subproblem into a memcached key"""
        # Cannot just use straight json because it has spaces,
        # which memcache does not support. Hash is repeatable and
        # also make sure we stay under the memcache key length limit
        return hashlib.sha256(json.dumps(subproblem, sort_keys=True).encode('utf-8')).hexdigest()
