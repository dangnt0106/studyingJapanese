#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Configuration management for Anki Integration Tool."""

from pathlib import Path
from typing import Optional, List
import yaml
from pydantic import BaseModel, Field


class AnkiConfig(BaseModel):
    """AnkiConnect configuration."""
    url: str = "http://localhost"
    port: int = 8765
    timeout: int = 10
    test_connection: bool = True

    @property
    def full_url(self) -> str:
        """Get full AnkiConnect API URL."""
        return f"{self.url}:{self.port}"


class PathsConfig(BaseModel):
    """Paths configuration."""
    grammar_csv_dir: str = "../output"
    audio_base_dir: str = "../audio"
    output_dir: str = "./output"
    logs_dir: str = "./logs"

    def get_grammar_csv_path(self, base_path: Path) -> Path:
        """Get absolute path to grammar CSV directory."""
        return self._resolve_path(base_path, self.grammar_csv_dir)

    def get_audio_base_path(self, base_path: Path) -> Path:
        """Get absolute path to audio base directory."""
        return self._resolve_path(base_path, self.audio_base_dir)

    def get_output_path(self, base_path: Path) -> Path:
        """Get absolute path to output directory."""
        return self._resolve_path(base_path, self.output_dir)

    def get_logs_path(self, base_path: Path) -> Path:
        """Get absolute path to logs directory."""
        return self._resolve_path(base_path, self.logs_dir)

    @staticmethod
    def _resolve_path(base: Path, relative: str) -> Path:
        """Resolve relative path from base."""
        path = Path(relative)
        if path.is_absolute():
            return path
        return (base / path).resolve()


class AudioConfig(BaseModel):
    """Audio matching configuration."""
    fuzzy_threshold: int = Field(default=80, ge=0, le=100)
    supported_formats: List[str] = Field(default=["mp3", "wav", "ogg"])
    log_unmatched: bool = True


class DeckConfig(BaseModel):
    """Anki deck configuration."""
    template: str = "Japanese::NguPhap::{lesson_name}"
    name_extraction_pattern: str = r"N(?P<level>\d+)-.*?(?P<lesson>Bai-\d+)"


class CardConfig(BaseModel):
    """Card configuration."""
    note_type: str = "Basic"
    fields: dict = Field(default={"front": "Front", "back": "Back"})
    duplicate_strategy: str = Field(default="skip")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "detailed"
    file_logging: bool = True
    filename: str = "anki_import_{date}.log"


class ImportConfig(BaseModel):
    """Import configuration."""
    batch_size: int = 100
    batch_delay: float = 1.0
    validate_before_import: bool = True


class AppConfig(BaseModel):
    """Main application configuration."""
    anki: AnkiConfig = Field(default_factory=AnkiConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    deck: DeckConfig = Field(default_factory=DeckConfig)
    card: CardConfig = Field(default_factory=CardConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    import_: ImportConfig = Field(default_factory=ImportConfig, alias="import")


def load_config(config_path: Path) -> AppConfig:
    """Load configuration from YAML file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config_dict = yaml.safe_load(f)

    return AppConfig(**config_dict)


def save_config(config: AppConfig, config_path: Path) -> None:
    """Save configuration to YAML file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config.model_dump(by_alias=True), f, default_flow_style=False, allow_unicode=True)


def get_default_config() -> AppConfig:
    """Get default configuration."""
    return AppConfig()
