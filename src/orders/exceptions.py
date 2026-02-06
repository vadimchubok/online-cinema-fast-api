class OrderBaseException(Exception):
    pass


class UserNotFoundException(OrderBaseException):
    pass


class OrderNotFoundException(OrderBaseException):
    pass


class CancellationIsNotAvailable(OrderNotFoundException):
    pass


class MovieIsNotAvailableException(OrderBaseException):
    pass

class OrderAlreadyPendingException(OrderBaseException):
    pass

