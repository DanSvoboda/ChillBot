import math
import os
import joblib
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from mcp.server import MCPServer
from pydantic import BaseModel, Field

load_dotenv()

MODEL_PATH = Path(os.environ["PRODUCTION_MODEL_PATH"])
MCP_PRODUCTION_URL = os.environ["MCP_PRODUCTION_URL"]
HOST = os.environ["MCP_PRODUCTION_LOCAL_HOST"]
PORT = int(os.environ["MCP_PRODUCTION_LOCAL_PORT"])

model = joblib.load(MODEL_PATH)

mcp = MCPServer()

CATEGORICAL = {
    "area",
    "peppers",
    "climate_flag_standard_deviation",
    "climate_flag_temperature_change",
    "price_flag",
    "flag_prod_prev_year",
}

class ProductionInput(BaseModel):
    # povinne: kde, co, kdy, plocha letos vs. loni a loňská produkce
    area: str = Field(description="Country name as in FAOSTAT, e.g. 'Spain'")
    peppers: str = Field(description="'fresh' or 'dry'")
    year: int
    area_harvested: float = Field(description="Area harvested (planted) this year, ha")
    area_harvested_prev_year: float = Field(description="Area harvested last year, ha")
    production_prev_year: float = Field(description="Production last year, t")
    # volitelne - chybejici hodnoty doplni imputer v pipeline
    yield_prev_year: float | None = None
    price_value: float | None = None
    price_value_prev_year: float | None = None
    climate_value_standard_deviation: float | None = None
    climate_value_temperature_change: float | None = None
    climate_value_standard_deviation_prev_year: float | None = None
    climate_value_temperature_change_prev_year: float | None = None
    production_change_prev_year: float | None = Field(None, description="log(production t-1 / production t-2)")
    yield_change_prev_year: float | None = None
    area_harvested_change_prev_year: float | None = None
    price_value_change_prev_year: float | None = None
    climate_flag_standard_deviation: str | None = None
    climate_flag_temperature_change: str | None = None
    price_flag: str | None = None
    flag_prod_prev_year: str | None = None


@mcp.tool()
def predict_production_rise(input_data: ProductionInput) -> dict:
    """Predicts whether pepper production in a country rises vs. last year, given this year's harvested area."""
    features = input_data.model_dump()
    features["area_harvested_change_this_year"] = (
        math.log(input_data.area_harvested / input_data.area_harvested_prev_year)
        if input_data.area_harvested > 0 and input_data.area_harvested_prev_year > 0
        else None
    )
    change = input_data.production_change_prev_year
    features["production_flat_prev_year"] = None if change is None else float(change == 0)
    features["production_rose_prev_year"] = None if change is None else float(change > 0)
    features["production_abs_change_prev_year"] = None if change is None else abs(change)

    # None -> NaN (float) u ciselnych, object u kategorickych, jinak imputer/encoder spadne
    X = pd.DataFrame([features])
    X = X.astype({c: object if c in CATEGORICAL else float for c in X.columns})
    proba = float(model.predict_proba(X)[0, 1])
    return {"production_rise": int(proba >= 0.5), "probability": round(proba, 3)}


def get_MCP():
    """
    Returns the URL for the MCP server.
    """
    return {
            "type": "mcp",
            "server_label": "production_classifier",
            "description": "Predicts whether chilli/pepper production in a country rises vs. last year, given this year's harvested area and last year's production.",
            "server_url": MCP_PRODUCTION_URL,
            "require_approval": "never", 
        }
    
if __name__ == "__main__":
    print("Starting the Production Classifier MCP Server...")
    mcp.run(
        transport="streamable-http",
        host=HOST,
        port=PORT
        )