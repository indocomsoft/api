from sanic.exceptions import SanicException


class ApiException(SanicException):
    status_code = 500

    def __init__(self, message, status_code=None):
        super().__init__(message=message, status_code=status_code)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        else:
            self.status_code = type(self).status_code


class InvalidRequestException(ApiException):
    status_code = 422
