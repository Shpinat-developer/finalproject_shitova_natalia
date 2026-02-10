from __future__ import annotations

from datetime import datetime
from typing import Tuple

from valutatrade_hub.core.models import User, Portfolio
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

