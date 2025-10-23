from time import perf_counter
from functools import wraps
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")


def timeit(label: str = "") -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            t0 = perf_counter()
            result = func(*args, **kwargs)
            dt = perf_counter() - t0
            print(f"{label or func.__name__}: {dt * 1000:.2f} ms")
            return result

        return wrapper

    return decorator

# @timeit("compute")
# def compute(n: int) -> int:
#     return sum(range(n))
