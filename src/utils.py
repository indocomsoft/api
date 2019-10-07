from collections import Mapping
from exceptions import InvalidRequestException
from functools import wraps


def expects_json_object(func):
    @wraps(func)
    def decorated_func(request, *args, **kwargs):
        if not isinstance(request.json, Mapping):
            raise InvalidRequestException("Request body must be an object")

        return func(request, *args, **kwargs)

    return decorated_func
