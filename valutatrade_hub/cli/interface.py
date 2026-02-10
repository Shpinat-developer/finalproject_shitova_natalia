import shlex
from valutatrade_hub.core.usecases import register_user, login_user, show_portfolio, buy_currency, sell_currency
from valutatrade_hub.core.models import User

CURRENT_USER: User | None = None


def main() -> None:
    print("ValutaTrade Hub CLI. Введите команду (help для справки, exit для выхода).")

    while True:
        try:
            raw = input("> ")
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break

        if not raw.strip():
            continue

        parts = shlex.split(raw)
        if not parts:
            continue

        command, *args = parts

        if command == "exit" or command == "quit":
            print("Выход.")
            break

        if command == "register":
            handle_register(args)
        elif command == "login":
            handle_login(args)
        elif command == "show-portfolio":
            handle_show_portfolio(args)
        elif command == "buy":
            handle_buy(args)
        elif command == "sell":
            handle_sell(args)
        else:
            print(f"Неизвестная команда: {command}")
            

def handle_register(args: list[str]) -> None:
    username = None
    password = None

    it = iter(args)
    for token in it:
        if token == "--username":
            username = next(it, None)
        elif token == "--password":
            password = next(it, None)

    try:
        _, msg = register_user(username=username or "", password=password or "")
    except ValueError as exc:
        print(str(exc))
        return

    print(msg)
    
def handle_login(args: list[str]) -> None:
    global CURRENT_USER

    username = None
    password = None

    it = iter(args)
    for token in it:
        if token == "--username":
            username = next(it, None)
        elif token == "--password":
            password = next(it, None)

    try:
        user, msg = login_user(username=username or "", password=password or "")
    except ValueError as exc:
        print(str(exc))
        return

    CURRENT_USER = user
    print(msg)

def handle_show_portfolio(args: list[str]) -> None:
    if CURRENT_USER is None:
        print("Сначала войдите в систему: login --username <имя> --password <пароль>")
        return

    base = "USD"

    it = iter(args)
    for token in it:
        if token == "--base":
            base = (next(it, "") or "").upper()

    try:
        table_str, total = show_portfolio(user_id=CURRENT_USER.user_id, base_currency=base)
    except ValueError as exc:
        print(str(exc))
        return

    print(table_str)
    print(f"Итоговая стоимость портфеля в {base}: {total}")
    
def handle_buy(args: list[str]) -> None:
    if CURRENT_USER is None:
        print("Сначала войдите в систему: login --username <имя> --password <пароль>")
        return

    currency = None
    amount = None

    it = iter(args)
    for token in it:
        if token == "--currency":
            currency = next(it, None)
        elif token == "--amount":
            amount = next(it, None)

    try:
        op_msg, changes_msg = buy_currency(
            user_id=CURRENT_USER.user_id,
            currency_code=currency or "",
            amount=float(amount) if amount is not None else 0.0,
            base_currency="USD",
        )
    except ValueError as exc:
        print(str(exc))
        return

    print(op_msg)
    print(changes_msg)

def handle_sell(args: list[str]) -> None:
    if CURRENT_USER is None:
        print("Сначала войдите в систему: login --username <имя> --password <пароль>")
        return

    currency = None
    amount = None

    it = iter(args)
    for token in it:
        if token == "--currency":
            currency = next(it, None)
        elif token == "--amount":
            amount = next(it, None)

    try:
        op_msg, changes_msg = sell_currency(
            user_id=CURRENT_USER.user_id,
            currency_code=currency or "",
            amount=float(amount) if amount is not None else 0.0,
            base_currency="USD",
        )
    except ValueError as exc:
        print(str(exc))
        return

    print(op_msg)
    print(changes_msg)



