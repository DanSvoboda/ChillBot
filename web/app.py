import flask
from datetime import datetime as dt
from flask import render_template
import json
import os
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv

load_dotenv()

LLM_BASE_URL = os.environ["LLM_BASE_URL"]
LLM_MODEL = os.environ["LLM_MODEL"]
FLASK_HOST = os.environ["FLASK_HOST"]
FLASK_PORT = int(os.environ["FLASK_PORT"])

from web.mcp_client import get_MCP_urls
from web.rag import DocumentDB


client = None
app = flask.Flask(__name__)
vector_db = DocumentDB()

global mcp_servers
mcp_servers = get_MCP_urls()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    global client
    if client is None:
        return flask.jsonify({
            "error": "No API key configured. Open API settings and add your api_key before chatting.",
        }), 403
    request_data = flask.request.json or {}
    messages = request_data.get("messages")
    if not messages:
        return flask.jsonify({"error": "No messages provided"}), 400

    global mcp_servers
    print(f"Asking for Documents {dt.now()}")
    latest_message = messages[-1]
    if not isinstance(latest_message, dict) or not latest_message.get("content"):
        return flask.jsonify({"error": "The latest message must contain content."}), 400

    known_documents = vector_db.get_documents(latest_message["content"])
    messages.append({
        "role": "assistant",
        "content": (
            "Here are the relevant documents from the knowledge base. "
            "Use them as reference material:\n\n"
            + "\n\n".join(known_documents)
        ),
    })
    print(f"Documents received {dt.now()}")
    try:
        stream = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            stream=True,
        )
    except OpenAIError:
        return flask.jsonify({
            "error": "The AI provider could not process the request. Check your API key and try again.",
        }), 502

    def generate():
        try:
            for chunk in stream:
                content = (
                    chunk.choices[0].delta.content
                    if chunk.choices
                    else None
                )
                if content:
                    yield f"data: {json.dumps({'content': content})}\n\n"
            yield "data: [DONE]\n\n"
        except OpenAIError:
            yield (
                "event: error\n"
                "data: "
                + json.dumps({
                    "error": (
                        "The AI provider could not finish the response. "
                        "Check your API key and try again."
                    )
                })
                + "\n\n"
            )

    return flask.Response(
        flask.stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

@app.route("/api/update_client", methods=["POST"])
def update_client():
    data = flask.request.json
    global client
    
    api_key = data.get("api_key") if data else None
    if not api_key:
        return flask.jsonify({"error": "An api_key is required."}), 400

    client = OpenAI(
        base_url=LLM_BASE_URL,
        api_key=api_key,

)
    return flask.jsonify({"status": "client updated"})

@app.route("/api/models", methods=["GET"])
def get_models():
    global client
    if client is None:
        return flask.jsonify({
            "error": "No API key configured. Open API settings and add your api_key before fetching models.",
        }), 403

    try:
        response = client.models.list()
    except OpenAIError:
        return flask.jsonify({
            "error": "The AI provider could not fetch the available models. Check your API key and try again.",
        }), 502

    return flask.jsonify({
        "models": response.model_dump(),
    })

if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT)