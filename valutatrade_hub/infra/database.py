# valutatrade_hub/decorators.py
import functools
import logging
from datetime import datetime

logger = logging.getLogger("valutatrade.actions")


def log_action(action: str, verbose: bool = False):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ts = datetime.now().isoformat(timespec="seconds")

            # Берём user_id и прочие параметры из kwargs (как ты договорилась в usecases)
            user_id = kwargs.get("user_id") or "unknown"
            currency_code = kwargs.get("currency_code") or ""
            amount = kwargs.get("amount") or ""
            base_currency = kwargs.get("base_currency") or ""

            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                logger.info(
                    f"{ts} action={action} user_id={user_id} "
                    f"currency='{currency_code}' amount={amount} base='{base_currency}' "
                    f"result=ERROR error_type={type(exc).__name__} error_message='{exc}'"
                )
                raise
            else:
                extra = ""
                if verbose and isinstance(result, tuple) and len(result) == 2:
                    extra = f" details='{result[1]}'"
                logger.info(
                    f"{ts} action={action} user_id={user_id} "
                    f"currency='{currency_code}' amount={amount} base='{base_currency}' "
                    f"result=OK{extra}"
                )
                return result

        return wrapper

    return decorator

