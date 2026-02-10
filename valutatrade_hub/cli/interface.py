import shlex
from valutatrade_hub.core.usecases import register_user, login_user
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



