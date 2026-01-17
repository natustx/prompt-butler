"""Integration tests for MigrationService.

Tests use real filesystem operations with temporary directories.
"""

import pytest
import yaml

from prompt_butler.services.migration import MigrationResult, MigrationService
from prompt_butler.services.storage import PromptStorage


@pytest.fixture
def source_dir(tmp_path):
    """Create a source directory with YAML prompts."""
    return tmp_path / 'source'


@pytest.fixture
def target_dir(tmp_path):
    """Create a target directory for migrated prompts."""
    return tmp_path / 'target'


@pytest.fixture
def migration_service(source_dir, target_dir):
    """Create a MigrationService with separate source and target directories."""
    source_dir.mkdir(parents=True, exist_ok=True)
    target_storage = PromptStorage(prompts_dir=target_dir)
    return MigrationService(source_dir=source_dir, target_storage=target_storage)


def create_yaml_prompt(directory, name, **kwargs):
    """Helper to create a YAML prompt file."""
    directory.mkdir(parents=True, exist_ok=True)
    data = {
        'name': name,
        'system_prompt': kwargs.get('system_prompt', f'System prompt for {name}'),
        'description': kwargs.get('description', ''),
        'user_prompt': kwargs.get('user_prompt', ''),
        'tags': kwargs.get('tags', []),
        'group': kwargs.get('group', ''),
    }
    file_path = directory / f'{name}.yaml'
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)
    return file_path


class TestMigrationServiceFindYamlPrompts:
    """Tests for finding YAML prompt files."""

    def test_finds_yaml_files(self, migration_service, source_dir):
        create_yaml_prompt(source_dir, 'prompt1')
        create_yaml_prompt(source_dir, 'prompt2')

        files = migration_service.find_yaml_prompts()

        assert len(files) == 2
        names = [f.name for f in files]
        assert 'prompt1.yaml' in names
        assert 'prompt2.yaml' in names

    def test_finds_yml_extension(self, source_dir, target_dir):
        source_dir.mkdir(parents=True, exist_ok=True)
        yml_file = source_dir / 'test.yml'
        yml_file.write_text('name: test\nsystem_prompt: content')

        target_storage = PromptStorage(prompts_dir=target_dir)
        service = MigrationService(source_dir=source_dir, target_storage=target_storage)
        files = service.find_yaml_prompts()

        assert len(files) == 1
        assert files[0].name == 'test.yml'

    def test_returns_empty_for_nonexistent_dir(self, tmp_path):
        service = MigrationService(source_dir=tmp_path / 'nonexistent')
        files = service.find_yaml_prompts()
        assert files == []

    def test_ignores_non_yaml_files(self, migration_service, source_dir):
        create_yaml_prompt(source_dir, 'valid')
        (source_dir / 'readme.md').write_text('# README')
        (source_dir / 'config.json').write_text('{}')

        files = migration_service.find_yaml_prompts()

        assert len(files) == 1
        assert files[0].name == 'valid.yaml'


class TestMigrationServiceReadYamlPrompt:
    """Tests for reading YAML prompt files."""

    def test_reads_complete_prompt(self, migration_service, source_dir):
        file_path = create_yaml_prompt(
            source_dir,
            'test-prompt',
            description='Test description',
            system_prompt='System content',
            user_prompt='User content',
            tags=['tag1', 'tag2'],
            group='my-group',
        )

        prompt = migration_service.read_yaml_prompt(file_path)

        assert prompt is not None
        assert prompt.name == 'test-prompt'
        assert prompt.description == 'Test description'
        assert prompt.system_prompt == 'System content'
        assert prompt.user_prompt == 'User content'
        assert prompt.tags == ['tag1', 'tag2']
        assert prompt.group == 'my-group'

    def test_reads_minimal_prompt(self, migration_service, source_dir):
        file_path = create_yaml_prompt(source_dir, 'minimal')

        prompt = migration_service.read_yaml_prompt(file_path)

        assert prompt is not None
        assert prompt.name == 'minimal'
        assert prompt.system_prompt == 'System prompt for minimal'
        assert prompt.user_prompt == ''
        assert prompt.tags == []
        # Group is empty string from YAML - migrate_prompt applies default_group
        assert prompt.group == ''

    def test_returns_none_for_missing_name(self, migration_service, source_dir):
        source_dir.mkdir(parents=True, exist_ok=True)
        file_path = source_dir / 'invalid.yaml'
        with open(file_path, 'w') as f:
            yaml.dump({'system_prompt': 'content'}, f)

        prompt = migration_service.read_yaml_prompt(file_path)

        assert prompt is None

    def test_returns_none_for_missing_system_prompt(self, migration_service, source_dir):
        source_dir.mkdir(parents=True, exist_ok=True)
        file_path = source_dir / 'invalid.yaml'
        with open(file_path, 'w') as f:
            yaml.dump({'name': 'test'}, f)

        prompt = migration_service.read_yaml_prompt(file_path)

        assert prompt is None

    def test_returns_none_for_invalid_yaml(self, migration_service, source_dir):
        source_dir.mkdir(parents=True, exist_ok=True)
        file_path = source_dir / 'invalid.yaml'
        file_path.write_text('not: valid: yaml: content:')

        prompt = migration_service.read_yaml_prompt(file_path)

        assert prompt is None

    def test_returns_none_for_nonexistent_file(self, migration_service, source_dir):
        prompt = migration_service.read_yaml_prompt(source_dir / 'nonexistent.yaml')
        assert prompt is None


