import os


class Config:
    # Change these values if your MySQL/XAMPP configuration differs.
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_NAME = os.getenv("DB_NAME", "logiclab")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "Melody123")

    # Set a long random value before deploying beyond your own computer.
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-this-for-any-shared-deployment")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("FLASK_HTTPS", "false").lower() == "true"
