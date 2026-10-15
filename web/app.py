import flask
from flask import render_template
from web.rag import DocumentDB
from openai import OpenAI
from web.mcp_client import get_MCP_urls



vectorDB = DocumentDB()
client = OpenAI()
app = flask.Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    user_input = flask.request.json.get("user_input")
    if not user_input:
        return flask.jsonify({"error": "Missing user input"}), 400

    documents = vectorDB.get_documents(user_input)
    return flask.jsonify({"documents": documents})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)