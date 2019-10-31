class AcquityException(Exception):
    status_code = 500

    def __init__(self, message="", status_code=None):
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        else:
            self.status_code = type(self).status_code


class InvalidRequestException(AcquityException):
    status_code = 422


class UnauthorizedException(AcquityException):
    status_code = 403


class ResourceNotOwnedException(AcquityException):
    status_code = 404


class ResourceNotFoundException(AcquityException):
    status_code = 404


class InvisibleUnauthorizedException(AcquityException):
    status_code = 404
