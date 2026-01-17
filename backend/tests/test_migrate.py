import yaml

from prompt_butler.services.migrate import MigrationResult, _read_yaml_prompt, migrate_prompts
from prompt_butler.services.storage import PromptStorage


class TestReadYamlPrompt:
    def test_read_valid_prompt(self, tmp_path):
        yaml_file = tmp_path / 'test.yaml'
        yaml_file.write_text(
            yaml.dump({
                'name': 'test-prompt',
                'description': 'Test description',
                'system_prompt': 'You are helpful.',
                'user_prompt': 'Help me with {task}',
                'tags': ['test', 'example'],
                'group': 'testing',
            })
        )

        result = _read_yaml_prompt(yaml_file)

        assert result is not None
        assert result.name == 'test-prompt'
        assert result.description == 'Test description'
        assert result.system_prompt == 'You are helpful.'
        assert result.user_prompt == 'Help me with {task}'
        assert result.tags == ['test', 'example']
        assert result.group == 'testing'

    def test_read_minimal_prompt(self, tmp_path):
        yaml_file = tmp_path / 'test.yaml'
        yaml_file.write_text(
            yaml.dump({
                'name': 'minimal',
                'system_prompt': 'You are helpful.',
            })
        )

        result = _read_yaml_prompt(yaml_file)

        assert result is not None
        assert result.name == 'minimal'
        assert result.system_prompt == 'You are helpful.'
        assert result.description == ''
        assert result.user_prompt == ''
        assert result.tags == []
        assert result.group == ''

    def test_read_missing_name_returns_none(self, tmp_path):
        yaml_file = tmp_path / 'test.yaml'
        yaml_file.write_text(yaml.dump({'system_prompt': 'Content'}))

        result = _read_yaml_prompt(yaml_file)

        assert result is None

    def test_read_missing_system_prompt_returns_none(self, tmp_path):
        yaml_file = tmp_path / 'test.yaml'
        yaml_file.write_text(yaml.dump({'name': 'test'}))

        result = _read_yaml_prompt(yaml_file)

        assert result is None

    def test_read_empty_file_returns_none(self, tmp_path):
        yaml_file = tmp_path / 'test.yaml'
        yaml_file.write_text('')

        result = _read_yaml_prompt(yaml_file)

        assert result is None


class TestMigrationResult:
    def test_total_processed(self):
        result = MigrationResult(success_count=5, failure_count=2, skipped_count=3)

        assert result.total_processed == 10

    def test_defaults(self):
        result = MigrationResult()

        assert result.success_count == 0
        assert result.failure_count == 0
        assert result.skipped_count == 0
        assert result.errors == []


