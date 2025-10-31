from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from database import db
from config import Config
from routes.chat_routes import chat_bp
from routes.socket_manager import socketio

# Import models for migrations
from database import models

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    db.init_app(app)
    Migrate(app, db)
    app.register_blueprint(chat_bp)
    return app

app = create_app()

# Initialize SocketIO after app creation
socketio.init_app(app, cors_allowed_origins="*")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
