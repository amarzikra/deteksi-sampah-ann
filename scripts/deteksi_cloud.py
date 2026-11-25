import os
import tomllib
from pathlib import Path

from inference_sdk import InferenceHTTPClient

PROJECT_DIR = Path(__file__).resolve().parents[1]
SECRETS_PATH = PROJECT_DIR / ".streamlit" / "secrets.toml"
DEFAULT_MODEL_ID = "waste-classification-awlni-o55f1/3"


def get_roboflow_config():
    api_key = os.environ.get("ROBOFLOW_API_KEY", "")
    model_id = os.environ.get("ROBOFLOW_MODEL_ID", DEFAULT_MODEL_ID)
    if (not api_key or model_id == DEFAULT_MODEL_ID) and SECRETS_PATH.exists():
        with open(SECRETS_PATH, "rb") as file:
            secrets = tomllib.load(file)
        config = secrets.get("roboflow", {})
        api_key = api_key or config.get("api_key", "")
        model_id = config.get("model_id", model_id)
    return api_key, model_id


API_KEY, MODEL_ID = get_roboflow_config()

if not API_KEY:
    raise SystemExit(
        "API key Roboflow belum diatur. Isi .streamlit/secrets.toml (lihat secrets.toml.example) "
        "atau set environment variable ROBOFLOW_API_KEY."
    )

CLIENT = InferenceHTTPClient(
    api_url="https://classify.roboflow.com",
    api_key=API_KEY
)

image_file = PROJECT_DIR / "train" / "Plastics" / "pet-3-_jpg.rf.4dc25cc64a2c790f4f47e6ad4be7fb16.jpg"

result = CLIENT.infer(
    str(image_file),
    model_id=MODEL_ID
)

print("--- Hasil Prediksi AI  ---")
print(result)
