from flask import Blueprint, request, jsonify
from database import db
from database.models import UserMessage
from redis_client.session_manager import add_message_to_context, get_context
from utils.n8n_client import send_to_n8n
import json

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_id = data.get("user_id")
    query = data.get("query")

    if not user_id or not query:
        return jsonify({"error": "Missing user_id or query"}), 400

    # Save user message
    msg = UserMessage(user_id=user_id, message=query)
    db.session.add(msg)
    db.session.commit()

    # Get conversation context
    context = get_context(user_id)

    # Send to n8n
    result = send_to_n8n(user_id, query, context)

    # Store bot reply as VALID JSON (with double quotes)
    msg.ai_response = json.dumps(result, ensure_ascii=False)
    db.session.commit()

    # Update Redis context
    add_message_to_context(user_id, query)
    if isinstance(result, dict) and "query" in result:
        add_message_to_context(user_id, result["query"])

    return jsonify(result)
