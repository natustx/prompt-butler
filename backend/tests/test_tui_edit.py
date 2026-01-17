"""Tests for TUI AddEditScreen."""

import pytest
from textual.widgets import Input, ListView, TextArea

from prompt_butler.models import Prompt
from prompt_butler.services.storage import PromptStorage
from prompt_butler.tui.app import AddEditScreen, HomeScreen, PromptButlerApp


@pytest.mark.asyncio
async def test_add_prompt_saves_and_closes(tmp_path):
    """Test that saving a new prompt persists and returns to HomeScreen."""
    storage = PromptStorage(prompts_dir=tmp_path / 'prompts')
    app = PromptButlerApp(storage=storage)

    async with app.run_test() as pilot:
        app.push_screen(AddEditScreen(storage))
        await pilot.pause()

        screen = app.screen
        screen.query_one('#name-input', Input).value = 'new-prompt'
        screen.query_one('#group-input', Input).value = 'group1'
        screen.query_one('#description-input', Input).value = 'A test prompt'
        screen.query_one('#tags-input', Input).value = 'tag1, tag2'
        screen.query_one('#system-prompt-input', TextArea).text = 'System prompt'
        screen.query_one('#user-prompt-input', TextArea).text = 'User prompt'

        await pilot.press('ctrl+s')
        await pilot.pause()

        saved = storage.read('new-prompt', 'group1')
        assert saved is not None
        assert isinstance(app.screen, HomeScreen)


@pytest.mark.asyncio
async def test_cancel_discards_changes(tmp_path):
    """Test that cancel exits without saving."""
    storage = PromptStorage(prompts_dir=tmp_path / 'prompts')
    app = PromptButlerApp(storage=storage)

    async with app.run_test() as pilot:
        app.push_screen(AddEditScreen(storage))
        await pilot.pause()

        screen = app.screen
        screen.query_one('#name-input', Input).value = 'Canceled Prompt'
        screen.query_one('#system-prompt-input', TextArea).text = 'System prompt'

        await pilot.press('escape')
        await pilot.pause()

        assert storage.read('Canceled Prompt') is None
        assert isinstance(app.screen, HomeScreen)


@pytest.mark.asyncio
async def test_group_autocomplete_shows_matches(tmp_path):
    """Test that group suggestions appear as the user types."""
    storage = PromptStorage(prompts_dir=tmp_path / 'prompts')
    storage.create(
        Prompt(
            name='alpha-prompt',
            description='',
            system_prompt='System',
            user_prompt='',
            group='alpha',
            tags=['test'],
        )
    )

    app = PromptButlerApp(storage=storage)
    async with app.run_test() as pilot:
        app.push_screen(AddEditScreen(storage))
        await pilot.pause()

        screen = app.screen
        screen.query_one('#group-input', Input).value = 'al'
        await pilot.pause()

        suggestions = screen.query_one('#group-suggestions', ListView)
        assert suggestions.has_class('-visible')
        assert len(suggestions.children) > 0


@pytest.mark.asyncio
async def test_tag_autocomplete_shows_matches(tmp_path):
    """Test that tag suggestions appear for the current tag."""
    storage = PromptStorage(prompts_dir=tmp_path / 'prompts')
    storage.create(
        Prompt(
            name='tagged-prompt',
            description='',
            system_prompt='System',
            user_prompt='',
            group='',
            tags=['alpha', 'beta'],
        )
    )

    app = PromptButlerApp(storage=storage)
    async with app.run_test() as pilot:
        app.push_screen(AddEditScreen(storage))
        await pilot.pause()

        screen = app.screen
        screen.query_one('#tags-input', Input).value = 'al'
        await pilot.pause()

        suggestions = screen.query_one('#tag-suggestions', ListView)
        assert suggestions.has_class('-visible')
        assert len(suggestions.children) > 0


@pytest.mark.asyncio
async def test_edit_prompt_updates_group(tmp_path):
    """Test that editing a prompt can move it to a new group."""
    storage = PromptStorage(prompts_dir=tmp_path / 'prompts')
    storage.create(
        Prompt(
            name='move-prompt',
            description='',
            system_prompt='System',
            user_prompt='',
            group='old',
            tags=[],
        )
    )

    app = PromptButlerApp(storage=storage)
    async with app.run_test() as pilot:
        app.push_screen(AddEditScreen(storage, 'move-prompt', prompt_group='old'))
        await pilot.pause()

        screen = app.screen
        screen.query_one('#group-input', Input).value = 'new'
        await pilot.press('ctrl+s')
        await pilot.pause()

        assert storage.read('move-prompt', 'new') is not None
        old_path = storage._get_prompt_path('move-prompt', 'old')
        assert not old_path.exists()
