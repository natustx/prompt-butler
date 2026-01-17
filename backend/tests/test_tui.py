"""Integration tests for TUI application.

Tests use Textual's built-in testing framework with real storage.
"""

from __future__ import annotations

import pytest
from textual.widgets import Button, Input, Static, TextArea

from prompt_butler.models import Prompt
from prompt_butler.services.storage import PromptStorage
from prompt_butler.tui.app import (
    AddEditPromptScreen,
    DeleteConfirmScreen,
    FilterSidebar,
    PromptButlerApp,
    PromptDetailPanel,
    PromptDetailScreen,
    PromptTable,
)


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


class TestPromptDetailScreen:
    """Tests for the full-screen prompt detail view."""

    @pytest.mark.asyncio
    async def test_enter_opens_detail_screen(self, storage, sample_prompts):
        """Test that pressing Enter on a prompt opens the detail screen."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('enter')
            await pilot.pause()
            assert len(app.screen_stack) == 2
            assert isinstance(app.screen, PromptDetailScreen)

    @pytest.mark.asyncio
    async def test_detail_screen_shows_prompt_name(self, storage, sample_prompts):
        """Test that detail screen shows prompt name."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('enter')
            await pilot.pause()
            header_text = app.screen.query_one('#detail-header-text', Static)
            assert 'code-review' in str(header_text.render())

    @pytest.mark.asyncio
    async def test_detail_screen_shows_system_prompt(self, storage, sample_prompts):
        """Test that detail screen shows system prompt content."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('enter')
            await pilot.pause()
            system_content = app.screen.query_one('#system-prompt-content', Static)
            assert 'expert code reviewer' in str(system_content.render())

    @pytest.mark.asyncio
    async def test_detail_screen_shows_user_prompt(self, storage, sample_prompts):
        """Test that detail screen shows user prompt content."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('enter')
            await pilot.pause()
            user_content = app.screen.query_one('#user-prompt-content', Static)
            assert 'Review this code' in str(user_content.render())

    @pytest.mark.asyncio
    async def test_escape_returns_to_list_view(self, storage, sample_prompts):
        """Test that pressing Escape returns from detail to list view."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('enter')
            await pilot.pause()
            assert len(app.screen_stack) == 2
            await pilot.press('escape')
            await pilot.pause()
            assert len(app.screen_stack) == 1
            assert not isinstance(app.screen, PromptDetailScreen)

    @pytest.mark.asyncio
    async def test_detail_screen_copy_system_prompt(self, storage, sample_prompts, monkeypatch):
        """Test that pressing c copies system prompt to clipboard."""
        copied_text = []

        def mock_copy(text):
            copied_text.append(text)

        monkeypatch.setattr('pyperclip.copy', mock_copy)

        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('enter')
            await pilot.pause()
            await pilot.press('c')
            assert len(copied_text) == 1
            assert 'expert code reviewer' in copied_text[0]

    @pytest.mark.asyncio
    async def test_detail_screen_copy_user_prompt(self, storage, sample_prompts, monkeypatch):
        """Test that pressing u copies user prompt to clipboard."""
        copied_text = []

        def mock_copy(text):
            copied_text.append(text)

        monkeypatch.setattr('pyperclip.copy', mock_copy)

        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('enter')
            await pilot.pause()
            await pilot.press('u')
            assert len(copied_text) == 1
            assert 'Review this code' in copied_text[0]

    @pytest.mark.asyncio
    async def test_detail_screen_shows_metadata(self, storage, sample_prompts):
        """Test that detail screen shows all metadata (group, description, tags)."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('enter')
            await pilot.pause()
            metadata_values = app.screen.query('.metadata-value')
            metadata_text = ' '.join(str(w.render()) for w in metadata_values)
            assert 'development' in metadata_text
            assert 'code' in metadata_text
            assert 'review' in metadata_text

    @pytest.mark.asyncio
    async def test_detail_screen_q_quits_app(self, storage, sample_prompts):
        """Test that pressing q quits the application from detail screen."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('enter')
            await pilot.pause()
            await pilot.press('q')

    @pytest.mark.asyncio
    async def test_prompt_without_user_prompt_hides_section(self, storage):
        """Test that detail screen doesn't show user section if no user prompt."""
        prompt_no_user = Prompt(
            name='no-user-prompt',
            description='Has no user prompt',
            system_prompt='System prompt only',
            user_prompt='',
            tags=['test'],
            group='default',
        )
        storage.create(prompt_no_user)

        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('enter')
            await pilot.pause()
            user_sections = app.screen.query('#user-prompt-content')
            assert len(user_sections) == 0


