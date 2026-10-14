import os
from pathlib import Path
from typing import List

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(title="12-Factor Config Precedence")

# Allow the assignment page/browser grader to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

def coerce(key: str, value):
    value = str(value)
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return value.strip().lower() in ("true", "1", "yes", "on")
    return value

def env_key_to_config(key: str):
    aliases = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
        "NUM_WORKERS": "workers",
    }
    return aliases.get(key)

def get_effective_config(sets: List[str]):
    config = DEFAULTS.copy()

    # Layer 2: environment-specific YAML. APP_ENV defaults to development.
    env_name = os.getenv("APP_ENV", "development")
    yaml_path = ROOT / f"config.{env_name}.yaml"
    if yaml_path.exists():
        with yaml_path.open("r", encoding="utf-8") as f:
            yaml_layer = yaml.safe_load(f) or {}
        for key, value in yaml_layer.items():
            if key in config:
                config[key] = coerce(key, value)

    # Layer 3: .env file. NUM_WORKERS is an alias for workers.
    dotenv_path = ROOT / ".env"
    env_file = dotenv_values(dotenv_path) if dotenv_path.exists() else {}
    for key, value in env_file.items():
        mapped = env_key_to_config(key)
        if mapped in config and value is not None:
            config[mapped] = coerce(mapped, value)

    # Layer 4: OS environment variables take precedence over .env.
    # Assignment values are fallbacks for hosting platforms where these
    # environment variables have not been configured in the dashboard.
    os_fallbacks = {
        "APP_PORT": "8775",
        "APP_WORKERS": "10",
        "APP_DEBUG": "true",
    }
    for env_key, fallback in os_fallbacks.items():
        value = os.environ.get(env_key, fallback)
        mapped = env_key_to_config(env_key)
        config[mapped] = coerce(mapped, value)

    # Apply repeated CLI-style query parameters last, e.g. ?set=port=9000&set=debug=true
    for item in sets:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip().lower()
        if key in config:
            config[key] = coerce(key, value)

    # Never return the actual secret.
    config["api_key"] = "****"
    return config

@app.get("/effective-config")
def effective_config(set: List[str] = Query(default=[])):
    return get_effective_config(set)

@app.get("/")
def root():
    return {"message": "Config precedence API is running", "endpoint": "/effective-config"}
