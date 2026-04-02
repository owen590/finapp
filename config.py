import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'finance.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # URL prefix for /finapp path
    SCRIPT_NAME = os.environ.get('SCRIPT_NAME', '/finapp')
    SESSION_COOKIE_PATH = '/'
    APPLICATION_ROOT = '/finapp'
    PREFERRED_URL_SCHEME = None  # let Flask infer from environ
