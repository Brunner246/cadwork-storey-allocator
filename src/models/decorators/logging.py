from functools import wraps
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")


def log_calls(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"→ {func.__name__} called with args={args!r}, kwargs={kwargs!r}")
        # print(f"← {func.__name__} -> {result!r}")
        return func(*args, **kwargs)

    return wrapper

# @log_calls
# def add(a: int, b: int) -> int:
#     return a + b
#
#
# if __name__ == "__main__":
#     result = add(2, b=3)
#     print(f"Result: {result!r}")
