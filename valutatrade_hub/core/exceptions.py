class CurrencyNotFoundError(Exception):
    """Неизвестная валюта."""
    def __init__(self, code: str) -> None:
        self.code = code
        message = f"Неизвестная валюта '{code}'"
        super().__init__(message)

class InsufficientFundsError(Exception):
    """Недостаточно средств на кошельке."""
    def __init__(self, available: float, required: float, code: str) -> None:
        message = (
            f"Недостаточно средств: доступно {available:.4f} {code}, "
            f"требуется {required:.4f} {code}"
        )
        super().__init__(message)
        self.available = available
        self.required = required
        self.code = code

class ApiRequestError(Exception):
    """Ошибка при обращении к внешнему API получения курсов."""
    def __init__(self, reason: str) -> None:
        message = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(message)
        self.reason = reason




