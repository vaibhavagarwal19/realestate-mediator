from flask_socketio import SocketIO, emit, join_room
from database import db
from flask import request as flask_request
from database.models import UserMessage
from redis_client.session_manager import (
    add_message_to_context, get_context, create_user_session
)
from utils.n8n_client import process_data
import json
import datetime
import traceback

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
        # -----------------------------
        # 1. Parse incoming payload
        # -----------------------------
        if isinstance(data, dict):
            user_id = data.get("user_id")
            query = data.get("message")
            emoji_type = data.get("emoji_type")
            q_id = data.get("q_id")
            q_type = data.get("q_type")
            session_id = data.get("sessionId")
        elif isinstance(data, str):
            query = data.strip()
            session_id = None
        else:
            emit("error", {"error": "Invalid message format"})
            log_event("ERROR", "❌ Invalid message format", str(data))
            return

        # -----------------------------
        # 2. Validate input
        # -----------------------------
        if not query:
            emit("error", {"error": "Missing message text"})
            log_event("ERROR", "❌ Missing message text", str(data))
            return

        if not user_id:
            emit("error", {"error": "Missing user_id"})
            log_event("ERROR", "❌ Missing user_id", str(data))
            return

        log_event("PROCESS", f"📩 Message from user {user_id}: {query}")

        # -----------------------------
        # 3. Ensure room is joined
        # -----------------------------
        try:
            join_room(str(user_id))
        except Exception as e:
            log_event("WARN", f"Could not join room {user_id}: {e}")

        # -----------------------------
        # 4. Create/refresh session (store socket id)
        # -----------------------------
        try:
            socket_id = getattr(flask_request, "sid", None) or None
        except Exception:
            socket_id = None

        # Use create_user_session(user_id, socket_id=...) if your implementation supports socket id
        try:
            create_user_session(user_id, socket_id=socket_id)
        except Exception as e:
            log_event("WARN", f"create_user_session failed: {e}")

        # -----------------------------
        # 5. Update Redis context BEFORE calling n8n
        # -----------------------------
        try:
            # add_message_to_context should trim internally (see suggestions below)
            add_message_to_context(user_id, query)
            context = get_context(user_id) or []
        except Exception as e:
            log_event("WARN", f"Redis context update/read failed: {e}")
            context = []

        log_event("CONTEXT_UPDATED", "🧠 Context after update", context)

        # -----------------------------
        # 6. Save User Message to DB
        # -----------------------------
        msg = UserMessage(user_id=user_id, message=query)
        db.session.add(msg)
        db.session.flush()
        message_id = msg.id
        log_event("DB", f"🆔 New message inserted with ID {message_id}")

        # -----------------------------
        # 7. Call n8n / AI with proper payload
        # -----------------------------
        # process_data should accept (user_id, query, context, session_id, user_query)
        try:
            response = process_data(
                user_id=user_id,
                query=query,
                context=context,
                session_id=session_id
            )
        except Exception as e:
            log_event("ERROR", f"❌ process_data exception: {e}", traceback.format_exc())
            response = {"error": f"process_data failed: {str(e)}"}


        log_event("AI_RESPONSE", "🤖 AI/n8n response received", response)

        # -----------------------------
        # 8. Save AI response SAFELY to DB
        # -----------------------------
        try:
            ai_json = json.dumps(response, ensure_ascii=False)
        except Exception:
            # fallback to str() to avoid crashes
            ai_json = json.dumps({"error": "unable to serialize response", "raw": str(response)}, ensure_ascii=False)

        # Safe truncation: avoid producing invalid JSON if truncating
        if len(ai_json) > 65000:
            ai_json = json.dumps({
                "truncated": True,
                "original_length": len(ai_json),
                "data": ai_json[:64000]
            }, ensure_ascii=False)


        msg.ai_response = ai_json
        db.session.commit()
        log_event("DB", f"💾 Message + AI response saved for user {user_id}")

        # -----------------------------
        # 9. Update context with any follow-up query returned by AI (if present)
        # -----------------------------
        try:
            if isinstance(response, dict) and response.get("query"):
                add_message_to_context(user_id, response["query"])
        except Exception as e:
            log_event("WARN", f"Could not add AI query to context: {e}")

        # -----------------------------
        # 10. Inject q_id into response
        # -----------------------------
        try:
            if isinstance(response, dict):
                response["q_id"] = message_id
            elif isinstance(response, list):
                for item in response:
                    if isinstance(item, dict):
                        item["q_id"] = message_id
        except Exception as e:
            log_event("WARN", f"Failed to inject q_id: {e}")

        # -----------------------------
        # 11. Emit reply
        # -----------------------------
        try:
            emit("reply", {"response": response}, room=str(user_id))
            log_event("REPLY_SENT", f"🚀 Sent reply to user {user_id}", response)
        except Exception as e:
            log_event("ERROR", f"❌ Failed to emit reply: {e}", traceback.format_exc())
            emit("error", {"error": "Failed to deliver reply"}, room=str(user_id))

    except Exception as e:
        db.session.rollback()
        error_trace = traceback.format_exc()
        log_event("ERROR", f"❌ Exception while handling message for user {user_id}: {e}", error_trace)
        emit("error", {"error": str(e)}, room=str(user_id) if user_id else None)