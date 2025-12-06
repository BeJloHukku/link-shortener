from functools import wraps
from typing import Callable


def retry(times: int, exception):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < times:
                try:
                    return await func(*args, **kwargs)
                except exception:
                    print(f"Try {attempt + 1} to generate slug was failed")
                attempt += 1
            return await func(*args, **kwargs)
        return wrapper
    return decorator