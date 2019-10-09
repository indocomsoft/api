import json
from functools import wraps

from cerberus import Validator

from src.exceptions import InvalidRequestException


def validate_input(schema):
    def decorator(func):
        @wraps(func)
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

UUID_RULE = {"type": "string", "regex": UUID_REGEX}
EMAIL_RULE = {"type": "string", "regex": EMAIL_REGEX}
NONNEGATIVE_NUMBER_RULE = {"type": "number", "min": 0}
OPTIONAL_NONNEGATIVE_NUMBER_RULE = {"type": "number", "min": 0, "required": False}


SELLER_AUTH_SCHEMA = {
    "email": EMAIL_RULE,
    "password": {"type": "string", "minlength": 6},
}
SELLER_AUTH_SCHEMA_WITH_INVITATION = {
    "email": EMAIL_RULE,
    "full_name": {"type": "string"},
    "password": {"type": "string", "minlength": 6},
    "check_invitation": {"type": "boolean"},
}
CREATE_INVITE_SCHEMA = {"origin_seller_id": UUID_RULE, "destination_email": EMAIL_RULE}
CREATE_SELL_ORDER_SCHEMA = {
    "seller_id": UUID_RULE,
    "number_of_shares": NONNEGATIVE_NUMBER_RULE,
    "price": NONNEGATIVE_NUMBER_RULE,
    "security_id": UUID_RULE,
}
EDIT_SELL_ORDER_SCHEMA = {
    "id": UUID_RULE,
    "subject_id": UUID_RULE,
    "new_number_of_shares": OPTIONAL_NONNEGATIVE_NUMBER_RULE,
    "new_price": OPTIONAL_NONNEGATIVE_NUMBER_RULE,
}
DELETE_SELL_ORDER_SCHEMA = {"id": UUID_RULE, "subject_id": UUID_RULE}
