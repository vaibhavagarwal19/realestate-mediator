from datetime import datetime
from database import db

class UserMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), nullable=False)
    message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
