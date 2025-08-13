import os
import re
from pathlib import Path
from typing import Optional

import yaml

from models import Prompt


class StorageService:
    def __init__(self):
        self.prompts_dir = Path(os.getenv('PROMPTS_DIR', os.path.expanduser('~/.prompts')))
        self.ensure_prompts_dir()

    def ensure_prompts_dir(self) -> None:
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize_filename(name: str) -> str:
        filename = re.sub(r'[^\w\s-]', '_', name.lower())
        filename = re.sub(r'[-\s]+', '_', filename)
        return filename.strip('_')

    def get_prompt_path(self, name: str) -> Path:
        sanitized_name = self.sanitize_filename(name)
        return self.prompts_dir / f'{sanitized_name}.yaml'

    def list_prompts(self) -> list[str]:
        try:
            yaml_files = list(self.prompts_dir.glob('*.yaml'))
            prompt_names = []

            for file_path in yaml_files:
                try:
                    with open(file_path, encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        if data and isinstance(data, dict) and 'name' in data:
                            prompt_names.append(data['name'])
                except (OSError, yaml.YAMLError):
                    continue

            return sorted(prompt_names)
        except Exception as e:
            raise StorageError(f'Failed to list prompts: {str(e)}') from e

    def get_prompt(self, name: str) -> Optional[Prompt]:
        file_path = self.get_prompt_path(name)

        if not file_path.exists():
            return None

        try:
            with open(file_path, encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data:
                    return Prompt(**data)
                return None
        except yaml.YAMLError as e:
            raise InvalidPromptDataError(f'Invalid YAML in prompt file: {str(e)}') from e
        except Exception as e:
            raise StorageError(f'Failed to read prompt: {str(e)}') from e

    def save_prompt(self, prompt: Prompt) -> None:
        file_path = self.get_prompt_path(prompt.name)

        try:
            prompt_dict = prompt.model_dump()

            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(prompt_dict, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        except OSError as e:
            if 'No space left on device' in str(e):
                raise StorageError('Insufficient disk space to save prompt') from e
            elif 'Permission denied' in str(e):
                raise StorageError('Permission denied to save prompt') from e
            else:
                raise StorageError(f'Failed to save prompt: {str(e)}') from e
        except Exception as e:
            raise StorageError(f'Unexpected error saving prompt: {str(e)}') from e

    def delete_prompt(self, name: str) -> bool:
        file_path = self.get_prompt_path(name)

        if not file_path.exists():
            return False

        try:
            file_path.unlink()
            return True
        except PermissionError as e:
            raise StorageError('Permission denied to delete prompt') from e
        except Exception as e:
            raise StorageError(f'Failed to delete prompt: {str(e)}') from e

    def prompt_exists(self, name: str) -> bool:
        file_path = self.get_prompt_path(name)
        return file_path.exists()


class StorageError(Exception):
    pass


class PromptNotFoundError(Exception):
    pass


class InvalidPromptDataError(Exception):
    pass


storage_service = StorageService()
