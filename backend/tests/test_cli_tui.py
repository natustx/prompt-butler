import sys

import pytest
from typer.testing import CliRunner

from prompt_butler.cli import app


@pytest.fixture
def runner():
    return CliRunner()


class TestTuiCommand:
    def test_tui_command_exists(self, runner):
        """Test that the tui command exists and shows help."""
        result = runner.invoke(app, ['tui', '--help'])

        assert result.exit_code == 0
        assert 'Terminal User Interface' in result.output

    def test_tui_launches_app(self, runner, tmp_path, monkeypatch):
        """Test that tui command creates and runs the app."""
        import prompt_butler.services.config as config_module
        from prompt_butler.services.config import Config

        # Create a mock config
        config_file = tmp_path / 'config.yaml'
        prompts_dir = tmp_path / 'prompts'
        prompts_dir.mkdir()

        config = Config(prompts_dir=prompts_dir)
        config.save(config_file)

        monkeypatch.setattr(config_module, 'DEFAULT_CONFIG_FILE', config_file)
        monkeypatch.setattr(config_module, '_config', None)

        # Track if app was created and run
        app_created = False
        app_run = False

        class MockTuiApp:
            def __init__(self, storage=None):
                nonlocal app_created
                app_created = True
                self.storage = storage

            def run(self):
                nonlocal app_run
                app_run = True

        # Patch the TUI app class at the module level
        import prompt_butler.tui.app as tui_app
        monkeypatch.setattr(tui_app, 'PromptButlerApp', MockTuiApp)

        runner.invoke(app, ['tui'])

        # App should have been created and run
        assert app_created, 'TUI app was not created'
        assert app_run, 'TUI app was not run'

    def test_tui_handles_missing_textual(self, runner, monkeypatch):
        """Test that tui shows helpful error when textual is not available."""

        # Remove tui from sys.modules so the import fails
        modules_to_remove = [k for k in sys.modules if k.startswith('prompt_butler.tui')]
        for mod in modules_to_remove:
            monkeypatch.delitem(sys.modules, mod, raising=False)

        # Make the import fail
        def mock_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.startswith('prompt_butler.tui'):
                raise ImportError('No module named prompt_butler.tui')
            return original_import(name, globals, locals, fromlist, level)

        import builtins
        original_import = builtins.__import__
        monkeypatch.setattr(builtins, '__import__', mock_import)

        result = runner.invoke(app, ['tui'])

        assert result.exit_code == 1
        assert 'textual' in result.output.lower()

    def test_tui_passes_storage_to_app(self, runner, tmp_path, monkeypatch):
        """Test that TUI receives storage with correct prompts_dir."""
        import prompt_butler.services.config as config_module
        from prompt_butler.services.config import Config

        # Create a mock config
        config_file = tmp_path / 'config.yaml'
        prompts_dir = tmp_path / 'prompts'
        prompts_dir.mkdir()

        config = Config(prompts_dir=prompts_dir)
        config.save(config_file)

        monkeypatch.setattr(config_module, 'DEFAULT_CONFIG_FILE', config_file)
        monkeypatch.setattr(config_module, '_config', None)

        # Track the storage that was passed to the app
        captured_storage = None

        class MockTuiApp:
            def __init__(self, storage=None):
                nonlocal captured_storage
                captured_storage = storage

            def run(self):
                pass  # Don't actually run

        # Patch the TUI app class
        import prompt_butler.tui.app as tui_app
        monkeypatch.setattr(tui_app, 'PromptButlerApp', MockTuiApp)

        runner.invoke(app, ['tui'])

        # Verify storage was passed with correct prompts_dir
        assert captured_storage is not None
        assert captured_storage.prompts_dir == prompts_dir
