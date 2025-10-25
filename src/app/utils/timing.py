# import time
# from contextlib import contextmanager

# @contextmanager
# def timer(cb):
#     t0 = time.perf_counter()
#     try:
#         yield
#     finally:
#         cb(time.perf_counter() - t0)

# src/app/utils/timing.py
"""
Utility for lightweight execution timing.

Provides a context manager `timer(cb)` that measures the elapsed
time of a code block and passes it to a callback function.
"""

import time
from contextlib import contextmanager
from typing import Callable, Generator


@contextmanager
def timer(cb: Callable[[float], None]) -> Generator[None, None, None]:
    """
    Measure elapsed time for a code block and send it to a callback.

    Parameters
    ----------
    cb : Callable[[float], None]
        Callback that receives the elapsed time in seconds.

    Example
    -------
    >>> with timer(lambda t: print(f"Elapsed: {t:.3f}s")):
    ...     heavy_operation()
    Elapsed: 1.532s
    """
    t0 = time.perf_counter()
    try:
        yield
    finally:
        cb(time.perf_counter() - t0)
