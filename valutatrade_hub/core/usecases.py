from __future__ import annotations

from datetime import datetime
from typing import Tuple
from prettytable import PrettyTable

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import CurrencyNotFoundError, InsufficientFundsError, ApiRequestError
from valutatrade_hub.core.models import User, Portfolio, Wallet
from valutatrade_hub.core.utils import (
    load_users,
    save_users,
    load_portfolios,
    save_portfolios,
    load_rates, 
    save_rates, 
    is_rate_fresh
)
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.decorators import log_action

settings = SettingsLoader()

def register_user(username: str, password: str) -> Tuple[User, str]:
    """Регистрация нового пользователя.

    Возвращает (User, сообщение_для_пользователя).
    """
    if not username:
        raise ValueError("Имя пользователя не может быть пустым")

    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    users = load_users()

    # 1. Проверить уникальность username
    for u in users:
        if u.username == username:
            raise ValueError(f"Имя пользователя '{username}' уже занято")

    # 2. Сгенерировать user_id (автоинкремент)
    next_id = 1
    if users:
        next_id = max(u.user_id for u in users) + 1

    # 3. Создать пользователя (внутри User пароль будет захеширован с солью)
    # Соль можно сгенерировать как угодно, позже при необходимости вынесем
    salt = "static_salt_for_now"
    user = User(
        user_id=next_id,
        username=username,
        password=password,
        salt=salt,
        registration_date=datetime.now(),
    )

    users.append(user)
    save_users(users)

    # 5. Создать пустой портфель
    portfolios = load_portfolios()
    portfolios.append(
        {
            "user_id": user.user_id,
            "wallets": {},
        }
    )
    save_portfolios(portfolios)

    message = (
        f"Пользователь '{username}' зарегистрирован (id={user.user_id}). "
        f"Войдите: login --username {username} --password ****"
    )
    return user, message


def login_user(username: str, password: str) -> Tuple[User, str]:
    if not username:
        raise ValueError("Имя пользователя не может быть пустым")
    if not password:
        raise ValueError("Пароль не может быть пустым")

    users = load_users()

    found: Optional[User] = None
    for u in users:
        if u.username == username:
            found = u
            break

    if found is None:
        raise ValueError(f"Пользователь '{username}' не найден")

    if not found.verify_password(password):
        raise ValueError("Неверный пароль")

    msg = f"Вы вошли как '{username}'"
    return found, msg

def show_portfolio(user_id: int, base_currency: str = "USD") -> Tuple[str, float]:
    """Возвращает текст таблицы портфеля и итоговую стоимость в базовой валюте."""
    base = base_currency.upper()

    portfolios = load_portfolios()
    portfolio_dict = next(
        (p for p in portfolios if p["user_id"] == user_id),
        None,
    )
    if portfolio_dict is None:
        raise ValueError("Портфель пользователя не найден")

    wallets_data = portfolio_dict.get("wallets") or {}
    if not wallets_data:
        raise ValueError("У пользователя пока нет ни одного кошелька")

    # временно формируем объект Portfolio с фиктивным User (нужен только user_id)
    dummy_user = type("DummyUser", (), {"user_id": user_id})
    portfolio = Portfolio(user=dummy_user, wallets={})

    # создаём Wallet-ы из json
    for code, data in wallets_data.items():
        wallet = Wallet(currency_code=code, balance=float(data.get("balance", 0.0)))
        portfolio._wallets[code] = wallet  # noqa: SLF001

    total = portfolio.get_total_value(base_currency=base)

    table = PrettyTable(["Валюта", "Баланс", f"Стоимость в {base}"])  # [web:217][web:35][web:186]

    # здесь для упрощения считаем, что base = USD и курс 1:1
    for code, wallet in portfolio.wallets.items():
        balance = wallet.balance
        value_in_base = balance  # позже заменится расчётом по реальным курсам
        table.add_row([code, balance, value_in_base])

    return table.get_string(), total
    
@log_action("BUY", verbose=True)    
def buy_currency(
    user_id: int,
    currency_code: str,
    amount: float,
    base_currency: str = "USD",
) -> Tuple[str, str]:
    """Покупка валюты.

    Возвращает (сообщение_об_операции, сообщение_об_изменениях_портфеля).
    """
    currency = get_currency(currency_code)

    try:
        amount_value = float(amount)
    except (TypeError, ValueError):
        raise ValueError("'amount' должен быть положительным числом")

    if amount_value <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    base = (base_currency or settings.get("base_currency", "USD")).upper()

    portfolios = load_portfolios()
    portfolio_dict = next(
        (p for p in portfolios if p["user_id"] == user_id),
        None,
    )
    if portfolio_dict is None:
        raise ValueError("Портфель пользователя не найден")

    wallets = portfolio_dict.setdefault("wallets", {})

    wallet_data = wallets.get(currency.code)
    if wallet_data is None:
        wallets[currency.code] = {"balance": 0.0}
        wallet_data = wallets[currency.code]

    old_balance = float(wallet_data.get("balance", 0.0))
    new_balance = old_balance + amount_value
    wallet_data["balance"] = new_balance

    rate = 1.0
    estimated_cost = amount_value * rate

    save_portfolios(portfolios)

    operation_msg = (
        f"Покупка выполнена: {amount_value:.4f} {currency.code} "
        f"({currency.name}) по курсу {rate:.2f} {base}/{currency.code}"
    )
    changes_msg = (
        "Изменения в портфеле:\n"
        f"- {currency.code}: было {old_balance:.4f} → стало {new_balance:.4f}\n"
        f"Оценочная стоимость покупки: {estimated_cost:,.2f} {base}"
    )

    return operation_msg, changes_msg

