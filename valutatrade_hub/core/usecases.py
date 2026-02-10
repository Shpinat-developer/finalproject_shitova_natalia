from __future__ import annotations

from datetime import datetime
from typing import Tuple
from prettytable import PrettyTable

from valutatrade_hub.core.models import User, Portfolio, Wallet
from valutatrade_hub.core.utils import (
    load_users,
    save_users,
    load_portfolios,
    save_portfolios,
)


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
    
def buy_currency(
    user_id: int,
    currency_code: str,
    amount: float,
    base_currency: str = "USD",
) -> Tuple[str, str]:
    """Покупка валюты.

    Возвращает (сообщение_об_операции, сообщение_об_изменениях_портфеля).
    """
    code = (currency_code or "").upper()
    if not code:
        raise ValueError("currency не может быть пустым")

    # 2. Валидировать amount > 0
    try:
        amount_value = float(amount)
    except (TypeError, ValueError):
        raise ValueError("'amount' должен быть положительным числом")  # noqa: B904

    if amount_value <= 0:
        raise ValueError("'amount' должен быть положительным числом")  # [web:246][web:251]

    base = base_currency.upper()

    # 3. Загрузить портфели и найти портфель пользователя
    portfolios = load_portfolios()
    portfolio_dict = next(
        (p for p in portfolios if p["user_id"] == user_id),
        None,
    )
    if portfolio_dict is None:
        raise ValueError("Портфель пользователя не найден")

    wallets = portfolio_dict.setdefault("wallets", {})

    # 3. Если кошелька нет — создать
    wallet_data = wallets.get(code)
    if wallet_data is None:
        wallets[code] = {"balance": 0.0}
        wallet_data = wallets[code]

    old_balance = float(wallet_data.get("balance", 0.0))

    # 4. Увеличить баланс кошелька
    new_balance = old_balance + amount_value
    wallet_data["balance"] = new_balance

    # 5. Заглушка для курса: считаем, что 1 единица currency = 1 base
    rate = 1.0
    estimated_cost = amount_value * rate

    save_portfolios(portfolios)

    operation_msg = (
        f"Покупка выполнена: {amount_value:.4f} {code} по курсу {rate:.2f} {base}/{code}"
    )
    changes_msg = (
        f"Изменения в портфеле:\n"
        f"- {code}: было {old_balance:.4f} → стало {new_balance:.4f}\n"
        f"Оценочная стоимость покупки: {estimated_cost:,.2f} {base}"
    )

    return operation_msg, changes_msg
    
def sell_currency(
    user_id: int,
    currency_code: str,
    amount: float,
    base_currency: str = "USD",
) -> Tuple[str, str]:
    """Продажа валюты.

    Возвращает (сообщение_об_операции, сообщение_об_изменениях_портфеля).
    """
    code = (currency_code or "").upper()
    if not code:
        raise ValueError("currency не может быть пустым")

    try:
        amount_value = float(amount)
    except (TypeError, ValueError):
        raise ValueError("'amount' должен быть положительным числом")  # [web:246][web:251]

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

    # 3. Проверить, что кошелёк существует и средств хватает
    wallet_data = wallets.get(code)
    if wallet_data is None:
        raise ValueError(f"У вас нет кошелька '{code}'. "
            "Добавьте валюту: она создаётся автоматически при первой покупке."
        )
        
    old_balance = float(wallet_data.get("balance", 0.0))
    if amount_value > old_balance:
        raise ValueError(
            f"Недостаточно средств: доступно {old_balance:.4f} {code}, "
            f"требуется {amount_value:.4f} {code}"
        )


    # 4. Уменьшить баланс
    new_balance = old_balance - amount_value
    wallet_data["balance"] = new_balance

    # 5. Заглушка для курса: 1:1, начисление в USD можно добавить позже
    rate = 1.0
    estimated_income = amount_value * rate

    save_portfolios(portfolios)

    operation_msg = (
        f"Продажа выполнена: {amount_value:.4f} {code} по курсу {rate:.2f} {base}/{code}"
    )
    changes_msg = (
        f"Изменения в портфеле:\n"
        f"- {code}: было {old_balance:.4f} → стало {new_balance:.4f}\n"
        f"Оценочная выручка: {estimated_income:,.2f} {base}"
    )

    return operation_msg, changes_msg

