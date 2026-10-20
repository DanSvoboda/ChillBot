import flask
from flask import render_template
from openai import OpenAI, OpenAIError
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
    messages = flask.request.json.get("messages")
    if not messages:
        return flask.jsonify({"error": "No messages provided"}), 400

    global mcp_servers
    try:
        response = client.chat.completions.create(
            model="qwen3.6-35b",
            messages=messages,
        )
    except OpenAIError:
        return flask.jsonify({
            "error": "The AI provider could not process the request. Check your API key and try again.",
        }), 502

    return flask.jsonify({
        "messages": messages,
        "response": response.model_dump(),
    })

@app.route("/api/update_client", methods=["POST"])
def update_client():
    data = flask.request.json
    global client
    
    api_key = data.get("api_key") if data else None
    if not api_key:
        return flask.jsonify({"error": "An api_key is required."}), 400

    client = OpenAI(
        base_url="https://litellm.vse.cz/v1/",
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
    app.run(host="0.0.0.0", port=5000)