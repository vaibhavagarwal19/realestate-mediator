from flask_socketio import SocketIO, emit, join_room
from database import db
from database.models import UserMessage
from redis_client.session_manager import (
    add_message_to_context, get_context,
    create_user_session
)
from utils.n8n_client import process_data

socketio = SocketIO()

@socketio.on("connect")
def handle_connect():
    print("⚡ Client connected!")
    emit("connected", {"message": "Socket connected successfully!"})

@socketio.on("join")
def handle_join(data):
    user_id = data.get("user_id")
    if not user_id:
        emit("error", {"error": "user_id required"})
        return
    join_room(str(user_id))
    emit("joined", {"message": f"Joined room {user_id}"}, room=str(user_id))
    print(f"👥 User {user_id} joined room")

@socketio.on("message")
def handle_message(data):
    try:
        user_id = data.get("user_id")
        query = data.get("message")

        if not user_id or not query:
            emit("error", {"error": "Missing user_id or message"})
            return

        # Always refresh or create session
        create_user_session(user_id)

        print(f"📩 Message from user {user_id}: {query}")

        # Save user message
        msg = UserMessage(user_id=user_id, message=query)
        db.session.add(msg)
        db.session.commit()

        # Retrieve user context
        context = get_context(user_id)

        # Process with AI/n8n
        response = process_data(user_id, query, context)

        # Store bot response
        msg.ai_response = str(response)
        db.session.commit()

        # Update Redis context
        add_message_to_context(user_id, query)
        if isinstance(response, dict) and "query" in response:
            add_message_to_context(user_id, response["query"])

        # Emit back to the same user's room
        emit("reply", {"response": response}, room=str(user_id))
        print(f"🤖 Sent reply to user {user_id}")

    except Exception as e:
        print(f"❌ Error handling message: {e}")
        emit("error", {"error": str(e)}, room=str(user_id))
