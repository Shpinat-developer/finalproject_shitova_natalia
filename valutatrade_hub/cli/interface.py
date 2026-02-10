import shlex
from valutatrade_hub.core.usecases import register_user, login_user, show_portfolio, buy_currency, sell_currency, get_rate
from valutatrade_hub.core.models import User
from valutatrade_hub.core.exceptions import InsufficientFundsError, CurrencyNotFoundError, ApiRequestError

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

        if command in {"exit", "quit"}:
            print("Выход.")
            break

        if command == "register":
            handle_register(args)
        elif command == "login":
            handle_login(args)
        elif command == "show-portfolio":
            if CURRENT_USER is None:
                print("Сначала выполните login.")
            else:
                handle_show_portfolio(args)
        elif command == "buy":
            if CURRENT_USER is None:
                print("Сначала выполните login.")
            else:
                handle_buy(args)
        elif command == "sell":
            if CURRENT_USER is None:
                print("Сначала выполните login.")
            else:
                handle_sell(args)
        elif command == "get-rate":
            handle_get_rate(args)
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
    global CURRENT_USER

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
            amount=amount or "",
        )
    except CurrencyNotFoundError as exc:
        print(str(exc))
        print("Используйте 'help get-rate' или посмотрите список поддерживаемых валют.")
        return
    except InsufficientFundsError as exc:
        # обычно для buy не нужно, но можно оставить на будущее
        print(str(exc))
        return
    except ApiRequestError as exc:
        print(str(exc))
        print("Попробуйте повторить операцию позже или проверьте сеть.")
        return
    except ValueError as exc:
        # ошибки валидации amount и т.п.
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
            currency_code=currency,
            amount=amount,
        )
    except InsufficientFundsError as exc:
        print(str(exc))  # текст как есть
        return
    except CurrencyNotFoundError as exc:
        print(str(exc))
        print("Используйте 'help get-rate' или посмотрите список поддерживаемых валют.")
        return
    except ApiRequestError as exc:
        print(str(exc))
        print("Попробуйте повторить операцию позже или проверьте соединение с интернетом.")
        return

    print(op_msg)
    print(changes_msg)
    
def handle_get_rate(args: list[str]) -> None:
    from_code = None
    to_code = None

    it = iter(args)
    for token in it:
        if token == "--from":
            from_code = next(it, None)
        elif token == "--to":
            to_code = next(it, None)

    try:
        rate_fwd, rate_rev, updated_at = get_rate(from_code, to_code)
    except CurrencyNotFoundError as exc:
        print(str(exc))
        print("Используйте 'help get-rate' или проверьте код валюты.")
        return
    except ApiRequestError as exc:
        print(str(exc))
        print("Попробуйте повторить позже или проверьте сеть.")
        return

    print(
        f"Курс {from_code.upper()}→{to_code.upper()}: {rate_fwd:.8f} "
        f"(обновлено: {updated_at.replace('T', ' ')})"
    )
    print(f"Обратный курс {to_code.upper()}→{from_code.upper()}: {rate_rev:.2f}")




