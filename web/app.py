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

from tools.registry import TOOLS, run_tool
from web.rag import DocumentDB

# Kolikrat po sobe muze LLM volat nastroje, nez musi odpovedet textem
MAX_TOOL_ROUNDS = 5

client = None
app = flask.Flask(__name__)
vector_db = DocumentDB()


def create_stream(messages, allow_tools=True):
    return client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto" if allow_tools else "none",
        stream=True,
    )


def stream_with_tools(messages, stream):
    """
    Streams the answer text. When the LLM asks for tools, runs them locally,
    adds the results to the conversation and asks the LLM again.
    """
    # o jedno kolo vic: posledni stream je bez nastroju a musi odpovedet textem
    for tool_round in range(MAX_TOOL_ROUNDS + 1):
        content = ""
        tool_calls = {}
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                content += delta.content
                yield delta.content
            # argumenty volani nastroje chodi po kouskach, skladame je podle indexu
            for call_delta in delta.tool_calls or []:
                call = tool_calls.setdefault(call_delta.index, {"id": "", "name": "", "arguments": ""})
                if call_delta.id:
                    call["id"] = call_delta.id
                if call_delta.function and call_delta.function.name:
                    call["name"] += call_delta.function.name
                if call_delta.function and call_delta.function.arguments:
                    call["arguments"] += call_delta.function.arguments

        if not tool_calls:
            return

        messages.append({
            "role": "assistant",
            "content": content or None,
            "tool_calls": [
                {
                    "id": call["id"],
                    "type": "function",
                    "function": {"name": call["name"], "arguments": call["arguments"]},
                }
                for call in tool_calls.values()
            ],
        })
        for call in tool_calls.values():
            print(f"Running tool {call['name']}({call['arguments']}) {dt.now()}")
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": run_tool(call["name"], call["arguments"]),
            })
        stream = create_stream(messages, allow_tools=tool_round + 1 < MAX_TOOL_ROUNDS)

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
        stream = create_stream(messages)
    except OpenAIError:
        return flask.jsonify({
            "error": "The AI provider could not process the request. Check your API key and try again.",
        }), 502

    def generate():
        try:
            for content in stream_with_tools(messages, stream):
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