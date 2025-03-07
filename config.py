import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("APP_SECRET_KEY", os.urandom(24).hex())
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), "database.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUTH0_CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID")
    AUTH0_CLIENT_SECRET = os.environ.get("AUTH0_CLIENT_SECRET")
    AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN")
    PORT = int(os.environ.get("PORT", 5000))
