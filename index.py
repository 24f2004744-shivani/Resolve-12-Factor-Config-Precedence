
import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path(__file__).parent

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def convert(key, value):
    if key in ("port", "workers"):
        return int(value)

    if key == "debug":
        return str(value).strip().lower() in (
            "true", "1", "yes", "on"
        )

    return str(value)


def effective_config(overrides):
    config = DEFAULTS.copy()

    # 1. Environment-specific YAML
    env_name = os.getenv("APP_ENV", "development")
    yaml_file = ROOT / f"config.{env_name}.yaml"

    if yaml_file.exists():
        with open(yaml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        for key, value in data.items():
            if key in config:
                config[key] = convert(key, value)

    # 2. .env file
    env_file = dotenv_values(ROOT / ".env")

    aliases = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "NUM_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for key, value in env_file.items():
        target = aliases.get(key)
        if target and value is not None:
            config[target] = convert(target, value)

    # 3. Operating-system environment variables
    for key, target in aliases.items():
        value = os.environ.get(key)
        if value is not None:
            config[target] = convert(target, value)

    # 4. Query-string overrides, in supplied order
    for item in overrides:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        key = key.strip().lower()

        if key in config:
            config[key] = convert(key, value)

    # Never expose the actual API key
    config["api_key"] = "****"

    return config


@app.get("/effective-config")
def get_config(set: list[str] = Query(default=[])):
    return effective_config(set)


@app.get("/")
def health():
    return {"ok": True, "endpoint": "/effective-config"}
