from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List

from .models import User, Portfolio

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"


def load_users() -> List[User]:
    if not USERS_FILE.exists():
        return []

    with USERS_FILE.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    users: List[User] = []
    for item in raw:
        user = User(
            user_id=item["user_id"],
            username=item["username"],
            password="stub",
            salt=item["salt"],
            registration_date=datetime.fromisoformat(item["registration_date"]),
        )
        user._hashed_password = item["hashed_password"]  # noqa: SLF001
        users.append(user)
    return users


def save_users(users: List[User]) -> None:
    data = []
    for u in users:
        info = u.get_user_info()
        data.append(
            {
                "user_id": info["user_id"],
                "username": info["username"],
                "hashed_password": u._hashed_password,  # noqa: SLF001
                "salt": u.salt,
                "registration_date": info["registration_date"],
            }
        )

    with USERS_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_portfolios() -> list[dict]:
    if not PORTFOLIOS_FILE.exists():
        return []
    with PORTFOLIOS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_portfolios(portfolios: list[dict]) -> None:
    with PORTFOLIOS_FILE.open("w", encoding="utf-8") as f:
        json.dump(portfolios, f, ensure_ascii=False, indent=4)