@log_action("SELL", verbose=True)
def sell_currency(
    user_id: int,
    currency_code: str,
    amount: float,
    base_currency: str = "USD",
) -> Tuple[str, str]:
    """Продажа валюты.

    Возвращает (сообщение_об_операции, сообщение_об_изменениях_портфеля).
    """
    try:
        currency = get_currency(currency_code)
    except CurrencyNotFoundError as exc:
        raise ValueError(str(exc)) from exc

    try:
        amount_value = float(amount)
    except (TypeError, ValueError):
        raise ValueError("'amount' должен быть положительным числом")

    if amount_value <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    base = base_currency.upper()

    portfolios = load_portfolios()
    portfolio_dict = next(
        (p for p in portfolios if p["user_id"] == user_id),
        None,
    )
    if portfolio_dict is None:
        raise ValueError("Портфель пользователя не найден")

    wallets = portfolio_dict.get("wallets") or {}

    wallet_data = wallets.get(currency.code)
    if wallet_data is None:
        raise ValueError(
            f"У вас нет кошелька '{currency.code}'. "
            "Добавьте валюту: она создаётся автоматически при первой покупке."
        )

    old_balance = float(wallet_data.get("balance", 0.0))
    if amount_value > old_balance:
        # вместо ValueError
        raise InsufficientFundsError(
            available=old_balance,
            required=amount_value,
            code=currency.code,
        )

    new_balance = old_balance - amount_value
    wallet_data["balance"] = new_balance

    rate = 1.0
    estimated_income = amount_value * rate

    save_portfolios(portfolios)

    operation_msg = (
        f"Продажа выполнена: {amount_value:.4f} {currency.code} "
        f"({currency.name}) по курсу {rate:.2f} {base}/{currency.code}"
    )
    changes_msg = (
        "Изменения в портфеле:\n"
        f"- {currency.code}: было {old_balance:.4f} → стало {new_balance:.4f}\n"
        f"Оценочная выручка: {estimated_income:,.2f} {base}"
    )

    return operation_msg, changes_msg


def get_rate(from_currency: str, to_currency: str) -> Tuple[float, float, str]:
    try:
        from_cur = get_currency(from_currency)
        to_cur = get_currency(to_currency)
    except CurrencyNotFoundError:
        # просто пробрасываем – CLI обработает отдельно
        raise

    from_code = from_cur.code
    to_code = to_cur.code

    if from_code == to_code:
        raise ValueError("Коды валют должны отличаться")

    pair_key = f"{from_code}_{to_code}"
    reverse_key = f"{to_code}_{from_code}"

    rates = load_rates()

    pair = rates.get(pair_key)
    ttl_sec = int(settings.get("rates_ttl_seconds", 300))
    
    if pair and "rate" in pair and "updated_at" in pair:
    
        if is_rate_fresh(pair["updated_at"], max_age_minutes=ttl_sec // 60):
            rate_forward = float(pair["rate"])
            updated_at = pair["updated_at"]
            rev = rates.get(reverse_key)
            if rev and "rate" in rev:
                rate_reverse = float(rev["rate"])
            else:
                rate_reverse = 1.0 / rate_forward if rate_forward != 0 else 0.0
            return rate_forward, rate_reverse, updated_at

    now = datetime.now().isoformat(timespec="seconds")
    if from_code == "USD" and to_code == "BTC":
        rate_forward = 0.00001685
    elif from_code == "BTC" and to_code == "USD":
        rate_forward = 59337.21
    else:
        raise ApiRequestError(f"Курс {from_code}→{to_code} недоступен. Повторите попытку позже.")

    rate_reverse = 1.0 / rate_forward if rate_forward != 0 else 0.0

    rates[pair_key] = {"rate": rate_forward, "updated_at": now}
    rates[reverse_key] = {"rate": rate_reverse, "updated_at": now}
    rates["source"] = "ParserService"
    rates["last_refresh"] = now

    save_rates(rates)

    return rate_forward, rate_reverse, now
