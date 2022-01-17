import logging
from functools import wraps

logger = logging.getLogger('jobs.executor')


def retry(count=1):
    def wrapper(func):
        async def wrapped(*args, **kwargs):
            msg = ''
            retries = 0
            while retries < count:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    msg = str(e)
                    retries += 1
            logger.error('Job %s finished with error %s', func.__name__, msg)

        return wrapped

    return wrapper
