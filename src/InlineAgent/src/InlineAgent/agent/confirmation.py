from functools import wraps
from typing import Callable


def require_confirmation(message: str = None):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            confirmation_message = (
                message
                or f"Do you want to proceed with {func.__name__.replace('_', ' ').title()}?"
            )
            return func(*args, **kwargs)

        wrapper.__is_confirmation_required__ = True
        return wrapper

    # decorator.__is_confirmation_required__ = True

    # Handle both @require_confirmation and @require_confirmation()
    if callable(message):
        func = message
        message = None
        return decorator(func)
    return decorator
