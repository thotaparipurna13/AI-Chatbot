import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from groq import Groq

from database import (
    add_message,
    create_conversation,
    delete_conversation,
    get_conversation_messages,
    get_conversations,
    init_db,
)

load_dotenv()

app = Flask(__name__)
init_db()


def get_groq_client():
    """Create a Groq client using the environment API key."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Set it in your .env file.")
    return Groq(api_key=api_key)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Please enter a message."}), 400

    conversation_id = data.get("conversation_id")
    if conversation_id:
        try:
            conversation_id = int(conversation_id)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid conversation_id."}), 400
    else:
        conversation_id = create_conversation(user_message[:40])

    add_message(conversation_id, "user", user_message)

    conversation_history = get_conversation_messages(conversation_id)
    messages_for_model = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant for the KHub chatbot. Keep replies concise, professional, and useful.",
        }
    ]

    for item in conversation_history:
        messages_for_model.append(
            {
                "role": item["role"],
                "content": item["content"],
            }
        )

    try:
        client = get_groq_client()
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_for_model,
        )
        reply = completion.choices[0].message.content or "I could not generate a reply."
    except Exception as exc:  # pragma: no cover - runtime protection
        return jsonify({"error": f"Unable to generate a response: {str(exc)}"}), 500

    add_message(conversation_id, "assistant", reply)

    return jsonify({
        "response": reply,
        "conversation_id": conversation_id,
    })


@app.route("/conversations", methods=["GET"])
def list_conversations():
    return jsonify({"conversations": get_conversations()})


@app.route("/conversations/new", methods=["POST"])
def new_conversation():
    conversation_id = create_conversation("New Conversation")
    return jsonify({"conversation_id": conversation_id})


@app.route("/conversations/<int:conversation_id>", methods=["GET"])
def conversation_detail(conversation_id):
    return jsonify({
        "conversation_id": conversation_id,
        "messages": get_conversation_messages(conversation_id),
    })


@app.route("/conversations/<int:conversation_id>", methods=["DELETE"])
def conversation_delete(conversation_id):
    deleted = delete_conversation(conversation_id)
    return jsonify({"deleted": deleted})


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)