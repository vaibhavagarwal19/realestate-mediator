import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY")
    REDIS_URL = os.getenv("REDIS_URL")
    N8N_AGENT_URL = os.getenv("N8N_AGENT_URL")
