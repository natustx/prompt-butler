"""Migration service for converting YAML prompts to markdown format."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import yaml

from prompt_butler.models import Prompt
from prompt_butler.services.storage import PromptExistsError, PromptStorage, StorageError


@dataclass
class MigrationResult:
    """Result of a migration operation."""

    success_count: int = 0
    failure_count: int = 0
    skipped_count: int = 0
    errors: list[tuple[str, str]] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        return self.success_count + self.failure_count + self.skipped_count


def migrate_prompts(
    source_dir: Path,
    target_storage: PromptStorage,
    on_progress: Optional[Callable[[str, str], None]] = None,
    skip_existing: bool = True,
) -> MigrationResult:
    """Migrate YAML prompts to markdown format.

    Args:
        source_dir: Directory containing old YAML prompt files
        target_storage: PromptStorage instance to write new format
        on_progress: Optional callback(action, message) for progress updates
        skip_existing: If True, skip prompts that already exist in target

    Returns:
        MigrationResult with counts and any errors
    """
    result = MigrationResult()

    def report(action: str, message: str) -> None:
        if on_progress:
            on_progress(action, message)

    # Find all YAML files in source directory
    yaml_files = list(source_dir.glob('*.yaml'))

    if not yaml_files:
        report('info', f'No YAML files found in {source_dir}')
        return result

    report('start', f'Found {len(yaml_files)} YAML files to migrate')

    for yaml_file in yaml_files:
        try:
            # Read the old YAML format
            prompt = _read_yaml_prompt(yaml_file)
            if prompt is None:
                report('skip', f'{yaml_file.name}: Invalid or empty file')
                result.skipped_count += 1
                continue

            # Try to create in new format
            try:
                target_storage.create(prompt)
                report('success', f'{prompt.name}: Migrated successfully')
                result.success_count += 1
            except PromptExistsError:
                if skip_existing:
                    report('skip', f'{prompt.name}: Already exists in target')
                    result.skipped_count += 1
                else:
                    # Overwrite by updating
                    target_storage.update(prompt.name, prompt, prompt.group)
                    report('success', f'{prompt.name}: Updated existing')
                    result.success_count += 1

        except (OSError, yaml.YAMLError, StorageError) as e:
            error_msg = str(e)
            report('error', f'{yaml_file.name}: {error_msg}')
            result.errors.append((yaml_file.name, error_msg))
            result.failure_count += 1

    report(
        'done',
        (
            'Migration complete: '
            f'{result.success_count} succeeded, '
            f'{result.failure_count} failed, '
            f'{result.skipped_count} skipped'
        ),
    )

    return result


def _read_yaml_prompt(file_path: Path) -> Optional[Prompt]:
    """Read a prompt from old YAML format.

    Old format:
    ```yaml
    name: code-review
    description: Reviews code
    system_prompt: You are helpful
    user_prompt: Please review...
    tags:
      - coding
    group: coding
    ```
    """
    with open(file_path, encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not data or not isinstance(data, dict):
        return None

    # Name is required
    if 'name' not in data:
        return None

    # System prompt is required
    if 'system_prompt' not in data:
        return None

    return Prompt(
        name=data['name'],
        description=data.get('description', ''),
        system_prompt=data['system_prompt'],
        user_prompt=data.get('user_prompt', ''),
        tags=data.get('tags', []),
        group=data.get('group', ''),
    )


def print_migration_summary(result: MigrationResult) -> None:
    """Print a formatted summary of migration results."""
    print('\n=== Migration Summary ===')
    print(f'  Succeeded: {result.success_count}')
    print(f'  Skipped:   {result.skipped_count}')
    print(f'  Failed:    {result.failure_count}')
    print(f'  Total:     {result.total_processed}')

    if result.errors:
        print('\nErrors:')
        for filename, error in result.errors:
            print(f'  - {filename}: {error}')