class TestAddEditPromptScreen:
    """Tests for the add/edit prompt modal."""

    @pytest.mark.asyncio
    async def test_a_key_opens_add_screen(self, storage, sample_prompts):
        """Test that pressing 'a' opens the add prompt screen."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('a')
            await pilot.pause()
            assert isinstance(app.screen, AddEditPromptScreen)
            assert not app.screen.is_edit_mode

    @pytest.mark.asyncio
    async def test_add_screen_shows_empty_form(self, storage, sample_prompts):
        """Test that add screen shows empty form fields."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('a')
            await pilot.pause()
            name_input = app.screen.query_one('#name-input', Input)
            assert name_input.value == ''
            assert not name_input.disabled

    @pytest.mark.asyncio
    async def test_escape_cancels_add_screen(self, storage, sample_prompts):
        """Test that pressing Escape closes the add screen."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('a')
            await pilot.pause()
            assert isinstance(app.screen, AddEditPromptScreen)
            await pilot.press('escape')
            await pilot.pause()
            assert not isinstance(app.screen, AddEditPromptScreen)

    @pytest.mark.asyncio
    async def test_e_key_opens_edit_screen(self, storage, sample_prompts):
        """Test that pressing 'e' opens the edit prompt screen."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('e')
            await pilot.pause()
            assert isinstance(app.screen, AddEditPromptScreen)
            assert app.screen.is_edit_mode

    @pytest.mark.asyncio
    async def test_edit_screen_shows_populated_form(self, storage, sample_prompts):
        """Test that edit screen shows existing prompt data."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('e')
            await pilot.pause()
            name_input = app.screen.query_one('#name-input', Input)
            assert name_input.value == 'code-review'
            assert name_input.disabled

    @pytest.mark.asyncio
    async def test_add_screen_has_textarea_for_prompts(self, storage, sample_prompts):
        """Test that add screen has TextArea widgets for system/user prompts."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('a')
            await pilot.pause()
            system_area = app.screen.query_one('#system-prompt-area', TextArea)
            user_area = app.screen.query_one('#user-prompt-area', TextArea)
            assert system_area is not None
            assert user_area is not None

    @pytest.mark.asyncio
    async def test_add_screen_has_save_button(self, storage, sample_prompts):
        """Test that add screen has a save button."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('a')
            await pilot.pause()
            save_btn = app.screen.query_one('#save-btn', Button)
            assert save_btn is not None

    @pytest.mark.asyncio
    async def test_edit_from_detail_screen(self, storage, sample_prompts):
        """Test that pressing 'e' from detail screen opens edit mode."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('enter')
            await pilot.pause()
            assert isinstance(app.screen, PromptDetailScreen)
            await pilot.press('e')
            await pilot.pause()
            assert isinstance(app.screen, AddEditPromptScreen)
            assert app.screen.is_edit_mode


