"""Configuration service for Prompt Butler.

Config file location: ~/.config/prompt-butler/config.yaml
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Application configuration."""

    prompts_dir: str = Field(default='~/.prompts', description='Directory for storing prompts')
    default_group: str = Field(default='', description='Default group for new prompts (empty for ungrouped)')
    editor: str = Field(default='', description='Preferred editor (overrides $EDITOR)')

    def get_prompts_dir(self) -> Path:
        """Get expanded prompts directory path."""
        return Path(os.path.expanduser(self.prompts_dir))


DEFAULT_CONFIG = Config()

CONFIG_DIR = Path(os.path.expanduser('~/.config/prompt-butler'))
CONFIG_FILE = CONFIG_DIR / 'config.yaml'


class ConfigService:
    """Service for managing application configuration."""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or CONFIG_FILE
        self._config: Config | None = None

    def _ensure_config_dir(self) -> None:
        """Ensure config directory exists."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Config:
        """Load configuration from file, creating defaults if needed."""
        if self._config is not None:
            return self._config

        if not self.config_path.exists():
            self._config = DEFAULT_CONFIG
            return self._config

        try:
            with open(self.config_path, encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            self._config = Config(**data)
        except Exception:
            self._config = DEFAULT_CONFIG

        return self._config

    def save(self, config: Config | None = None) -> None:
        """Save configuration to file."""
        self._ensure_config_dir()
        config = config or self._config or DEFAULT_CONFIG
        self._config = config

        data = config.model_dump()
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get(self, key: str) -> Any:
        """Get a configuration value."""
        config = self.load()
        return getattr(config, key, None)

    def set(self, key: str, value: Any) -> bool:
        """Set a configuration value."""
        config = self.load()
        if not hasattr(config, key):
            return False

        data = config.model_dump()
        data[key] = value
        self._config = Config(**data)
        self.save()
        return True

    def as_dict(self) -> dict[str, Any]:
        """Get configuration as a dictionary."""
        return self.load().model_dump()

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._config = DEFAULT_CONFIG
        self.save()

    def get_editor(self) -> str:
        """Get the editor command, respecting config and $EDITOR."""
        config = self.load()
        if config.editor:
            return config.editor
        return os.environ.get('EDITOR', os.environ.get('VISUAL', 'vim'))

    @property
    def config_file_path(self) -> Path:
        """Get the config file path."""
        return self.config_path


config_service = ConfigService()
