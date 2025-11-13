from flask import Blueprint, jsonify

intents_bp = Blueprint("intents", __name__)

SAMPLE_INTENTS = [
    "Show properties",
    "Show stores",
    "Show blogs",
]

def get_common_intents():
    return SAMPLE_INTENTS

@intents_bp.route("/intents", methods=["GET"])
def get_intents():
    return jsonify({
        "status": True,
        "intents": get_common_intents()
    })