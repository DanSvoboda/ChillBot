import flask
from flask import render_template
from openai import AzureOpenAI
from web.mcp_client import get_MCP_urls


global client
client = AzureOpenAI()
app = flask.Flask(__name__)

mcp_servers = get_MCP_urls()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    messages = flask.request.json.get("messages")
    if not messages:
        return flask.jsonify({"error": "No messages provided"}), 400
    
    response = client.chat.completions.create(
        model="gpt-5",
        messages=messages,
        tools=mcp_servers,
    )
    
    return flask.jsonify({"messages": messages, "response": response})

@app.route("/api/update_client", methods=["POST"])
def update_client():
    data = flask.request.json
    global client
    
    client = AzureOpenAI(
    api_key=data.get("api_key"),
    azure_endpoint="",
    api_version="2025-01-01",  # use the version your resource supports
)
    return flask.jsonify({"status": "client updated"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)