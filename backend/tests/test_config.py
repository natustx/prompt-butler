"""Tests for ConfigService."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from prompt_butler.services.config import DEFAULT_CONFIG, Config, ConfigService


@pytest.fixture
def config_file(tmp_path):
    """Create a temporary config file path."""
    return tmp_path / 'config.yaml'


@pytest.fixture
def config_service(config_file):
    """Create a ConfigService with a temporary config file."""
    return ConfigService(config_path=config_file)


class TestConfig:
    """Tests for Config model."""

    def test_default_values(self):
        config = Config()
        assert config.prompts_dir == '~/.prompts'
        assert config.default_group == 'default'
        assert config.editor == ''

    def test_custom_values(self):
        config = Config(
            prompts_dir='/custom/path',
            default_group='work',
            editor='nano',
        )
        assert config.prompts_dir == '/custom/path'
        assert config.default_group == 'work'
        assert config.editor == 'nano'

    def test_get_prompts_dir_expands_user(self):
        config = Config(prompts_dir='~/my-prompts')
        result = config.get_prompts_dir()
        assert result == Path(os.path.expanduser('~/my-prompts'))


class TestConfigService:
    """Tests for ConfigService."""

    def test_load_creates_default_when_missing(self, config_service, config_file):
        assert not config_file.exists()
        config = config_service.load()
        assert config.prompts_dir == DEFAULT_CONFIG.prompts_dir
        assert config.default_group == DEFAULT_CONFIG.default_group

    def test_load_reads_existing_config(self, config_service, config_file):
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text('prompts_dir: /custom/prompts\ndefault_group: projects\n')

        config = config_service.load()
        assert config.prompts_dir == '/custom/prompts'
        assert config.default_group == 'projects'

    def test_save_creates_file(self, config_service, config_file):
        config_service.save()
        assert config_file.exists()

    def test_save_writes_config(self, config_service, config_file):
        custom_config = Config(prompts_dir='/my/prompts', default_group='test')
        config_service.save(custom_config)

        content = config_file.read_text()
        assert '/my/prompts' in content
        assert 'test' in content

    def test_get_returns_value(self, config_service):
        config_service._config = Config(prompts_dir='/test/path')
        assert config_service.get('prompts_dir') == '/test/path'

    def test_get_returns_none_for_unknown_key(self, config_service):
        config_service.load()
        assert config_service.get('nonexistent') is None

    def test_set_updates_value(self, config_service, config_file):
        config_service.load()
        result = config_service.set('prompts_dir', '/new/path')

        assert result is True
        assert config_service.get('prompts_dir') == '/new/path'
        assert config_file.exists()

    def test_set_returns_false_for_unknown_key(self, config_service):
        config_service.load()
        result = config_service.set('unknown_key', 'value')
        assert result is False

    def test_as_dict_returns_all_values(self, config_service):
        config_service.load()
        data = config_service.as_dict()

        assert 'prompts_dir' in data
        assert 'default_group' in data
        assert 'editor' in data

    def test_reset_restores_defaults(self, config_service, config_file):
        config_service._config = Config(prompts_dir='/custom', default_group='custom')
        config_service.reset()

        assert config_service.get('prompts_dir') == DEFAULT_CONFIG.prompts_dir
        assert config_service.get('default_group') == DEFAULT_CONFIG.default_group

    def test_get_editor_uses_config_value(self, config_service):
        config_service._config = Config(editor='nvim')
        assert config_service.get_editor() == 'nvim'

    def test_get_editor_falls_back_to_env(self, config_service, monkeypatch):
        monkeypatch.setenv('EDITOR', 'nano')
        config_service._config = Config(editor='')
        assert config_service.get_editor() == 'nano'

    def test_get_editor_uses_visual_if_no_editor(self, config_service, monkeypatch):
        monkeypatch.delenv('EDITOR', raising=False)
        monkeypatch.setenv('VISUAL', 'emacs')
        config_service._config = Config(editor='')
        assert config_service.get_editor() == 'emacs'

    def test_get_editor_defaults_to_vim(self, config_service, monkeypatch):
        monkeypatch.delenv('EDITOR', raising=False)
        monkeypatch.delenv('VISUAL', raising=False)
        config_service._config = Config(editor='')
        assert config_service.get_editor() == 'vim'

    def test_config_file_path_property(self, config_service, config_file):
        assert config_service.config_file_path == config_file

    def test_load_handles_malformed_yaml(self, config_service, config_file):
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text('this is: [invalid: yaml')

        config = config_service.load()
        assert config == DEFAULT_CONFIG

    def test_load_handles_empty_file(self, config_service, config_file):
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text('')

        config = config_service.load()
        assert config.prompts_dir == DEFAULT_CONFIG.prompts_dir

    def test_caching_returns_same_config(self, config_service):
        config1 = config_service.load()
        config2 = config_service.load()
        assert config1 is config2
