import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL")
    ADMIN_ID = os.getenv("ADMIN_ID")
    PROXY_URL = os.getenv("PROXY_URL") 

settings = Settings()