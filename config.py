import os

class Config:
    SECRET_KEY = 'your-secret-key-123'  # Для сессий и Flask-Login
    SQLALCHEMY_DATABASE_URI = 'sqlite:///hr.db'  # Простая SQLite база
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    