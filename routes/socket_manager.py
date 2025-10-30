from flask_socketio import SocketIO, emit, join_room
from database import db
from database.models import UserMessage
from redis_client.session_manager import (
    add_message_to_context, get_context, create_user_session
)
from utils.n8n_client import process_data
import json
import datetime

socketio = SocketIO(cors_allowed_origins="*")

def log_event(event, message="", data=None):
    """Pretty logger for SocketIO events."""
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "=" * 80)
    print(f"🕒 [{time}]  EVENT: {event}")
    if message:
        print(f"🔹 {message}")
    if data is not None:
        try:
            print("📦 Data:", json.dumps(data, indent=2, ensure_ascii=False))
        except Exception:
            print(f"📦 Data: {data}")
    print("=" * 80 + "\n")

@socketio.on("connect")
def handle_connect():
    log_event("CONNECT", "⚡ Client connected!")
    emit("connected", {"message": "Socket connected successfully!"})

@socketio.on("disconnect")
def handle_disconnect():
    log_event("DISCONNECT", "🔌 Client disconnected")

@socketio.on("join")
def handle_join(data):
    log_event("JOIN", "Incoming join request", data)
    try:
        if not isinstance(data, dict):
            emit("error", {"error": "Invalid join payload"})
            return
        
        user_id = data.get("user_id")
        if not user_id:
            emit("error", {"error": "user_id required"})
            return

        join_room(str(user_id))
        emit("joined", {"message": f"Joined room {user_id}"}, room=str(user_id))
        log_event("JOINED", f"👥 User {user_id} joined room successfully")

    except Exception as e:
        log_event("JOIN_ERROR", f"❌ Error in join: {e}")
        emit("error", {"error": str(e)})

@socketio.on("message")
def handle_message(data):
    user_id = None
    log_event("MESSAGE", "📨 Raw incoming message", data)

    try:
        # --- Parse Data ---
        if isinstance(data, dict):
            user_id = data.get("user_id")
            query = data.get("message")
        elif isinstance(data, str):
            query = data.strip()
        else:
            emit("error", {"error": "Invalid message format"})
            return

        # --- Validate ---
        if not query:
            emit("error", {"error": "Missing message text"})
            return
        if not user_id:
            emit("error", {"error": "Missing user_id"})
            return

        log_event("PROCESS", f"📩 Message from user {user_id}: {query}")

        # --- Create session ---
        create_user_session(user_id)
        log_event("SESSION", f"✅ Session created/refreshed for user {user_id}")

        # --- Save message ---
        msg = UserMessage(user_id=user_id, message=query)
        db.session.add(msg)
        db.session.flush()

        # --- Get context ---
        context = get_context(user_id)
        log_event("CONTEXT", "🧠 Retrieved user context", context)

        # --- Process AI response ---
        response = process_data(user_id, query, context)
        log_event("AI_RESPONSE", "🤖 n8n/AI response received", response)

        msg.ai_response = str(response)[:65000]
        db.session.commit()
        log_event("DB", f"💾 Message saved for user {user_id}")

        # --- Update Redis context ---
        add_message_to_context(user_id, query)
        if isinstance(response, dict) and "query" in response:
            add_message_to_context(user_id, response["query"])

        # --- Emit Reply ---
        emit("reply", {"response": response}, room=str(user_id))
        log_event("REPLY_SENT", f"🚀 Sent reply to user {user_id}", response)

    except Exception as e:
        db.session.rollback()
        log_event("ERROR", f"❌ Error handling message: {e}")
        emit("error", {"error": str(e)}, room=str(user_id) if user_id else None)