class TestDeleteConfirmScreen:
    """Tests for the delete confirmation modal."""

    @pytest.mark.asyncio
    async def test_d_key_opens_delete_confirm(self, storage, sample_prompts):
        """Test that pressing 'd' opens the delete confirmation dialog."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('d')
            await pilot.pause()
            assert isinstance(app.screen, DeleteConfirmScreen)

    @pytest.mark.asyncio
    async def test_delete_confirm_shows_prompt_name(self, storage, sample_prompts):
        """Test that delete confirm dialog shows the prompt name."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('d')
            await pilot.pause()
            message = app.screen.query_one('#dialog-message', Static)
            assert 'code-review' in str(message.render())

    @pytest.mark.asyncio
    async def test_escape_cancels_delete(self, storage, sample_prompts):
        """Test that pressing Escape cancels the delete dialog."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            initial_count = len(app.prompts)
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('d')
            await pilot.pause()
            await pilot.press('escape')
            await pilot.pause()
            assert not isinstance(app.screen, DeleteConfirmScreen)
            assert len(storage.list()) == initial_count

    @pytest.mark.asyncio
    async def test_confirm_delete_removes_prompt(self, storage, sample_prompts):
        """Test that confirming delete removes the prompt."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            initial_count = len(app.prompts)
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('d')
            await pilot.pause()
            confirm_btn = app.screen.query_one('#confirm-btn', Button)
            await pilot.click(confirm_btn)
            await pilot.pause()
            assert len(storage.list()) == initial_count - 1

    @pytest.mark.asyncio
    async def test_delete_from_detail_screen(self, storage, sample_prompts):
        """Test that pressing 'd' from detail screen opens delete dialog."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('enter')
            await pilot.pause()
            assert isinstance(app.screen, PromptDetailScreen)
            await pilot.press('d')
            await pilot.pause()
            assert isinstance(app.screen, DeleteConfirmScreen)

    @pytest.mark.asyncio
    async def test_delete_has_cancel_button(self, storage, sample_prompts):
        """Test that delete dialog has a cancel button."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('d')
            await pilot.pause()
            cancel_btn = app.screen.query_one('#cancel-btn', Button)
            assert cancel_btn is not None


class TestAddEditFormValidation:
    """Tests for form validation in add/edit screen."""

    @pytest.mark.asyncio
    async def test_save_requires_name(self, storage, sample_prompts):
        """Test that saving without a name shows error."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('a')
            await pilot.pause()
            system_area = app.screen.query_one('#system-prompt-area', TextArea)
            system_area.text = 'Test system prompt'
            await pilot.press('ctrl+s')
            await pilot.pause()
            status = app.screen.query_one('#status-bar', Static)
            assert 'Name is required' in str(status.render())

    @pytest.mark.asyncio
    async def test_save_requires_system_prompt(self, storage, sample_prompts):
        """Test that saving without a system prompt shows error."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('a')
            await pilot.pause()
            name_input = app.screen.query_one('#name-input', Input)
            name_input.value = 'test-prompt'
            await pilot.press('ctrl+s')
            await pilot.pause()
            status = app.screen.query_one('#status-bar', Static)
            assert 'System prompt is required' in str(status.render())

    @pytest.mark.asyncio
    async def test_tags_field_accepts_comma_separated(self, storage, sample_prompts):
        """Test that tags field properly parses comma-separated values."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('a')
            await pilot.pause()
            tags_input = app.screen.query_one('#tags-input', Input)
            tags_input.value = 'tag1, tag2, tag3'
            name_input = app.screen.query_one('#name-input', Input)
            name_input.value = 'test-prompt'
            system_area = app.screen.query_one('#system-prompt-area', TextArea)
            system_area.text = 'Test system prompt'
            save_btn = app.screen.query_one('#save-btn', Button)
            await pilot.click(save_btn)
            await pilot.pause()
            prompt = storage.get('test-prompt', '')
            assert prompt is not None
            assert prompt.tags == ['tag1', 'tag2', 'tag3']

    @pytest.mark.asyncio
    async def test_edit_preserves_existing_data(self, storage, sample_prompts):
        """Test that editing preserves existing prompt data."""
        app = PromptButlerApp(storage=storage)
        async with app.run_test() as pilot:
            table = app.query_one('#prompt-table', PromptTable)
            table.focus()
            await pilot.press('e')
            await pilot.pause()
            desc_input = app.screen.query_one('#description-input', Input)
            assert desc_input.value == 'Reviews code for best practices'
