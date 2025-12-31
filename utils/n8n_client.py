import requests
import json
from config import Config


def send_to_n8n(user_id, query, context=None, session_id=None):
    if context is None:
        context = []

    payload = {
        "user_id": str(user_id),     # ensure consistent type
        "user_query": query,
        "context": context,
        "sessionId": session_id      # ✅ REQUIRED
    }

    try:
        res = requests.post(
            Config.N8N_AGENT_URL,
            json=payload,
            timeout=60
        )

        # 🔍 DEBUG (keep during development)
        print("N8N STATUS:", res.status_code)
        print("N8N PAYLOAD SENT:", payload)
        print("N8N RAW RESPONSE:", repr(res.text))

        res.raise_for_status()

        # ❗ Safety: empty response
        if not res.text or not res.text.strip():
            return {
                "error": "n8n returned empty response",
                "payload_sent": payload
            }

        # ❗ Safety: non-JSON response
        try:
            return res.json()
        except json.JSONDecodeError:
            return {
                "error": "n8n returned non-JSON response",
                "raw_response": res.text[:500]
            }

    except requests.exceptions.RequestException as e:
        return {
            "error": "Request to n8n failed",
            "details": str(e)
        }


def process_data(user_id, query, context=None, session_id=None):
    return send_to_n8n(
        user_id=user_id,
        query=query,
        context=context,
        session_id=session_id
    )
