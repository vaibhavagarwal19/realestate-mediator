from flask import Blueprint, jsonify

intents_bp = Blueprint("intents", __name__)

SAMPLE_INTENTS = [
    "Search for a Property",
    "Show RE developers",
    "Show home Service",
]

def get_common_intents():
    return SAMPLE_INTENTS

@intents_bp.route("/intents", methods=["GET"])
def get_intents():
    return jsonify({
        "status": True,
        "intents": get_common_intents()
    })
