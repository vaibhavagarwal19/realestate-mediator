import os

class Config:
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:@localhost/aqarat"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
    REDIS_URL = "redis://localhost:6379/0"
    N8N_AGENT_URL = "https://aqarize.app.n8n.cloud/webhook-test/chatbotllm"
