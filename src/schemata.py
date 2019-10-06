import json
from exceptions import InvalidRequestException

from cerberus import Validator


def validate_input(schema):
    def decorator(func):
        def decorated_func(*args, **kwargs):
            validator = Validator(schema, require_all=True)
            res = validator.validate(kwargs)
            if not res:
                raise InvalidRequestException(validator.errors)

            return func(*args, **kwargs)

        return decorated_func

    return decorator


SELLER_AUTH_SCHEMA = {"email": {"type": "string"}, "password": {"type": "string"}}
