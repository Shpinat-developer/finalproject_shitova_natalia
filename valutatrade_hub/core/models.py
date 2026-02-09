from datetime import datetime
import hashlib


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

