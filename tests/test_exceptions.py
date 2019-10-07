from src.exceptions import AcquityException


class DumbException(AcquityException):
    status_code = 1234


def test_status_code_initialisation():
    assert DumbException("haha").status_code == 1234
    assert DumbException("haha", 2345).status_code == 2345
