import os
from pathlib import Path
from unittest.mock import patch

from prompt_butler.services.config import DEFAULT_PROMPTS_DIR, Config, get_config, reload_config


class TestConfigDefaults:
    def test_default_prompts_dir(self):
        config = Config()
        assert config.prompts_dir == DEFAULT_PROMPTS_DIR

    def test_default_editor_from_env(self):
        with patch.dict(os.environ, {'EDITOR': 'nano'}):
            config = Config()
            assert config.editor == 'nano'

    def test_default_editor_fallback(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('EDITOR', None)
            config = Config()
            assert config.editor == 'vim'

    def test_default_group_is_empty(self):
        config = Config()
        assert config.default_group == ''

    def test_prompts_dir_string_converted_to_path(self):
        config = Config(prompts_dir='~/custom')
        assert isinstance(config.prompts_dir, Path)
        assert config.prompts_dir == Path.home() / 'custom'


class TestConfigLoad:
    def test_load_missing_file_returns_defaults(self, tmp_path):
        missing = tmp_path / 'nonexistent.yaml'
        config = Config.load(missing)
        assert config.prompts_dir == DEFAULT_PROMPTS_DIR

    def test_load_empty_file_returns_defaults(self, tmp_path):
        config_file = tmp_path / 'config.yaml'
        config_file.write_text('')
        config = Config.load(config_file)
        assert config.prompts_dir == DEFAULT_PROMPTS_DIR

    def test_load_valid_config(self, tmp_path):
        config_file = tmp_path / 'config.yaml'
        config_file.write_text(
            'prompts_dir: /custom/prompts\n'
            'editor: code\n'
            'default_group: work\n'
        )
        config = Config.load(config_file)
        assert config.prompts_dir == Path('/custom/prompts')
        assert config.editor == 'code'
        assert config.default_group == 'work'

    def test_load_partial_config_fills_defaults(self, tmp_path):
        config_file = tmp_path / 'config.yaml'
        config_file.write_text('default_group: personal\n')

        with patch.dict(os.environ, {'EDITOR': 'emacs'}):
            config = Config.load(config_file)

        assert config.prompts_dir == DEFAULT_PROMPTS_DIR
        assert config.editor == 'emacs'
        assert config.default_group == 'personal'

    def test_load_invalid_yaml_returns_defaults(self, tmp_path):
        config_file = tmp_path / 'config.yaml'
        config_file.write_text('invalid: yaml: content: [')
        config = Config.load(config_file)
        assert config.prompts_dir == DEFAULT_PROMPTS_DIR

    def test_load_expands_tilde_in_prompts_dir(self, tmp_path):
        config_file = tmp_path / 'config.yaml'
        config_file.write_text('prompts_dir: ~/.my-prompts\n')
        config = Config.load(config_file)
        assert config.prompts_dir == Path.home() / '.my-prompts'


class TestConfigSave:
    def test_save_creates_parent_directories(self, tmp_path):
        config = Config(
            prompts_dir=Path('/custom/prompts'),
            editor='nano',
            default_group='test',
        )
        nested_path = tmp_path / 'nested' / 'dir' / 'config.yaml'
        config.save(nested_path)
        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_save_writes_valid_yaml(self, tmp_path):
        config = Config(
            prompts_dir=Path('/my/prompts'),
            editor='code',
            default_group='work',
        )
        config_file = tmp_path / 'config.yaml'
        config.save(config_file)

        loaded = Config.load(config_file)
        assert loaded.prompts_dir == Path('/my/prompts')
        assert loaded.editor == 'code'
        assert loaded.default_group == 'work'


class TestConfigUpdate:
    def test_update_returns_new_config(self):
        original = Config(default_group='old')
        updated = original.update(default_group='new')
        assert updated is not original
        assert original.default_group == 'old'
        assert updated.default_group == 'new'

    def test_update_preserves_unchanged_values(self):
        original = Config(
            prompts_dir=Path('/custom'),
            editor='nano',
            default_group='test',
        )
        updated = original.update(editor='code')
        assert updated.prompts_dir == Path('/custom')
        assert updated.editor == 'code'
        assert updated.default_group == 'test'


class TestGlobalConfig:
    def test_get_config_returns_same_instance(self, tmp_path, monkeypatch):
        import prompt_butler.services.config as config_module

        config_module._config = None
        monkeypatch.setattr(config_module, 'DEFAULT_CONFIG_FILE', tmp_path / 'missing.yaml')

        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reload_config_returns_fresh_instance(self, tmp_path, monkeypatch):
        import prompt_butler.services.config as config_module

        config_file = tmp_path / 'config.yaml'
        config_file.write_text('default_group: initial\n')
        monkeypatch.setattr(config_module, 'DEFAULT_CONFIG_FILE', config_file)
        config_module._config = None

        config1 = get_config()
        assert config1.default_group == 'initial'

        config_file.write_text('default_group: updated\n')
        config2 = reload_config()

        assert config2.default_group == 'updated'
        assert config2 is not config1
