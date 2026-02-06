class CartBaseException(Exception):
    pass


class MovieAlreadyPurchasedException(CartBaseException):
    pass


class MovieAlreadyInCartException(CartBaseException):
    pass


class MovieNotInCartException(CartBaseException):
    pass


class CartIsNotExistException(CartBaseException):
    pass


class CartIsEmptyException(CartBaseException):
    pass
