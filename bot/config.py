import os
from dataclasses import dataclass


@dataclass
class Config:
    bot_token: str
    db_path: str = "data/shepot.db"
    report_threshold: int = 5
    max_whisper_age_days: int = 30

    @classmethod
    def from_env(cls) -> "Config":
        token = os.getenv("BOT_TOKEN")
        if not token:
            raise ValueError("BOT_TOKEN environment variable is required")
        return cls(
            bot_token=token,
            db_path=os.getenv("DB_PATH", "data/shepot.db"),
            report_threshold=int(os.getenv("REPORT_THRESHOLD", "5")),
            max_whisper_age_days=int(os.getenv("MAX_WHISPER_AGE_DAYS", "30")),
        )