class TestMigratePrompts:
    def test_migrate_single_prompt(self, tmp_path):
        source_dir = tmp_path / 'source'
        target_dir = tmp_path / 'target'
        source_dir.mkdir()
        target_dir.mkdir()

        # Create a YAML prompt
        (source_dir / 'test.yaml').write_text(
            yaml.dump({
                'name': 'test-prompt',
                'system_prompt': 'You are helpful.',
                'description': 'Test',
            })
        )

        storage = PromptStorage(prompts_dir=target_dir)
        result = migrate_prompts(source_dir, storage)

        assert result.success_count == 1
        assert result.failure_count == 0
        assert result.skipped_count == 0

        # Verify prompt was created
        prompt = storage.read('test-prompt')
        assert prompt is not None
        assert prompt.name == 'test-prompt'

    def test_migrate_multiple_prompts(self, tmp_path):
        source_dir = tmp_path / 'source'
        target_dir = tmp_path / 'target'
        source_dir.mkdir()
        target_dir.mkdir()

        # Create multiple YAML prompts
        for i in range(3):
            (source_dir / f'prompt{i}.yaml').write_text(
                yaml.dump({
                    'name': f'prompt{i}',
                    'system_prompt': f'Content {i}',
                })
            )

        storage = PromptStorage(prompts_dir=target_dir)
        result = migrate_prompts(source_dir, storage)

        assert result.success_count == 3
        assert result.failure_count == 0

    def test_migrate_preserves_all_fields(self, tmp_path):
        source_dir = tmp_path / 'source'
        target_dir = tmp_path / 'target'
        source_dir.mkdir()
        target_dir.mkdir()

        (source_dir / 'full.yaml').write_text(
            yaml.dump({
                'name': 'full-prompt',
                'description': 'Full description',
                'system_prompt': 'System content',
                'user_prompt': 'User content',
                'tags': ['tag1', 'tag2'],
                'group': 'mygroup',
            })
        )

        storage = PromptStorage(prompts_dir=target_dir)
        migrate_prompts(source_dir, storage)

        prompt = storage.read('full-prompt', group='mygroup')
        assert prompt is not None
        assert prompt.name == 'full-prompt'
        assert prompt.description == 'Full description'
        assert prompt.system_prompt == 'System content'
        assert prompt.user_prompt == 'User content'
        assert prompt.tags == ['tag1', 'tag2']
        assert prompt.group == 'mygroup'

    def test_migrate_creates_group_folders(self, tmp_path):
        source_dir = tmp_path / 'source'
        target_dir = tmp_path / 'target'
        source_dir.mkdir()
        target_dir.mkdir()

        (source_dir / 'grouped.yaml').write_text(
            yaml.dump({
                'name': 'grouped-prompt',
                'system_prompt': 'Content',
                'group': 'coding',
            })
        )

        storage = PromptStorage(prompts_dir=target_dir)
        migrate_prompts(source_dir, storage)

        # Verify folder was created
        assert (target_dir / 'coding').is_dir()
        assert (target_dir / 'coding' / 'grouped-prompt.md').exists()

    def test_migrate_skips_existing_by_default(self, tmp_path):
        source_dir = tmp_path / 'source'
        target_dir = tmp_path / 'target'
        source_dir.mkdir()
        target_dir.mkdir()

        # Create prompt in source
        (source_dir / 'test.yaml').write_text(
            yaml.dump({
                'name': 'existing',
                'system_prompt': 'Original',
            })
        )

        # Pre-create in target
        storage = PromptStorage(prompts_dir=target_dir)
        from prompt_butler.models import Prompt

        storage.create(Prompt(name='existing', system_prompt='Pre-existing'))

        result = migrate_prompts(source_dir, storage)

        assert result.success_count == 0
        assert result.skipped_count == 1

        # Original should be unchanged
        prompt = storage.read('existing')
        assert prompt.system_prompt == 'Pre-existing'

    def test_migrate_overwrites_when_skip_disabled(self, tmp_path):
        source_dir = tmp_path / 'source'
        target_dir = tmp_path / 'target'
        source_dir.mkdir()
        target_dir.mkdir()

        (source_dir / 'test.yaml').write_text(
            yaml.dump({
                'name': 'existing',
                'system_prompt': 'New content',
            })
        )

        storage = PromptStorage(prompts_dir=target_dir)
        from prompt_butler.models import Prompt

        storage.create(Prompt(name='existing', system_prompt='Old content'))

        result = migrate_prompts(source_dir, storage, skip_existing=False)

        assert result.success_count == 1
        assert result.skipped_count == 0

        prompt = storage.read('existing')
        assert prompt.system_prompt == 'New content'

    def test_migrate_handles_invalid_yaml(self, tmp_path):
        source_dir = tmp_path / 'source'
        target_dir = tmp_path / 'target'
        source_dir.mkdir()
        target_dir.mkdir()

        (source_dir / 'invalid.yaml').write_text('invalid: yaml: [')

        storage = PromptStorage(prompts_dir=target_dir)
        result = migrate_prompts(source_dir, storage)

        assert result.failure_count == 1
        assert len(result.errors) == 1

    def test_migrate_skips_empty_files(self, tmp_path):
        source_dir = tmp_path / 'source'
        target_dir = tmp_path / 'target'
        source_dir.mkdir()
        target_dir.mkdir()

        (source_dir / 'empty.yaml').write_text('')

        storage = PromptStorage(prompts_dir=target_dir)
        result = migrate_prompts(source_dir, storage)

        assert result.skipped_count == 1
        assert result.failure_count == 0

    def test_migrate_empty_directory(self, tmp_path):
        source_dir = tmp_path / 'source'
        target_dir = tmp_path / 'target'
        source_dir.mkdir()
        target_dir.mkdir()

        storage = PromptStorage(prompts_dir=target_dir)
        result = migrate_prompts(source_dir, storage)

        assert result.total_processed == 0

    def test_migrate_calls_progress_callback(self, tmp_path):
        source_dir = tmp_path / 'source'
        target_dir = tmp_path / 'target'
        source_dir.mkdir()
        target_dir.mkdir()

        (source_dir / 'test.yaml').write_text(
            yaml.dump({
                'name': 'test',
                'system_prompt': 'Content',
            })
        )

        progress_calls = []

        def on_progress(action: str, message: str) -> None:
            progress_calls.append((action, message))

        storage = PromptStorage(prompts_dir=target_dir)
        migrate_prompts(source_dir, storage, on_progress=on_progress)

        # Should have start, success, and done calls
        actions = [call[0] for call in progress_calls]
        assert 'start' in actions
        assert 'success' in actions
        assert 'done' in actions

    def test_migrate_continues_after_error(self, tmp_path):
        source_dir = tmp_path / 'source'
        target_dir = tmp_path / 'target'
        source_dir.mkdir()
        target_dir.mkdir()

        # First file is invalid
        (source_dir / 'a_invalid.yaml').write_text('invalid: yaml: [')
        # Second file is valid
        (source_dir / 'b_valid.yaml').write_text(
            yaml.dump({
                'name': 'valid-prompt',
                'system_prompt': 'Content',
            })
        )

        storage = PromptStorage(prompts_dir=target_dir)
        result = migrate_prompts(source_dir, storage)

        # Should have processed both
        assert result.failure_count == 1
        assert result.success_count == 1

        # Valid prompt should exist
        assert storage.read('valid-prompt') is not None
