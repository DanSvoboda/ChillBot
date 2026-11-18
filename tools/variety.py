from pathlib import Path

from PIL import Image

from tools.variety_model import variety_model

_model = None

def get_model():
    # Load lazily so importing this file doesn't load ResNet
    global _model
    if _model is None:
        _model = variety_model(load_data=False)
    return _model

def classify_plant_type(image_path: str) -> str:
    """
    Identifies the chilli variety in a photo.

    Args:
        image_path: Path to the photo (JPEG or PNG), relative to the project root.

    Returns:
        The top 3 most likely chilli varieties with their probabilities.
    """
    image = Image.open(Path(image_path)).convert("RGB")

    results = get_model().predict(image)

    lines = [f"- {name}: {prob:.1%}" for name, prob in results]
    return "Most likely chilli varieties:\n" + "\n".join(lines)
