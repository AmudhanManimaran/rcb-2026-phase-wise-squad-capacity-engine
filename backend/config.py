"""Application configuration loaded from environment variables / .env."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv is optional
    load_dotenv = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if load_dotenv:
    load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "eesaala_tracker")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    DB_ADMIN_DB: str = os.getenv("DB_ADMIN_DB", "postgres")

    API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    CORS_ORIGINS = [o.strip() for o in os.getenv(
        "CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000").split(",")]

    RANDOM_SEED: int = int(os.getenv("RANDOM_SEED", "2026"))
    SEASON: int = 2026

    DATABASE_DIR = PROJECT_ROOT / "database"
    DATA_DIR = PROJECT_ROOT / "data"
    FRONTEND_DIR = PROJECT_ROOT / "frontend"

    def dsn(self, admin: bool = False) -> dict:
        return dict(host=self.DB_HOST, port=self.DB_PORT, user=self.DB_USER, password=self.DB_PASSWORD,
                    dbname=self.DB_ADMIN_DB if admin else self.DB_NAME)


settings = Settings()
