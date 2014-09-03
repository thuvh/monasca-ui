import functools
from time import time


def memoize(_cache=None, expiry_time=0, num_args=None):
    """
    Wrap a function so that results for any argument tuple are stored in
    'cache'. Note that the args to the function must be usable as dictionary
    keys.

    The function is re-evaluated if the value in the cache has passed the
    expiry_time (in seconds).

    Only the first num_args are considered when creating the key.
    """
    def _decorator(func):
        @functools.wraps(func)
        def _memoize(*args, **kw):
            # Determine what cache to use - the supplied one, or one we create
            # inside the wrapped function.
            cache = _cache
            if _cache is None and not hasattr(func, '_cache'):
                func._cache = {}
                cache = func._cache

            mem_args = args[:num_args]
            # frozenset is used to ensure hashability
            if kw:
                key = mem_args, frozenset(kw.iteritems())
            else:
                key = mem_args

            if key in cache:
                result, timestamp = cache[key]
                # Check the age.
                age = time() - timestamp
                if not expiry_time or age < expiry_time:
                    return result
            result = func(*args, **kw)
            cache[key] = (result, time())
            return result
        return _memoize

    return _decorator


