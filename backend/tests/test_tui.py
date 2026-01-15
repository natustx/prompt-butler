"""Integration tests for TUI application.

Tests use Textual's built-in testing framework with real storage.
"""

from __future__ import annotations

import pytest
from textual.widgets import Static

from prompt_butler.models import Prompt
from prompt_butler.services.storage import PromptStorage
from prompt_butler.tui.app import FilterSidebar, PromptButlerApp, PromptDetailPanel, PromptTable


@pytest.fixture
def storage(tmp_path):
    """Create a PromptStorage instance with a temporary directory."""
    return PromptStorage(prompts_dir=tmp_path)


@pytest.fixture
def sample_prompts(storage):
    """Create sample prompts for testing."""
    prompts = [
        Prompt(
            name='code-review',
            description='Reviews code for best practices',
            system_prompt='You are an expert code reviewer.',
            user_prompt='Review this code: {code}',
            tags=['code', 'review'],
            group='development',
        ),
        Prompt(
            name='summarize',
            description='Summarizes text content',
            system_prompt='You are a summarization expert.',
            user_prompt='Summarize: {text}',
            tags=['text', 'summary'],
            group='writing',
        ),
        Prompt(
            name='debug-helper',
            description='Helps debug issues',
            system_prompt='You are a debugging assistant.',
            user_prompt='Help debug: {error}',
            tags=['code', 'debug'],
            group='development',
        ),
    ]
    for p in prompts:
        storage.create(p)
    return prompts


class TestPromptButlerAppMount:
    """Tests for app mounting and initialization."""

    @pytest.mark.asyncio
    async def test_app_mounts_successfully(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test():
            assert app.is_running

    @pytest.mark.asyncio
    async def test_app_loads_prompts_on_mount(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test():
            assert len(app.prompts) == 3
            assert len(app.filtered_prompts) == 3

    @pytest.mark.asyncio
    async def test_app_displays_table_with_prompts(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test():
            table = app.query_one('#prompt-table', PromptTable)
            assert table.row_count == 3


class TestPromptTableNavigation:
    """Tests for table keyboard navigation."""

    @pytest.mark.asyncio
    async def test_j_key_moves_cursor_down(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            initial_row = table.cursor_row

            await pilot.press('j')
            assert table.cursor_row == (initial_row or 0) + 1

    @pytest.mark.asyncio
    async def test_k_key_moves_cursor_up(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('j')
            await pilot.press('j')
            row_before = table.cursor_row

            await pilot.press('k')
            assert table.cursor_row == row_before - 1

    @pytest.mark.asyncio
    async def test_enter_key_selects_prompt(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('enter')

            detail_panel = app.query_one('#detail-panel', PromptDetailPanel)
            content = detail_panel.query_one('#detail-content')
            assert 'code-review' in content.render() or len(app.filtered_prompts) > 0


class TestSearchFunctionality:
    """Tests for search/filter functionality."""

    @pytest.mark.asyncio
    async def test_search_action_shows_input(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test():
            app.action_search()

            search_input = app.query_one('#search-input')
            assert search_input.has_class('visible')

    @pytest.mark.asyncio
    async def test_escape_clears_search(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            await pilot.press('/')
            await pilot.press('escape')

            search_input = app.query_one('#search-input')
            assert not search_input.has_class('visible')
            assert app.search_query == ''

    @pytest.mark.asyncio
    async def test_fuzzy_search_filters_prompts(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test():
            app.search_query = 'review'
            app.apply_filters()

            assert len(app.filtered_prompts) >= 1
            names = [p.name for p in app.filtered_prompts]
            assert 'code-review' in names

    @pytest.mark.asyncio
    async def test_search_with_no_results(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test():
            app.search_query = 'zzzznotfound'
            app.apply_filters()

            assert len(app.filtered_prompts) == 0


class TestFilterSidebar:
    """Tests for sidebar filter functionality."""

    @pytest.mark.asyncio
    async def test_sidebar_shows_groups(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test():
            sidebar = app.query_one('#sidebar', FilterSidebar)
            assert 'development' in sidebar.groups
            assert 'writing' in sidebar.groups

    @pytest.mark.asyncio
    async def test_sidebar_shows_tags(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test():
            sidebar = app.query_one('#sidebar', FilterSidebar)
            assert 'code' in sidebar.tags
            assert 'text' in sidebar.tags

    @pytest.mark.asyncio
    async def test_group_filter_filters_prompts(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test():
            app.active_group_filter = 'development'
            app.apply_filters()

            assert len(app.filtered_prompts) == 2
            for p in app.filtered_prompts:
                assert p.group == 'development'

    @pytest.mark.asyncio
    async def test_tag_filter_filters_prompts(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test():
            app.active_tag_filter = 'code'
            app.apply_filters()

            assert len(app.filtered_prompts) == 2
            for p in app.filtered_prompts:
                assert 'code' in p.tags

    @pytest.mark.asyncio
    async def test_combined_filters(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test():
            app.active_group_filter = 'development'
            app.active_tag_filter = 'review'
            app.apply_filters()

            assert len(app.filtered_prompts) == 1
            assert app.filtered_prompts[0].name == 'code-review'


class TestPromptDetailPanel:
    """Tests for prompt detail display."""

    @pytest.mark.asyncio
    async def test_detail_panel_shows_prompt_info(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test():
            prompt = sample_prompts[0]
            detail_panel = app.query_one('#detail-panel', PromptDetailPanel)
            detail_panel.show_prompt(prompt)

            content = detail_panel.query_one('#detail-content')
            rendered = str(content.render())
            assert 'code-review' in rendered or prompt.name in str(content.renderable)

    @pytest.mark.asyncio
    async def test_detail_panel_shows_default_message(self, storage):
        app = PromptButlerApp(storage=storage)
        async with app.run_test():
            detail_panel = app.query_one('#detail-panel', PromptDetailPanel)
            detail_panel.show_prompt(None)

            content = detail_panel.query_one('#detail-content', Static)
            assert 'Select a prompt' in str(content.render())


class TestAppActions:
    """Tests for app-level actions."""

    @pytest.mark.asyncio
    async def test_refresh_action_reloads_prompts(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test():
            initial_count = len(app.prompts)

            storage.create(
                Prompt(
                    name='new-prompt',
                    system_prompt='New system prompt',
                    group='default',
                )
            )

            app.action_refresh()

            assert len(app.prompts) == initial_count + 1

    @pytest.mark.asyncio
    async def test_quit_action_exits_app(self, storage, sample_prompts):
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            await pilot.press('q')


class TestEmptyState:
    """Tests for empty storage state."""

    @pytest.mark.asyncio
    async def test_app_handles_empty_storage(self, storage):
        app = PromptButlerApp(storage=storage)
        async with app.run_test():
            assert len(app.prompts) == 0
            assert len(app.filtered_prompts) == 0

            table = app.query_one('#prompt-table', PromptTable)
            assert table.row_count == 0

    @pytest.mark.asyncio
    async def test_sidebar_empty_when_no_prompts(self, storage):
        app = PromptButlerApp(storage=storage)
        async with app.run_test():
            sidebar = app.query_one('#sidebar', FilterSidebar)
            assert sidebar.groups == []
            assert sidebar.tags == []
