# Placeholder for data_fetcher package
# This file was created to resolve ModuleNotFoundError during testing.

def cache_within_request(func):
    """
    Placeholder decorator for caching within request.
    """
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
