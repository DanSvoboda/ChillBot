from mcp.server import MCPServer

mcp = MCPServer()

HOST = "0.0.0.0"
PORT = 5001

@mcp.tool()
def classify_plant_type(image: bytes) -> str:
    """
    Classifies the type of chilli plant based on the provided image.

    Args:
        image (bytes): The image of the chilli plant in bytes format.

    Returns:
        str: The type of chilli plant.
    """
    # Placeholder for actual classification logic
    # In a real implementation, you would load a trained model and use it to classify the image.
    return "Chilli Plant Type A"  # Example return value


def get_MCP_url():
    """
    Returns the URL for the MCP server.
    """
    return f"http://{HOST}:{PORT}"

if __name__ == "__main__":
    print("Starting the Chilli Plant Classifier MCP Server...")
    mcp.run(
        transport="streamable-http",
        host=HOST,
        port=PORT
        )
