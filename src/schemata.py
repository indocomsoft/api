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


UUID_REGEX = (
    "[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}"
)
EMAIL_REGEX = "^.+@.+$"


def generate_id_schema(id_name):
    return {id_name: {"type": "string", "regex": UUID_REGEX}}


SELLER_AUTH_SCHEMA = {
    "email": {"type": "string", "regex": EMAIL_REGEX},
    "password": {"type": "string", "minlength": 6},
}
CREATE_INVITE_SCHEMA = {
    "origin_seller_id": {"type": "string", "regex": UUID_REGEX},
    "destination_email": {"type": "string", "regex": EMAIL_REGEX},
}
