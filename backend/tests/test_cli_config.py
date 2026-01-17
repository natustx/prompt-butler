import json

import pytest
from typer.testing import CliRunner

from prompt_butler.cli import app


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_config(tmp_path, monkeypatch):
    """Mock the config module to use a test config file."""
    from prompt_butler.services.config import Config

    config_file = tmp_path / 'config.yaml'
    prompts_dir = tmp_path / 'prompts'
    prompts_dir.mkdir()

    # Create initial config
    config = Config(
        prompts_dir=prompts_dir,
        editor='vim',
        default_group='testing',
    )
    config.save(config_file)

    # Mock the config file path
    import prompt_butler.services.config as config_module
    monkeypatch.setattr(config_module, 'DEFAULT_CONFIG_FILE', config_file)

    # Reset global config state
    monkeypatch.setattr(config_module, '_config', None)

    return config_file, prompts_dir


class TestConfigShow:
    def test_config_shows_settings(self, runner, mock_config):
        config_file, prompts_dir = mock_config

        result = runner.invoke(app, ['config'])

        assert result.exit_code == 0
        assert 'Configuration' in result.output
        # Rich may wrap long paths, so check for the directory name
        assert prompts_dir.name in result.output
        assert 'vim' in result.output
        assert 'testing' in result.output

    def test_config_json_output(self, runner, mock_config):
        config_file, prompts_dir = mock_config

        result = runner.invoke(app, ['--json', 'config'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert str(prompts_dir) in data['prompts_dir']
        assert data['editor'] == 'vim'
        assert data['default_group'] == 'testing'
        assert 'config_file' in data


class TestConfigSet:
    def test_config_set_editor(self, runner, mock_config):
        config_file, prompts_dir = mock_config

        result = runner.invoke(app, ['config', 'set', 'editor', 'nano'])

        assert result.exit_code == 0
        assert 'Set' in result.output
        assert 'editor' in result.output
        assert 'nano' in result.output

        # Verify it was saved
        import yaml
        with open(config_file) as f:
            saved = yaml.safe_load(f)
        assert saved['editor'] == 'nano'

    def test_config_set_default_group(self, runner, mock_config):
        config_file, prompts_dir = mock_config

        result = runner.invoke(app, ['config', 'set', 'default_group', 'coding'])

        assert result.exit_code == 0
        assert 'coding' in result.output

    def test_config_set_prompts_dir(self, runner, mock_config, tmp_path):
        config_file, prompts_dir = mock_config
        new_dir = tmp_path / 'new_prompts'

        result = runner.invoke(app, ['config', 'set', 'prompts_dir', str(new_dir)])

        assert result.exit_code == 0
        # Rich may wrap long paths, so check for the directory name
        assert new_dir.name in result.output

    def test_config_set_invalid_key(self, runner, mock_config):
        result = runner.invoke(app, ['config', 'set', 'invalid_key', 'value'])

        assert result.exit_code == 1
        assert 'Unknown config key' in result.output

    def test_config_set_json_output(self, runner, mock_config):
        result = runner.invoke(app, ['--json', 'config', 'set', 'editor', 'emacs'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['updated'] is True
        assert data['key'] == 'editor'
        assert data['value'] == 'emacs'


class TestConfigPath:
    def test_config_path_shows_file(self, runner, mock_config):
        config_file, prompts_dir = mock_config

        result = runner.invoke(app, ['config', 'path'])

        assert result.exit_code == 0
        # Rich may wrap long paths, so check for the file name
        assert config_file.name in result.output
        assert 'exists' in result.output

    def test_config_path_json_output(self, runner, mock_config):
        config_file, prompts_dir = mock_config

        result = runner.invoke(app, ['--json', 'config', 'path'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        # Check that the path ends with the expected file
        assert data['config_file'].endswith(config_file.name)
        assert data['exists'] is True

    def test_config_path_when_no_file(self, runner, tmp_path, monkeypatch):
        import prompt_butler.services.config as config_module
        nonexistent = tmp_path / 'nonexistent' / 'config.yaml'
        monkeypatch.setattr(config_module, 'DEFAULT_CONFIG_FILE', nonexistent)
        monkeypatch.setattr(config_module, '_config', None)

        result = runner.invoke(app, ['config', 'path'])

        assert result.exit_code == 0
        # Rich may wrap text across lines, so normalize whitespace
        output = ' '.join(result.output.split())
        assert 'not created yet' in output
