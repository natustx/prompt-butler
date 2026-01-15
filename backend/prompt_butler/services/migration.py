"""Migration service to convert YAML prompts to markdown format."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from prompt_butler.models import Prompt
from prompt_butler.services.storage import PromptStorage


@dataclass
class MigrationResult:
    """Result of a migration operation."""

    success_count: int = 0
    failure_count: int = 0
    skipped_count: int = 0
    errors: list[str] | None = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class MigrationService:
    """Service to migrate prompts from YAML to markdown format.

    Old format (YAML):
        ~/.prompts/{name}.yaml
        Contents: {name, description, system_prompt, user_prompt, tags}

    New format (Markdown with YAML frontmatter):
        ~/.prompts/{group}/name.md
        Contents: frontmatter + system_prompt + ---user--- + user_prompt
    """

    def __init__(
        self,
        source_dir: str | Path | None = None,
        target_storage: PromptStorage | None = None,
    ):
        if source_dir is None:
            source_dir = os.getenv('PROMPTS_DIR', os.path.expanduser('~/.prompts'))
        self.source_dir = Path(source_dir)
        self.target_storage = target_storage or PromptStorage(prompts_dir=source_dir)

    def find_yaml_prompts(self) -> list[Path]:
        """Find all YAML prompt files in the source directory."""
        if not self.source_dir.exists():
            return []
        return list(self.source_dir.glob('*.yaml')) + list(self.source_dir.glob('*.yml'))

    def read_yaml_prompt(self, file_path: Path) -> Prompt | None:
        """Read a prompt from a YAML file.

        Returns None if the file is invalid or missing required fields.
        """
        try:
            with open(file_path, encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data or not isinstance(data, dict):
                return None

            if 'name' not in data or 'system_prompt' not in data:
                return None

            # Note: group left as empty string if missing/empty in YAML
            # The migrate_prompt method applies default_group parameter
            return Prompt(
                name=data['name'],
                description=data.get('description', ''),
                system_prompt=data['system_prompt'],
                user_prompt=data.get('user_prompt', ''),
                tags=data.get('tags', []),
                group=data.get('group') or '',
            )
        except (yaml.YAMLError, OSError, ValueError):
            return None

    def migrate_prompt(self, yaml_path: Path, default_group: str = 'default') -> tuple[bool, str]:
        """Migrate a single YAML prompt to markdown format.

        Args:
            yaml_path: Path to the YAML file
            default_group: Group to use if prompt has no group set

        Returns:
            Tuple of (success, message)
        """
        prompt = self.read_yaml_prompt(yaml_path)
        if prompt is None:
            return False, f'Failed to read: {yaml_path.name}'

        if not prompt.group:
            prompt = Prompt(
                name=prompt.name,
                description=prompt.description,
                system_prompt=prompt.system_prompt,
                user_prompt=prompt.user_prompt,
                tags=prompt.tags,
                group=default_group,
            )

        if self.target_storage.exists(prompt.name, prompt.group):
            return False, f'Already exists: {prompt.name} in {prompt.group}'

        try:
            self.target_storage.create(prompt)
            return True, f'Migrated: {prompt.name} -> {prompt.group}/{prompt.name}.md'
        except Exception as e:
            return False, f'Failed to create: {prompt.name} - {e}'

    def migrate_all(self, default_group: str = 'default', remove_source: bool = False) -> MigrationResult:
        """Migrate all YAML prompts to markdown format.

        Args:
            default_group: Group to use for prompts without a group
            remove_source: If True, remove YAML files after successful migration

        Returns:
            MigrationResult with counts and any errors
        """
        result = MigrationResult()
        yaml_files = self.find_yaml_prompts()

        if not yaml_files:
            return result

        for yaml_path in yaml_files:
            success, message = self.migrate_prompt(yaml_path, default_group)

            if success:
                result.success_count += 1
                if remove_source:
                    try:
                        yaml_path.unlink()
                    except OSError as e:
                        result.errors.append(f'Failed to remove {yaml_path.name}: {e}')
            elif 'Already exists' in message:
                result.skipped_count += 1
            else:
                result.failure_count += 1
                result.errors.append(message)

        return result
