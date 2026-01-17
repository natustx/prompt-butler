import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

DEFAULT_PROMPTS_DIR = Path.home() / '.prompts'
DEFAULT_CONFIG_DIR = Path.home() / '.config' / 'prompt-butler'
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / 'config.yaml'


@dataclass
class Config:
    """Configuration for Prompt Butler.

    Attributes:
        prompts_dir: Directory where prompts are stored
        editor: Editor to use for editing prompts (defaults to $EDITOR)
        default_group: Default group for new prompts
    """

    prompts_dir: Path = field(default_factory=lambda: DEFAULT_PROMPTS_DIR)
    editor: str = field(default_factory=lambda: os.getenv('EDITOR', 'vim'))
    default_group: str = ''

    def __post_init__(self):
        if isinstance(self.prompts_dir, str):
            self.prompts_dir = Path(self.prompts_dir).expanduser()

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'Config':
        """Load configuration from YAML file.

        Falls back to defaults if file doesn't exist or is invalid.
        """
        path = config_path or DEFAULT_CONFIG_FILE

        if not path.exists():
            return cls()

        try:
            with open(path, encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        except (OSError, yaml.YAMLError):
            return cls()

        prompts_dir = data.get('prompts_dir')
        if prompts_dir:
            prompts_dir = Path(prompts_dir).expanduser()
        else:
            prompts_dir = DEFAULT_PROMPTS_DIR

        editor = data.get('editor') or os.getenv('EDITOR', 'vim')

        default_group = data.get('default_group', '')

        return cls(
            prompts_dir=prompts_dir,
            editor=editor,
            default_group=default_group,
        )

    def save(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to YAML file."""
        path = config_path or DEFAULT_CONFIG_FILE

        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'prompts_dir': str(self.prompts_dir),
            'editor': self.editor,
            'default_group': self.default_group,
        }

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def update(self, **kwargs) -> 'Config':
        """Return a new Config with updated values."""
        current = {
            'prompts_dir': self.prompts_dir,
            'editor': self.editor,
            'default_group': self.default_group,
        }
        current.update(kwargs)
        return Config(**current)


_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration, loading it if necessary."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def reload_config() -> Config:
    """Force reload the configuration from disk."""
    global _config
    _config = Config.load()
    return _config
