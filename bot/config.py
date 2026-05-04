import os
from dataclasses import dataclass


@dataclass
class Config:
    bot_token: str
    db_path: str = "data/krugovorot.db"
    report_threshold: int = 5  # auto-ban after N reports
    dialog_timeout_hours: int = 24  # inactivity timeout for dialog mode

    @classmethod
    def from_env(cls) -> "Config":
        token = os.getenv("BOT_TOKEN")
        if not token:
            raise ValueError("BOT_TOKEN environment variable is required")
        return cls(
            bot_token=token,
            db_path=os.getenv("DB_PATH", "data/krugovorot.db"),
            report_threshold=int(os.getenv("REPORT_THRESHOLD", "5")),
            dialog_timeout_hours=int(os.getenv("DIALOG_TIMEOUT_HOURS", "24")),
        )
