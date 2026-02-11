from __future__ import annotations
from abc import ABC, abstractmethod  
from dataclasses import dataclass
from typing import Dict
from .exceptions import CurrencyNotFoundError

def _validate_code(code: str) -> str:
    code = (code or "").upper()
    if not (2 <= len(code) <= 5) or " " in code:
        raise ValueError("Некорректный код валюты: должен быть 2–5 символов, без пробелов, в верхнем регистре")
    return code

def _validate_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        raise ValueError("Имя валюты не может быть пустым")
    return name

@dataclass
class Currency(ABC):
    """Абстрактная базовая валюта."""
    name: str
    code: str

    def __post_init__(self) -> None:
        # Общая валидация для всех валют
        self.code = _validate_code(self.code)
        self.name = _validate_name(self.name)

    @abstractmethod
    def get_display_info(self) -> str:
        """Строковое представление для UI/логов."""
        raise NotImplementedError

@dataclass
class FiatCurrency(Currency):
    issuing_country: str

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"

@dataclass
class CryptoCurrency(Currency):
    algorithm: str
    market_cap: float

    def get_display_info(self) -> str:
        # Краткая форма капитализации в научной нотации
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"


_CURRENCY_REGISTRY: Dict[str, Currency] = {
    "USD": FiatCurrency(name="US Dollar", code="USD", issuing_country="United States"),
    "EUR": FiatCurrency(name="Euro", code="EUR", issuing_country="Eurozone"),
    "RUB": FiatCurrency(name="Russian Ruble", code="RUB", issuing_country="Russia"),
    "BTC": CryptoCurrency(name="Bitcoin", code="BTC", algorithm="SHA-256", market_cap=1.12e12),
    "ETH": CryptoCurrency(name="Ethereum", code="ETH", algorithm="Ethash", market_cap=4.50e11),
}


"""def get_currency(code: str) -> Currency:

    norm_code = _validate_code(code)
    currency = _CURRENCY_REGISTRY.get(norm_code)
    if currency is None:

        raise CurrencyNotFoundError(f"Валюта с кодом '{norm_code}' не найдена")
    return currency"""
    
def get_currency(code: str) -> Currency:
    norm_code = _validate_code(code)
    currency = _CURRENCY_REGISTRY.get(norm_code)
    if currency is None:
        raise CurrencyNotFoundError(norm_code)
    return currency

