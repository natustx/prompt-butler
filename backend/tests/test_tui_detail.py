"""Tests for TUI DetailScreen."""

from unittest.mock import patch

import pytest
from textual.coordinate import Coordinate
from textual.widgets import DataTable

from prompt_butler.models import Prompt
from prompt_butler.services.storage import PromptStorage

from prompt_butler.tui.app import DetailScreen, HomeScreen, PromptButlerApp


@pytest.fixture
def mock_storage(tmp_path):
    """Create a storage with test prompts."""
    prompts_dir = tmp_path / 'prompts'
    prompts_dir.mkdir()
    storage = PromptStorage(prompts_dir=prompts_dir)

    # Create test prompts
    test_prompt = Prompt(
        name='test-prompt',
        description='A test prompt for testing',
        system_prompt='You are a helpful assistant.',
        user_prompt='Please help with {task}',
        group='testing',
        tags=['test', 'example'],
    )
    storage.create(test_prompt)

    long_prompt = Prompt(
        name='long-prompt',
        description='A prompt with long content',
        system_prompt='Line 1\n' * 100,
        user_prompt='',
        group='',
        tags=[],
    )
    storage.create(long_prompt)

    return storage


class TestDetailScreen:
    @pytest.mark.asyncio
    async def test_detail_shows_all_fields(self, mock_storage):
        """Test that detail screen displays all prompt fields."""
        app = PromptButlerApp(storage=mock_storage)
        async with app.run_test() as pilot:
            # Navigate to a prompt detail
            app.push_screen(DetailScreen(mock_storage, 'test-prompt'))
            await pilot.pause()

            # Check title is correct
            assert app.screen.prompt_name == 'test-prompt'
            # Check detail container exists with content
            container = app.screen.query_one('#detail-container')
            assert container is not None
            labels = app.screen.query('Label')
            assert any('Prompt: test-prompt' in str(label.renderable) for label in labels)

    @pytest.mark.asyncio
    async def test_detail_shows_system_prompt(self, mock_storage):
        """Test that system prompt content is displayed."""
        app = PromptButlerApp(storage=mock_storage)
        async with app.run_test() as pilot:
            app.push_screen(DetailScreen(mock_storage, 'test-prompt'))
            await pilot.pause()

            # Check system prompt is visible
            contents = app.screen.query('.prompt-content')
            assert contents
            assert 'You are a helpful assistant.' in str(contents[0].renderable)

    @pytest.mark.asyncio
    async def test_detail_shows_user_prompt_when_present(self, mock_storage):
        """Test that user prompt is shown when present."""
        app = PromptButlerApp(storage=mock_storage)
        async with app.run_test() as pilot:
            app.push_screen(DetailScreen(mock_storage, 'test-prompt'))
            await pilot.pause()

            # Should have multiple section titles (including user prompt section)
            labels = app.screen.query('.section-title')
            # At minimum: prompt name, System Prompt, User Prompt
            assert len(labels) >= 3
            contents = app.screen.query('.prompt-content')
            assert any('Please help with {task}' in str(content.renderable) for content in contents)

    @pytest.mark.asyncio
    async def test_detail_has_scrollable_container(self, mock_storage):
        """Test that detail view has a VerticalScroll container."""
        app = PromptButlerApp(storage=mock_storage)
        async with app.run_test() as pilot:
            app.push_screen(DetailScreen(mock_storage, 'test-prompt'))
            await pilot.pause()

            # Check for VerticalScroll container
            scroll = app.screen.query_one('#detail-scroll')
            assert scroll is not None

    @pytest.mark.asyncio
    async def test_detail_escape_goes_back(self, mock_storage):
        """Test that Esc key returns to list view."""
        app = PromptButlerApp(storage=mock_storage)
        async with app.run_test() as pilot:
            # Start with home screen
            await pilot.pause()
            # Push detail screen
            app.push_screen(DetailScreen(mock_storage, 'test-prompt'))
            await pilot.pause()
            assert isinstance(app.screen, DetailScreen)

            # Press escape to go back
            await pilot.press('escape')
            await pilot.pause()
            assert isinstance(app.screen, HomeScreen)

    @pytest.mark.asyncio
    async def test_detail_q_goes_back(self, mock_storage):
        """Test that q key also returns to list view."""
        app = PromptButlerApp(storage=mock_storage)
        async with app.run_test() as pilot:
            await pilot.pause()

            app.push_screen(DetailScreen(mock_storage, 'test-prompt'))
            await pilot.pause()
            assert isinstance(app.screen, DetailScreen)

            await pilot.press('q')
            await pilot.pause()
            assert isinstance(app.screen, HomeScreen)

    @pytest.mark.asyncio
    async def test_enter_opens_detail_from_table(self, mock_storage):
        """Test that Enter opens the selected prompt detail."""
        app = PromptButlerApp(storage=mock_storage)
        async with app.run_test() as pilot:
            await pilot.pause()

            table = app.screen.query_one('#prompt-list', DataTable)
            table.focus()
            if table.ordered_rows:
                table.cursor_coordinate = Coordinate(0, 0)

            await pilot.press('enter')
            await pilot.pause()

            assert isinstance(app.screen, DetailScreen)

    @pytest.mark.asyncio
    async def test_detail_copy_system_prompt(self, mock_storage):
        """Test that c key copies system prompt to clipboard."""
        app = PromptButlerApp(storage=mock_storage)
        async with app.run_test() as pilot:
            app.push_screen(DetailScreen(mock_storage, 'test-prompt'))
            await pilot.pause()

            with patch('pyperclip.copy') as mock_copy:
                await pilot.press('c')
                await pilot.pause()
                mock_copy.assert_called_once_with('You are a helpful assistant.')

    @pytest.mark.asyncio
    async def test_detail_copy_user_prompt(self, mock_storage):
        """Test that u key copies user prompt to clipboard."""
        app = PromptButlerApp(storage=mock_storage)
        async with app.run_test() as pilot:
            app.push_screen(DetailScreen(mock_storage, 'test-prompt'))
            await pilot.pause()

            with patch('pyperclip.copy') as mock_copy:
                await pilot.press('u')
                await pilot.pause()
                mock_copy.assert_called_once_with('Please help with {task}')

    @pytest.mark.asyncio
    async def test_detail_handles_missing_prompt(self, mock_storage):
        """Test that detail screen handles non-existent prompt gracefully."""
        app = PromptButlerApp(storage=mock_storage)
        async with app.run_test() as pilot:
            app.push_screen(DetailScreen(mock_storage, 'nonexistent'))
            await pilot.pause()

            # Should show 'not found' message
            labels = app.screen.query('Label')
            assert any('Prompt not found' in str(label.renderable) for label in labels)

    @pytest.mark.asyncio
    async def test_detail_shows_metadata(self, mock_storage):
        """Test that description, group, and tags are displayed."""
        app = PromptButlerApp(storage=mock_storage)
        async with app.run_test() as pilot:
            app.push_screen(DetailScreen(mock_storage, 'test-prompt'))
            await pilot.pause()

            # Should have a metadata section
            detail_widgets = app.screen.query('.prompt-detail')
            assert len(detail_widgets) > 0
            detail_text = str(detail_widgets[0].renderable)
            assert 'Description: A test prompt for testing' in detail_text
            assert 'Group: testing' in detail_text
            assert 'Tags: test, example' in detail_text
