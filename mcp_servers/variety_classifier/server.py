import base64
import io
from mcp.server import MCPServer
from PIL import Image
from mcp_servers.variety_classifier.model import variety_model

mcp = MCPServer()

HOST = "localhost"
PORT = 5001

_model = None

def get_model():
    # Load lazily so importing this file (e.g. for get_MCP_url) doesn't load ResNet
    global _model
    if _model is None:
        _model = variety_model(load_data=False)
    return _model

@mcp.tool()
def classify_plant_type(image_base64: str) -> str:
    """
    Identifies the chilli variety in a photo.

    Args:
        image_base64: The photo (JPEG or PNG) encoded as a base64 string.

    Returns:
        The top 3 most likely chilli varieties with their probabilities.
    """
    image_bytes = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    results = get_model().predict(image)

    lines = [f"- {name}: {prob:.1%}" for name, prob in results]
    return "Most likely chilli varieties:\n" + "\n".join(lines)

def get_MCP():
    """
    Returns the URL for the MCP server.
    """
    return {
            "type": "mcp",
            "server_label": "variety_classifier",
            "description": "Classifies the variety of chilli plants from images.",
            "server_url": f"http://{HOST}:{PORT}/mcp",
            "require_approval": "never", 
        }

if __name__ == "__main__":
    print("Starting the Chilli Plant Classifier MCP Server...")
    mcp.run(
        transport="streamable-http",
        host=HOST,
        port=PORT
        )
