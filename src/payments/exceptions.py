class BasePaymentException(Exception):
    pass


class PaymentNotFound(BasePaymentException):
    pass
