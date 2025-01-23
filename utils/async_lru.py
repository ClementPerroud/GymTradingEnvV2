import asyncio
import functools
from collections import OrderedDict
from datetime import datetime

def _convert_to_hashable(value):
    """
    Convert a value into a hashable representation so it can be used as part of the cache key.
    - dict -> sorted tuple of (key, converted_value)
    - list/tuple/set -> (type_name, tuple(sorted/converted_items))
    - datetime -> ('datetime', value.isoformat())
    - objects with stable __hash__ -> ('objhash', hash(value))
    - fallback -> ('repr', repr(value))
    """
    if isinstance(value, dict):
        return ('dict', tuple(sorted(
            (k, _convert_to_hashable(v)) for k, v in value.items()
        )))
    elif isinstance(value, (list, tuple, set)):
        # To handle sets (and to ensure consistent ordering),
        # we sort the items. For lists/tuples, you may prefer
        # preserving the actual order, depending on your needs.
        return (type(value).__name__, tuple(
            sorted(_convert_to_hashable(v) for v in value)
        ))
    elif isinstance(value, datetime):
        return ('datetime', value.isoformat())
    elif hasattr(value, '__hash__') and value.__hash__ is not None:
        return ('objhash', hash(value))
    else:
        # Fallback: rely on the string repr
        return ('repr', repr(value))

def make_key(args, kwargs):
    """Build a cache key out of function positional and keyword arguments."""
    converted_args = tuple(_convert_to_hashable(a) for a in args)
    converted_kwargs = tuple(
        sorted((k, _convert_to_hashable(v)) for k, v in kwargs.items())
    )
    return (converted_args, converted_kwargs)

class AsyncLRUCache:
    """
    An async LRU cache that uses an OrderedDict internally to keep track of
    insertion order, allowing it to pop out the oldest item when maxsize is reached.

    Additionally, it implements *single-flight* concurrency for each key:
    if multiple coroutines call 'get()' concurrently with the same key, only
    one will actually compute the result. The rest will wait for that result.
    """
    def __init__(self, maxsize=128):
        self.maxsize = maxsize
        self.cache = OrderedDict()  # actual LRU cache storage
        self.inflight = {}          # tracks in-progress tasks for specific keys
        self.lock = asyncio.Lock()

    async def get(self, key, coro_factory):
        """
        If 'key' is in the cache, return the cached value.
        Otherwise:
          1) If there's already an in-flight task for that key, await it.
          2) If not, create the task, run it, cache the result, return the result.
        """
        
        async with self.lock:
            # 1) Check the cache first
            if key in self.cache:
                # Move to the end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                # print("cache hit -> ", key, " : ", value)
                return value

            # 2) If there's an in-flight task for 'key', wait on it
            if key in self.inflight:
                future = self.inflight[key]
            else:
                # No in-flight task, so create one
                future = asyncio.create_task(coro_factory())
                self.inflight[key] = future

        # At this point, we have an in-flight future that may or may not belong to us
        # (either we created it, or someone else did). We'll wait for it outside the lock.
        try:
            value = await future
            # print("cache create -> ", key, " : ", value)
        except Exception as e:
            # If the task fails, remove it from inflight so that a subsequent call
            # can try again
            async with self.lock:
                # Only remove if we are still the in-flight future
                if self.inflight.get(key) is future:
                    del self.inflight[key]
            raise e

        # Once the future completes, store in the cache & remove from inflight
        async with self.lock:
            if key in self.inflight and self.inflight[key] is future:
                del self.inflight[key]

            # Insert into LRU
            # Possibly the value got inserted by a different task while we were awaiting
            # but let's just re-insert to ensure updated recency
            if key in self.cache:
                self.cache.pop(key)
            self.cache[key] = value

            # Enforce LRU size
            if len(self.cache) > self.maxsize:
                self.cache.popitem(last=False)  # remove oldest

        return value

    def clear(self):
        """Clear all items from cache and reset inflight tasks."""
        self.cache.clear()
        self.inflight.clear()

def alru_cache(maxsize=128):
    """
    Decorator that applies an async LRU cache to an async function with single-flight concurrency.

    - All calls to the same function with the same arguments will be deduplicated:
      if multiple tasks hit the function concurrently with identical arguments, only
      one will call the underlying function. Others will await the same result.

    - The wrapped function has a 'cache_clear()' method to empty the cache.
    """
    def decorator(coro):
        cache = AsyncLRUCache(maxsize=maxsize)

        @functools.wraps(coro)
        async def wrapper(*args, **kwargs):
            key = make_key(args, kwargs)
            return await cache.get(key, lambda: coro(*args, **kwargs))

        def cache_clear():
            cache.clear()

        wrapper.cache_clear = cache_clear
        return wrapper

    return decorator
