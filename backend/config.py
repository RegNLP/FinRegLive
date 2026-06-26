# Step 02 - Configuration
#
# Role:
#   Load project settings from a YAML config file.
#
# Why this exists:
#   Other backend files should not hardcode database paths, search hosts, model
#   names, or environment names. They should read those values from one config
#   layer.
#
# Input:
#   configs/local.yaml by default, or another path from FINREG_CONFIG_PATH.
#
# Output:
#   A validated AppSettings object used by the backend.

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel


class DatabaseSettings(BaseModel):
    type: str
    sqlite_path: str


class SearchSettings(BaseModel):
    type: str
    host: str
    index_name: str


class ProcessingSettings(BaseModel):
    chunk_size_words: int
    chunk_overlap_words: int


class LLMSettings(BaseModel):
    provider: str
    model: str


class AppSettings(BaseModel):
    environment: str
    database: DatabaseSettings
    search: SearchSettings
    processing: ProcessingSettings
    llm: LLMSettings


@lru_cache
def get_settings() -> AppSettings:
    config_path = Path(os.getenv("FINREG_CONFIG_PATH", "configs/local.yaml"))
    config_data = yaml.safe_load(config_path.read_text())
    return AppSettings(**config_data)
