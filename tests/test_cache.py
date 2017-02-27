from chomp import cache


class TestCache():
    def setup_method(self, method):
        self.cache = cache
        self.cache.flush()

    def teardown_method(self, method):
        self.cache.flush()

    def test_cache_caches(self):
        demand = [1, 2, 3, 2, 1]
        min_length = 1
        max_length = 2

        demo_shifts = [{"start": 1, "length": 2}, {"start": 3, "length": 4}]

        assert self.cache.get(
            demand=demand, min_length=min_length,
            max_length=max_length) is None

        self.cache.set(
            demand=demand,
            min_length=min_length,
            max_length=max_length,
            shifts=demo_shifts)

        assert self.cache.get(
            demand=demand,
            min_length=min_length,
            max_length=max_length, ) == demo_shifts

        # Fuzz it and make sure still none
        assert self.cache.get(
            demand=demand,
            min_length=min_length,
            max_length=(max_length + 1), ) is None

        assert self.cache.get(
            demand=demand,
            min_length=(min_length + 1),
            max_length=max_length, ) is None

        assert self.cache.get(
            demand=demand.append(1),
            min_length=min_length,
            max_length=max_length, ) is None
