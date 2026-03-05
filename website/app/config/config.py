import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / '.env')


def to_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def clean_env(value, default=''):
    if value is None:
        return default

    cleaned = str(value).strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'", '`'}:
        cleaned = cleaned[1:-1].strip()

    return cleaned

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'mysecretkey')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_USER = os.getenv('DB_USER', 'user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_NAME = os.getenv('DB_NAME', 'flask_api_db')
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False