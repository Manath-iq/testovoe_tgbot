import os


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise RuntimeError(f"Missing required env var: {name}")
    return value


class Config:
    database_url: str
    telegram_token: str
    gemini_api_key: str
    gemini_model: str

    def __init__(self) -> None:
        self.database_url = get_env("DATABASE_URL")
        self.telegram_token = get_env("TELEGRAM_BOT_TOKEN")
        self.gemini_api_key = get_env("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
