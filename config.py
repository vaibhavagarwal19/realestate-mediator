import os

class Config:
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:@localhost/aqarat"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
    REDIS_URL = "redis://localhost:6379/0"
    N8N_AGENT_URL = "http://localhost:5678/webhook-test/chatbotllm"