class TestMigrationServiceMigratePrompt:
    """Tests for migrating individual prompts."""

    def test_migrates_prompt_to_markdown(self, migration_service, source_dir, target_dir):
        file_path = create_yaml_prompt(
            source_dir,
            'test-prompt',
            system_prompt='System content',
            user_prompt='User content',
            description='Test',
            tags=['tag1'],
        )

        success, message = migration_service.migrate_prompt(file_path)

        assert success is True
        assert 'Migrated' in message

        md_path = target_dir / 'test-prompt.md'
        assert md_path.exists()

        content = md_path.read_text()
        assert 'name: test-prompt' in content
        assert 'System content' in content
        assert '---user---' in content
        assert 'User content' in content

    def test_migrates_prompt_without_user_prompt(self, migration_service, source_dir, target_dir):
        file_path = create_yaml_prompt(source_dir, 'system-only', system_prompt='Only system')

        success, _ = migration_service.migrate_prompt(file_path)

        assert success is True

        md_path = target_dir / 'system-only.md'
        content = md_path.read_text()
        assert 'Only system' in content
        assert '---user---' not in content

    def test_uses_prompt_group(self, migration_service, source_dir, target_dir):
        file_path = create_yaml_prompt(source_dir, 'grouped', group='coding')

        success, _ = migration_service.migrate_prompt(file_path)

        assert success is True
        assert (target_dir / 'coding' / 'grouped.md').exists()

    def test_uses_default_group_when_prompt_has_none(self, migration_service, source_dir, target_dir):
        file_path = create_yaml_prompt(source_dir, 'ungrouped', group='')

        success, _ = migration_service.migrate_prompt(file_path, default_group='misc')

        assert success is True
        assert (target_dir / 'misc' / 'ungrouped.md').exists()

    def test_skips_existing_prompt(self, migration_service, source_dir, target_dir):
        file_path = create_yaml_prompt(source_dir, 'existing')

        migration_service.migrate_prompt(file_path)
        success, message = migration_service.migrate_prompt(file_path)

        assert success is False
        assert 'Already exists' in message

    def test_reports_invalid_file(self, migration_service, source_dir):
        source_dir.mkdir(parents=True, exist_ok=True)
        file_path = source_dir / 'invalid.yaml'
        file_path.write_text('not valid yaml content here:::')

        success, message = migration_service.migrate_prompt(file_path)

        assert success is False
        assert 'Failed to read' in message


class TestMigrationServiceMigrateAll:
    """Tests for migrating all prompts."""

    def test_migrates_all_prompts(self, migration_service, source_dir, target_dir):
        create_yaml_prompt(source_dir, 'prompt1')
        create_yaml_prompt(source_dir, 'prompt2')
        create_yaml_prompt(source_dir, 'prompt3')

        result = migration_service.migrate_all()

        assert result.success_count == 3
        assert result.failure_count == 0
        assert result.skipped_count == 0
        assert (target_dir / 'prompt1.md').exists()
        assert (target_dir / 'prompt2.md').exists()
        assert (target_dir / 'prompt3.md').exists()

    def test_returns_empty_result_for_no_prompts(self, migration_service):
        result = migration_service.migrate_all()

        assert result.success_count == 0
        assert result.failure_count == 0
        assert result.skipped_count == 0

    def test_counts_skipped_prompts(self, migration_service, source_dir):
        create_yaml_prompt(source_dir, 'existing')
        migration_service.migrate_all()

        result = migration_service.migrate_all()

        assert result.success_count == 0
        assert result.skipped_count == 1
        assert result.failure_count == 0

    def test_counts_failed_prompts(self, migration_service, source_dir):
        create_yaml_prompt(source_dir, 'valid')
        source_dir.mkdir(parents=True, exist_ok=True)
        invalid_file = source_dir / 'invalid.yaml'
        invalid_file.write_text('invalid: yaml: content:::')

        result = migration_service.migrate_all()

        assert result.success_count == 1
        assert result.failure_count == 1
        assert len(result.errors) == 1

    def test_uses_default_group(self, migration_service, source_dir, target_dir):
        create_yaml_prompt(source_dir, 'ungrouped', group='')

        migration_service.migrate_all(default_group='imported')

        assert (target_dir / 'imported' / 'ungrouped.md').exists()

    def test_removes_source_files_when_requested(self, migration_service, source_dir):
        file1 = create_yaml_prompt(source_dir, 'prompt1')
        file2 = create_yaml_prompt(source_dir, 'prompt2')

        migration_service.migrate_all(remove_source=True)

        assert not file1.exists()
        assert not file2.exists()

    def test_preserves_source_files_by_default(self, migration_service, source_dir):
        file1 = create_yaml_prompt(source_dir, 'prompt1')

        migration_service.migrate_all()

        assert file1.exists()


class TestMigrationResult:
    """Tests for MigrationResult dataclass."""

    def test_default_values(self):
        result = MigrationResult()

        assert result.success_count == 0
        assert result.failure_count == 0
        assert result.skipped_count == 0
        assert result.errors == []

    def test_custom_values(self):
        result = MigrationResult(
            success_count=5,
            failure_count=2,
            skipped_count=1,
            errors=['error1', 'error2'],
        )

        assert result.success_count == 5
        assert result.failure_count == 2
        assert result.skipped_count == 1
        assert result.errors == ['error1', 'error2']
