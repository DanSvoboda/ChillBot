import json

from pydantic import ValidationError

from tools.production import ProductionInput, predict_production_rise
from tools.variety import classify_plant_type

# Popisy nastroju ve formatu function calling (chat.completions, parametr tools=)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "predict_production_rise",
            "description": (
                "Predicts whether chilli/pepper production in a country rises vs. last year, "
                "given this year's harvested area and last year's production."
            ),
            "parameters": ProductionInput.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "classify_plant_type",
            "description": "Identifies the chilli variety in a photo and returns the top 3 varieties.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Path to the photo (JPEG or PNG), relative to the project root.",
                    },
                },
                "required": ["image_path"],
            },
        },
    },
]


def run_tool(name: str, arguments: str) -> str:
    """Runs the tool the LLM asked for. Returns the result as a string for a `tool` message."""
    try:
        args = json.loads(arguments or "{}")
        if name == "predict_production_rise":
            result = predict_production_rise(ProductionInput(**args))
        elif name == "classify_plant_type":
            result = classify_plant_type(**args)
        else:
            return f"Error: unknown tool '{name}'."
    except (json.JSONDecodeError, TypeError, ValidationError, OSError, ValueError) as error:
        # chybu vratime LLM, aby mohl opravit argumenty misto padu celeho chatu
        return f"Error while running {name}: {error}"
    return result if isinstance(result, str) else json.dumps(result)
