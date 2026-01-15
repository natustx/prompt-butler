"""Prompt Butler TUI Application using Textual framework."""

from __future__ import annotations

from rapidfuzz import fuzz
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Label, ListItem, ListView, Static

from prompt_butler.models import Prompt
from prompt_butler.services.storage import PromptStorage


class FilterSidebar(Vertical):
    """Sidebar for filtering prompts by tags and groups."""

    DEFAULT_CSS = """
    FilterSidebar {
        width: 25;
        border: solid $primary;
        background: $surface;
        padding: 1;
    }

    FilterSidebar Label {
        text-style: bold;
        color: $warning;
        margin-bottom: 1;
    }

    FilterSidebar .section-label {
        margin-top: 1;
    }

    FilterSidebar ListView {
        height: auto;
        max-height: 10;
        background: $surface;
    }

    FilterSidebar ListItem {
        padding: 0 1;
    }

    FilterSidebar ListItem:hover {
        background: $primary-darken-2;
    }

    FilterSidebar .filter-item {
        color: $success;
    }

    FilterSidebar .active-filter {
        background: $primary;
        color: $text;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.groups: list[str] = []
        self.tags: list[str] = []

    def compose(self) -> ComposeResult:
        yield Label('Filters', classes='header-label')
        yield Label('Groups', classes='section-label')
        yield ListView(id='group-list')
        yield Label('Tags', classes='section-label')
        yield ListView(id='tag-list')

    def set_filters(self, groups: list[str], tags: list[str]) -> None:
        """Set filter lists with groups and tags."""
        self.groups = groups
        self.tags = tags

        import time

        ts = int(time.time() * 1000)

        group_list = self.query_one('#group-list', ListView)
        group_list.clear()
        for i, g in enumerate(['All', *groups]):
            group_list.append(ListItem(Static(g, classes='filter-item'), id=f'group-{ts}-{i}-{g}'))

        tag_list = self.query_one('#tag-list', ListView)
        tag_list.clear()
        for i, t in enumerate(['All', *tags]):
            tag_list.append(ListItem(Static(t, classes='filter-item'), id=f'tag-{ts}-{i}-{t}'))


class PromptDetailPanel(Vertical):
    """Panel showing prompt details."""

    DEFAULT_CSS = """
    PromptDetailPanel {
        height: auto;
        max-height: 15;
        border: solid $primary;
        background: $surface;
        padding: 1;
        margin-top: 1;
    }

    PromptDetailPanel .detail-label {
        color: $warning;
        text-style: bold;
    }

    PromptDetailPanel .detail-value {
        color: $success;
        margin-bottom: 1;
    }

    PromptDetailPanel .prompt-content {
        color: $text;
        max-height: 5;
        overflow: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label('Prompt Details', classes='detail-label')
        yield Static('Select a prompt to view details', id='detail-content')

    def show_prompt(self, prompt: Prompt | None) -> None:
        """Display prompt details."""
        content = self.query_one('#detail-content', Static)
        if prompt is None:
            content.update('Select a prompt to view details')
            return

        detail_text = (
            f'[bold yellow]Name:[/] [green]{prompt.name}[/]\n'
            f'[bold yellow]Group:[/] [blue]{prompt.group}[/]\n'
            f'[bold yellow]Description:[/] {prompt.description}\n'
            f'[bold yellow]Tags:[/] [green]{", ".join(prompt.tags) or "None"}[/]\n'
            f'[bold yellow]System Prompt:[/]\n{prompt.system_prompt[:200]}'
            f'{"..." if len(prompt.system_prompt) > 200 else ""}'
        )
        content.update(detail_text)


class PromptDetailScreen(Screen):
    """Full-screen detail view for a single prompt."""

    DEFAULT_CSS = """
    PromptDetailScreen {
        background: $background;
    }

    PromptDetailScreen #detail-header {
        dock: top;
        height: 3;
        background: $primary-darken-2;
        padding: 0 2;
        content-align: left middle;
    }

    PromptDetailScreen #detail-header-text {
        color: $warning;
        text-style: bold;
    }

    PromptDetailScreen #detail-scroll {
        padding: 1 2;
    }

    PromptDetailScreen .section-header {
        color: $warning;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
    }

    PromptDetailScreen .metadata-section {
        background: $surface;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }

    PromptDetailScreen .metadata-label {
        color: $warning;
        text-style: bold;
    }

    PromptDetailScreen .metadata-value {
        color: $success;
    }

    PromptDetailScreen .prompt-section {
        background: $surface;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }

    PromptDetailScreen .prompt-content {
        color: $text;
    }

    PromptDetailScreen #status-bar {
        dock: bottom;
        height: 1;
        background: $primary-darken-2;
        color: $text;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding('escape', 'go_back', 'Back', show=True),
        Binding('c', 'copy_system', 'Copy System', show=True),
        Binding('u', 'copy_user', 'Copy User', show=True),
        Binding('q', 'quit', 'Quit', show=True),
    ]

    def __init__(self, prompt: Prompt, **kwargs) -> None:
        super().__init__(**kwargs)
        self.prompt = prompt

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id='detail-header'):
            yield Static(f'Prompt: {self.prompt.name}', id='detail-header-text')
        with VerticalScroll(id='detail-scroll'):
            with Vertical(classes='metadata-section'):
                yield Static('[bold yellow]Name:[/]', classes='metadata-label')
                yield Static(f'[green]{self.prompt.name}[/]', classes='metadata-value')
                yield Static('[bold yellow]Group:[/]', classes='metadata-label')
                yield Static(f'[blue]{self.prompt.group}[/]', classes='metadata-value')
                yield Static('[bold yellow]Description:[/]', classes='metadata-label')
                yield Static(self.prompt.description or '(none)', classes='metadata-value')
                yield Static('[bold yellow]Tags:[/]', classes='metadata-label')
                yield Static(
                    f'[green]{", ".join(self.prompt.tags) or "(none)"}[/]',
                    classes='metadata-value',
                )
            yield Static('SYSTEM PROMPT', classes='section-header')
            with Vertical(classes='prompt-section'):
                system_content = self.prompt.system_prompt or '(empty)'
                yield Static(system_content, classes='prompt-content', id='system-prompt-content')
            if self.prompt.user_prompt:
                yield Static('USER PROMPT', classes='section-header')
                with Vertical(classes='prompt-section'):
                    yield Static(self.prompt.user_prompt, classes='prompt-content', id='user-prompt-content')
        yield Static('Press c to copy system prompt, u to copy user prompt, Esc to go back', id='status-bar')
        yield Footer()

    def action_go_back(self) -> None:
        """Return to the list view."""
        self.app.pop_screen()

    def action_copy_system(self) -> None:
        """Copy the system prompt to clipboard."""
        try:
            import pyperclip

            pyperclip.copy(self.prompt.system_prompt)
            self._update_status(f'Copied system prompt for "{self.prompt.name}" to clipboard')
        except Exception as e:
            self._update_status(f'Failed to copy: {e}')

    def action_copy_user(self) -> None:
        """Copy the user prompt to clipboard."""
        if not self.prompt.user_prompt:
            self._update_status('No user prompt to copy')
            return
        try:
            import pyperclip

            pyperclip.copy(self.prompt.user_prompt)
            self._update_status(f'Copied user prompt for "{self.prompt.name}" to clipboard')
        except Exception as e:
            self._update_status(f'Failed to copy: {e}')

    def _update_status(self, message: str) -> None:
        """Update the status bar."""
        status = self.query_one('#status-bar', Static)
        status.update(message)


class SearchInput(Input):
    """Search input with fuzzy matching."""

    DEFAULT_CSS = """
    SearchInput {
        dock: top;
        height: 3;
        border: solid $primary;
        background: $surface;
        display: none;
    }

    SearchInput:focus {
        border: solid $warning;
    }

    SearchInput.visible {
        display: block;
    }
    """


class PromptTable(DataTable):
    """Data table for displaying prompts with vim-style navigation."""

    DEFAULT_CSS = """
    PromptTable {
        height: 1fr;
        border: solid $primary;
    }

    PromptTable > .datatable--header {
        background: $primary-darken-2;
        color: $warning;
        text-style: bold;
    }

    PromptTable > .datatable--cursor {
        background: $primary;
        color: $text;
    }

    PromptTable > .datatable--hover {
        background: $primary-darken-1;
    }
    """


class PromptButlerApp(App):
    """Main TUI application for Prompt Butler."""

    CSS = """
    Screen {
        background: $background;
    }

    Header {
        background: $primary-darken-3;
        color: $warning;
    }

    Footer {
        background: $primary-darken-3;
    }

    #main-container {
        height: 1fr;
    }

    #content-area {
        height: 1fr;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $primary-darken-2;
        color: $text;
        padding: 0 1;
    }
    """

    TITLE = 'Prompt Butler'
    SUB_TITLE = 'AI Prompt Manager'

    BINDINGS = [
        Binding('q', 'quit', 'Quit', show=True),
        Binding('/', 'search', 'Search', show=True),
        Binding('escape', 'clear_search', 'Clear', show=True),
        Binding('j', 'cursor_down', 'Down', show=False),
        Binding('k', 'cursor_up', 'Up', show=False),
        Binding('enter', 'select_row', 'Select', show=True),
        Binding('c', 'copy_prompt', 'Copy', show=True),
        Binding('r', 'refresh', 'Refresh', show=True),
        Binding('tab', 'focus_next', 'Next', show=False),
        Binding('shift+tab', 'focus_previous', 'Prev', show=False),
    ]

    def __init__(self, storage: PromptStorage | None = None) -> None:
        super().__init__()
        self.storage = storage or PromptStorage()
        self.prompts: list[Prompt] = []
        self.filtered_prompts: list[Prompt] = []
        self.active_group_filter: str | None = None
        self.active_tag_filter: str | None = None
        self.search_query: str = ''

    def compose(self) -> ComposeResult:
        yield Header()
        yield SearchInput(placeholder='Type to search (fuzzy match)...', id='search-input')
        with Horizontal(id='main-container'):
            yield FilterSidebar(id='sidebar')
            with Vertical(id='content-area'):
                yield PromptTable(id='prompt-table', cursor_type='row')
                yield PromptDetailPanel(id='detail-panel')
        yield Static('Ready', id='status-bar')
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the application on mount."""
        self.load_prompts()
        self.setup_table()
        self.update_sidebar()

    def load_prompts(self) -> None:
        """Load prompts from storage."""
        self.prompts = self.storage.list()
        self.filtered_prompts = self.prompts.copy()

    def setup_table(self) -> None:
        """Set up the data table with columns."""
        table = self.query_one('#prompt-table', PromptTable)
        table.add_columns('Name', 'Group', 'Description', 'Tags')
        self.refresh_table()

    def refresh_table(self) -> None:
        """Refresh the table with current filtered prompts."""
        table = self.query_one('#prompt-table', PromptTable)
        table.clear()

        for prompt in self.filtered_prompts:
            desc = prompt.description[:40] + '...' if len(prompt.description) > 40 else prompt.description
            tags = ', '.join(prompt.tags[:3])
            if len(prompt.tags) > 3:
                tags += '...'
            table.add_row(prompt.name, prompt.group, desc, tags, key=prompt.name)

        self.update_status(f'{len(self.filtered_prompts)} prompts')

    def update_sidebar(self) -> None:
        """Update sidebar with available groups and tags."""
        groups = self.storage.list_groups()
        tags = list(self.storage.list_all_tags().keys())

        sidebar = self.query_one('#sidebar', FilterSidebar)
        sidebar.set_filters(groups, tags)

    def update_status(self, message: str) -> None:
        """Update the status bar."""
        status = self.query_one('#status-bar', Static)
        status.update(message)

    def apply_filters(self) -> None:
        """Apply all active filters to the prompt list."""
        self.filtered_prompts = self.prompts.copy()

        if self.active_group_filter and self.active_group_filter != 'All':
            self.filtered_prompts = [p for p in self.filtered_prompts if p.group == self.active_group_filter]

        if self.active_tag_filter and self.active_tag_filter != 'All':
            self.filtered_prompts = [p for p in self.filtered_prompts if self.active_tag_filter in p.tags]

        if self.search_query:
            self.filtered_prompts = self._fuzzy_filter(self.search_query)

        self.refresh_table()

    def _fuzzy_filter(self, query: str) -> list[Prompt]:
        """Filter prompts using fuzzy matching with rapidfuzz."""
        results = []
        for prompt in self.filtered_prompts:
            searchable = f'{prompt.name} {prompt.description} {" ".join(prompt.tags)}'
            score = fuzz.partial_ratio(query.lower(), searchable.lower())
            if score >= 50:
                results.append((score, prompt))
        results.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in results]

    def action_search(self) -> None:
        """Show search input."""
        search_input = self.query_one('#search-input', SearchInput)
        search_input.add_class('visible')
        search_input.focus()

    def action_clear_search(self) -> None:
        """Clear search and hide input."""
        search_input = self.query_one('#search-input', SearchInput)
        search_input.remove_class('visible')
        search_input.value = ''
        self.search_query = ''
        self.apply_filters()
        self.query_one('#prompt-table', PromptTable).focus()

    def action_cursor_down(self) -> None:
        """Move cursor down in the table (vim j key)."""
        table = self.query_one('#prompt-table', PromptTable)
        if table.has_focus:
            table.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in the table (vim k key)."""
        table = self.query_one('#prompt-table', PromptTable)
        if table.has_focus:
            table.action_cursor_up()

    def action_select_row(self) -> None:
        """Forward select action to the data table."""
        table = self.query_one('#prompt-table', PromptTable)
        if table.has_focus:
            table.action_select_cursor()

    def action_copy_prompt(self) -> None:
        """Copy the selected prompt's system prompt to clipboard."""
        table = self.query_one('#prompt-table', PromptTable)
        if table.cursor_row is not None and self.filtered_prompts:
            row_key = table.get_row_at(table.cursor_row)
            if row_key:
                prompt_name = str(row_key[0])
                prompt = next((p for p in self.filtered_prompts if p.name == prompt_name), None)
                if prompt:
                    try:
                        import pyperclip

                        pyperclip.copy(prompt.system_prompt)
                        self.update_status(f'Copied "{prompt.name}" to clipboard')
                    except Exception as e:
                        self.update_status(f'Failed to copy: {e}')

    def action_refresh(self) -> None:
        """Refresh prompts from storage."""
        self.load_prompts()
        self.update_sidebar()
        self.apply_filters()
        self.update_status('Refreshed')

    @on(Input.Changed, '#search-input')
    def on_search_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        self.search_query = event.value
        self.apply_filters()

    @on(Input.Submitted, '#search-input')
    def on_search_submitted(self, event: Input.Submitted) -> None:
        """Handle search submission (Enter key)."""
        self.query_one('#prompt-table', PromptTable).focus()

    @on(ListView.Selected, '#group-list')
    def on_group_selected(self, event: ListView.Selected) -> None:
        """Handle group filter selection."""
        if event.item.id:
            parts = event.item.id.split('-', 3)
            if len(parts) >= 4:
                group = parts[3]
                self.active_group_filter = None if group == 'All' else group
                self.apply_filters()
                self.update_status(f'Filter: group={group}')

    @on(ListView.Selected, '#tag-list')
    def on_tag_selected(self, event: ListView.Selected) -> None:
        """Handle tag filter selection."""
        if event.item.id:
            parts = event.item.id.split('-', 3)
            if len(parts) >= 4:
                tag = parts[3]
                self.active_tag_filter = None if tag == 'All' else tag
                self.apply_filters()
                self.update_status(f'Filter: tag={tag}')

    @on(DataTable.RowHighlighted, '#prompt-table')
    def on_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row highlight changes to update detail panel."""
        if event.row_key and self.filtered_prompts:
            prompt_name = str(event.row_key.value)
            prompt = next((p for p in self.filtered_prompts if p.name == prompt_name), None)
            if prompt:
                detail_panel = self.query_one('#detail-panel', PromptDetailPanel)
                detail_panel.show_prompt(prompt)

    @on(DataTable.RowSelected, '#prompt-table')
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection (Enter) to open full detail screen."""
        if event.row_key and self.filtered_prompts:
            prompt_name = str(event.row_key.value)
            prompt = next((p for p in self.filtered_prompts if p.name == prompt_name), None)
            if prompt:
                self.push_screen(PromptDetailScreen(prompt))


def run_tui(storage: PromptStorage | None = None) -> None:
    """Run the TUI application."""
    app = PromptButlerApp(storage=storage)
    app.run()
