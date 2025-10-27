import redis
import json
import time
from config import Config

# Connect to Redis
r = redis.StrictRedis.from_url(Config.REDIS_URL, decode_responses=True)

SESSION_TTL = 600  # 10 minutes
CONTEXT_TTL = 3600
# -------------------------
# 🔹 Session Management
# -------------------------

def create_user_session(user_id,socket_id=None, ip=None):
    """Create or refresh a 10-min session."""
    session_key = f"session:{user_id}"
    session_data = {
        "user_id": user_id,
        "created_at": int(time.time()),
        "last_active": int(time.time()),
        "socket_id": socket_id,
        "ip": ip
    }
    r.setex(session_key, SESSION_TTL, json.dumps(session_data))
    print(f"✅ Session created for user {user_id} (expires in 10 min)")


def get_user_session(user_id):
    """Return session data if active, else None."""
    session_key = f"session:{user_id}"
    data = r.get(session_key)
    return json.loads(data) if data else None


def is_session_active(user_id):
    """Check if session exists and valid."""
    return get_user_session(user_id) is not None


def delete_user_session(user_id):
    """Manually end a session."""
    session_key = f"session:{user_id}"
    r.delete(session_key)
    print(f"🧹 Session expired for user {user_id}")


# -------------------------
# 🔹 Context Management
# -------------------------

def get_context(user_id):
    key = f"context:{user_id}"
    data = r.get(key)
    return json.loads(data) if data else []


def add_message_to_context(user_id, message):
    key = f"context:{user_id}"
    context = get_context(user_id)
    context.append(message)
    r.setex(key, CONTEXT_TTL, json.dumps(context))  
