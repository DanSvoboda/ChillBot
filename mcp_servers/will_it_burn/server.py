from mcp.server import MCPServer


mcp = MCPServer()


@mcp.tool()
def predict_burn_intensity(scoville_heat_units: float, reference_heat_units: float) -> str:
    """
    Predicts how intense the burn may feel compared with a reference heat level.

    Args:
        scoville_heat_units: Heat level of the chilli being evaluated.
        reference_heat_units: Heat level of a pepper or meal used for comparison.

    Returns:
        A simple relative burn prediction.
    """
    if scoville_heat_units < 0 or reference_heat_units <= 0:
        raise ValueError("Heat values must be non-negative, and the reference must be above zero.")

    ratio = scoville_heat_units / reference_heat_units

    if ratio < 0.5:
        feeling = "mild"
    elif ratio < 1:
        feeling = "noticeable"
    elif ratio < 2:
        feeling = "strong"
    else:
        feeling = "very intense"

    return f"Predicted burn: {feeling} ({ratio:.1f}x the reference heat)."


if __name__ == "__main__":
    print("Starting the Will It Burn MCP Server...")
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=5001,
    )
