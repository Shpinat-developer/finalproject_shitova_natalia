from datetime import datetime
from typing import Dict
import hashlib

"""Класс User (пользователь системы)   """
class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        password: str,
        salt: str,
        registration_date: datetime,
    ) -> None:
        # приватные атрибуты
        self._user_id = user_id
        self._username = ""
        self._hashed_password = ""
        self._salt = salt
        self._registration_date = registration_date

        # используем сеттеры, чтобы проверки сработали
        self.username = username
        self.password = password
        
        
    # --- user_id 

    @property
    def user_id(self) -> int:
        return self._user_id

    # --- username ---

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not value:
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value

    # --- password 

    @property
    def password(self) -> str:
        # пароль наружу не отдаём
        raise AttributeError("Нельзя читать пароль")

    @password.setter
    def password(self, value: str) -> None:
        if len(value) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._hashed_password = self._hash_password(value, self._salt)

    # --- salt ---

    @property
    def salt(self) -> str:
        return self._salt

    @salt.setter
    def salt(self, value: str) -> None:
        self._salt = value

    # --- registration_date 

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    # --- служебное хеширование пароля ---

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        data = (password + salt).encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def get_user_info(self) -> dict:
        """Информация о пользователе без пароля."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str) -> None:
        """Меняет пароль с проверкой длины и хешированием."""
        self.password = new_password

    def verify_password(self, password: str) -> bool:
        """Проверяет введённый пароль на совпадение с сохранённым хешем."""
        expected = self._hash_password(password, self._salt)
        return self._hashed_password == expected

"""Класс Wallet (кошелёк пользователя для одной конкретной валюты)  """

class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0) -> None:
        self.currency_code = currency_code
        self._balance = 0.0
        self.balance = balance

    def deposit(self, amount: float) -> None:
        """Пополнение баланса."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self._balance += float(amount)

    def withdraw(self, amount: float) -> None:
        """Снятие средств, если хватает баланса."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        if amount > self._balance:
            raise ValueError("Недостаточно средств на балансе")
        self._balance -= float(amount)

    def get_balance_info(self) -> dict:
        """Информация о текущем балансе."""
        return {
            "currency_code": self.currency_code,
            "balance": self._balance,
        }

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

"""Класс Portfolio (управление всеми кошельками одного пользователя)  """

class Portfolio:
    def __init__(
        self,
        user: User,
        wallets: Dict[str, Wallet] | None = None,
    ) -> None:
        self._user = user
        self._user_id = user.user_id
        self._wallets: Dict[str, Wallet] = wallets or {}

    # --- свойства ---

    @property
    def user(self) -> User:
        """Объект пользователя (без возможности перезаписи)."""
        return self._user

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        """Копия словаря кошельков, чтобы снаружи не ломали внутреннее состояние."""
        return self._wallets.copy()  
        
    # --- работа с кошельками ---

    def add_currency(self, currency_code: str) -> Wallet:
        """Добавляет новый кошелёк для валюты, если его ещё нет."""
        code = currency_code.upper()
        if code in self._wallets:
            raise ValueError(f"Кошелёк для валюты {code} уже существует")
        wallet = Wallet(currency_code=code, balance=0.0)
        self._wallets[code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Wallet:
        """Возвращает кошелёк по коду валюты."""
        code = currency_code.upper()
        if code not in self._wallets:
            raise KeyError(f"Кошелёк для валюты {code} не найден")
        return self._wallets[code]

    def get_total_value(self, base_currency: str = "USD") -> float:
        """Общая стоимость всех валют в указанной базовой валюте.

        Для учебных целей используем фиксированные курсы в словаре exchange_rates.
        """
        base = base_currency.upper()
        
        
        # фиктивные курсы
        exchange_rates: Dict[str, float] = {
            "USD": 1.0,       
            "EUR": 1.1,       
            "BTC": 60000.0,   
            "ETH": 3000.0,    
        }

        if base not in exchange_rates:
            raise ValueError(f"Нет курса для базовой валюты {base}")

        total_in_base = 0.0
        for code, wallet in self._wallets.items():
            rate_to_usd = exchange_rates.get(code)
            if rate_to_usd is None:
                # валюты без курса можно пропустить или обработать отдельно
                continue
            value_in_usd = wallet.balance * rate_to_usd
            # если base != USD, конвертируем из USD в base
            total_in_base += value_in_usd / exchange_rates[base]

        return total_in_base

