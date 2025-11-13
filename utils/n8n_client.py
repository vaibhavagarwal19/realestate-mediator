import requests
from config import Config

def send_to_n8n(user_id, query, context=None):
    """
    Sends user input to the n8n AI agent webhook.

    Parameters:
        user_id (int): ID of the user
        query (str): The user's message
        context (list, optional): Optional past messages for context

    Returns:
        dict: JSON response from n8n or an error message
    """
    if context is None:
        context = []

    payload = {
        "user_id": user_id,
        "query": query,
        "context": context
    }

    try:
        res = requests.post(Config.N8N_AGENT_URL, json=payload, timeout=60)
        # Raise an error if the response is not JSON
        print(res)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Request error: {str(e)}"}
    except ValueError:
        return {"error": "Invalid JSON response from n8n"}


def process_data(user_id, query, context=None):
    # //store
    return send_to_n8n(user_id, query, context)


# def myn8nreceiver():
