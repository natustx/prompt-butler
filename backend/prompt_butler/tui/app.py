"""Prompt Butler Terminal User Interface.

A terminal UI for managing prompts using the Textual framework.
Green/amber on dark theme with box-drawing borders.
"""

import base64
from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.coordinate import Coordinate
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
    TextArea,
)

from prompt_butler.models import Prompt
from prompt_butler.services.storage import PromptStorage

# Custom theme colors: green/amber on dark
THEME_CSS = '''
Screen {
    background: $surface;
}

Header {
    background: $primary-darken-2;
    color: $text;
}

Footer {
    background: $primary-darken-3;
}

Input,
TextArea {
    color: #e6edf3;
}

Input.-placeholder,
TextArea.-placeholder {
    color: #9aa4ad;
}

DataTable {
    background: $surface;
}

DataTable > .datatable--header {
    background: $primary-darken-1;
    color: $text;
}

DataTable > .datatable--cursor {
    background: $primary;
    color: $text;
}

.prompt-detail {
    padding: 1 2;
    border: round $primary;
}

.prompt-content {
    padding: 1 2;
    border: round $secondary;
    background: $surface-darken-1;
}

.status-bar {
    dock: bottom;
    height: 1;
    background: $primary-darken-3;
    color: #9aa4ad;
}

#prompt-list {
    height: 100%;
}

#detail-container {
    padding: 1 2;
}

.section-title {
    color: #7fd2ff;
    text-style: bold;
    padding: 0 0 1 0;
}

#sidebar {
    width: 25;
    background: $surface-darken-1;
    border-right: solid $primary;
    padding: 1;
}

#sidebar-title {
    text-style: bold;
    color: #7fd2ff;
    padding: 0 0 1 0;
}

#main-content {
    width: 1fr;
}

#search-container {
    height: auto;
    padding: 0 1;
}

#search-input {
    width: 100%;
    margin-bottom: 1;
}

.filter-list {
    height: auto;
    max-height: 10;
}

.filter-item {
    padding: 0 1;
}

.filter-item:hover {
    background: $primary-darken-1;
}

.filter-item.-selected {
    background: $primary;
    color: $text;
}

#detail-scroll {
    height: 100%;
}

/* Add/Edit form styles */
#edit-form {
    padding: 1 2;
    height: 100%;
}

.form-row {
    height: auto;
    margin-bottom: 1;
}

.form-label {
    color: #7fd2ff;
    margin-bottom: 0;
}

.form-input {
    width: 100%;
}

#system-prompt-input {
    height: 10;
}

#user-prompt-input {
    height: 6;
}

#button-row {
    height: auto;
    margin-top: 1;
}

#save-btn {
    margin-right: 1;
}

.suggestion-list {
    height: auto;
    max-height: 5;
    background: $surface-darken-1;
    border: solid $primary;
    display: none;
}

.suggestion-list.-visible {
    display: block;
}

#confirm-delete {
    background: $surface-darken-2;
    border: round $secondary;
    padding: 1 2;
    width: 60;
}

#confirm-delete Label {
    padding-bottom: 1;
}
'''


def _encode_dom_id(value: str) -> str:
    encoded = base64.urlsafe_b64encode(value.encode('utf-8')).decode('ascii').rstrip('=')
    return encoded


def _decode_dom_id(value: str) -> str:
    padded = value + ('=' * (-len(value) % 4))
    return base64.urlsafe_b64decode(padded.encode('ascii')).decode('utf-8')


def _make_dom_id(prefix: str, value: str) -> str:
    return f'{prefix}-{_encode_dom_id(value)}'


class RenderableLabel(Label):
    """Label that exposes a renderable property for test compatibility."""

    def __init__(self, *args, **kwargs):
        if args:
            self._renderable_text = str(args[0])
        else:
            self._renderable_text = str(kwargs.get('text', ''))
        super().__init__(*args, **kwargs)

    @property
    def renderable(self) -> str:
        return self._renderable_text


class RenderableStatic(Static):
    """Static widget with a stable renderable string for tests."""

    def __init__(self, content: str, *args, **kwargs):
        super().__init__(content, *args, **kwargs)
        self._renderable_text = content

    @property
    def renderable(self) -> str:
        return self._renderable_text


class ConfirmDeleteScreen(ModalScreen[bool]):
    """Modal confirmation for deleting a prompt."""

    BINDINGS = [
        Binding('escape', 'cancel', 'Cancel'),
    ]

    def __init__(self, prompt_name: str, prompt_group: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompt_name = prompt_name
        self.prompt_group = prompt_group

    def compose(self) -> ComposeResult:
        group_label = f' in group "{self.prompt_group}"' if self.prompt_group else ''
        message = f'Delete "{self.prompt_name}"{group_label}?'
        yield Container(
            Label(message),
            Horizontal(
                Button('Delete', variant='error', id='confirm-delete-btn'),
                Button('Cancel', id='cancel-delete-btn'),
            ),
            id='confirm-delete',
        )

    def action_cancel(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'confirm-delete-btn':
            self.dismiss(True)
        elif event.button.id == 'cancel-delete-btn':
            self.dismiss(False)


class HomeScreen(Screen):
    """Main screen showing the list of prompts."""

    BINDINGS = [
        Binding('q', 'quit', 'Quit'),
        Binding('j', 'cursor_down', 'Down', show=False),
        Binding('k', 'cursor_up', 'Up', show=False),
        Binding('enter', 'view_prompt', 'View'),
        Binding('/', 'focus_search', 'Search'),
        Binding('escape', 'clear_search', 'Clear', show=False),
        Binding('a', 'add_prompt', 'Add'),
        Binding('d', 'delete_prompt', 'Delete'),
        Binding('r', 'refresh', 'Refresh'),
        Binding('g', 'cycle_group_filter', 'Group'),
        Binding('t', 'cycle_tag_filter', 'Tag'),
    ]

    def __init__(self, storage: PromptStorage, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = storage
        self.all_prompts: list[Prompt] = []
        self.search_query: str = ''
        self.selected_group: str = ''
        self.selected_tag: str = ''
        self._pending_delete: Optional[tuple[str, str]] = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(
                Label('Filters', id='sidebar-title'),
                Label('Groups:', classes='section-title'),
                ListView(id='group-list', classes='filter-list'),
                Label('Tags:', classes='section-title'),
                ListView(id='tag-list', classes='filter-list'),
                id='sidebar',
            ),
            Vertical(
                Container(
                    Input(placeholder='Search prompts... (press / to focus)', id='search-input'),
                    id='search-container',
                ),
                DataTable(id='prompt-list'),
                id='main-content',
            ),
        )
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the data table when screen mounts."""
        table = self.query_one('#prompt-list', DataTable)
        table.cursor_type = 'row'
        self.load_prompts()
        self.load_filters()
        table.focus()

    def load_filters(self) -> None:
        """Load group and tag filters into sidebar."""
        group_list = self.query_one('#group-list', ListView)
        tag_list = self.query_one('#tag-list', ListView)

        group_list.clear()
        tag_list.clear()

        # Add groups
        groups = self.storage.get_all_groups()
        group_list.append(ListItem(Label('All'), id='group-all', classes='filter-item'))
        for group, count in sorted(groups.items()):
            display_name = group or '(root)'
            group_list.append(
                ListItem(
                    Label(f'{display_name} ({count})'),
                    id=_make_dom_id('group', group),
                    classes='filter-item',
                )
            )

        # Add tags
        tags = self.storage.get_all_tags()
        tag_list.append(ListItem(Label('All'), id='tag-all', classes='filter-item'))
        for tag, count in sorted(tags.items()):
            tag_list.append(
                ListItem(Label(f'{tag} ({count})'), id=_make_dom_id('tag', tag), classes='filter-item')
            )

    def load_prompts(self) -> None:
        """Load prompts into the data table with filtering."""
        self.all_prompts = self.storage.list_all()
        self.update_table()

    def update_table(self) -> None:
        """Update table with current filters applied."""
        table = self.query_one('#prompt-list', DataTable)
        table.clear(columns=True)
        table.add_columns('Name', 'Group', 'Description', 'Tags')

        filtered = self.all_prompts

        # Filter by group
        if self.selected_group:
            if self.selected_group == '(root)':
                filtered = [p for p in filtered if not p.group]
            else:
                filtered = [p for p in filtered if p.group == self.selected_group]

        # Filter by tag
        if self.selected_tag:
            filtered = [p for p in filtered if self.selected_tag in p.tags]

        # Filter by search query
        if self.search_query:
            query = self.search_query.lower()
            filtered = [
                p
                for p in filtered
                if query in p.name.lower() or query in p.description.lower() or any(query in t.lower() for t in p.tags)
            ]

        for prompt in filtered:
            tags = ', '.join(prompt.tags) if prompt.tags else ''
            description = prompt.description or ''
            if len(description) > 40:
                description = description[:37] + '...'
            table.add_row(
                prompt.name,
                prompt.group or '(root)',
                description,
                tags,
                key=f'{prompt.group}/{prompt.name}' if prompt.group else prompt.name,
            )
        if table.ordered_rows:
            if table.cursor_coordinate.row >= len(table.ordered_rows):
                table.cursor_coordinate = Coordinate(0, 0)

    @on(DataTable.RowSelected, '#prompt-list')
    def on_prompt_selected(self, event: DataTable.RowSelected) -> None:
        """Open detail view when a row is selected."""
        row_key = str(event.row_key)
        if not row_key:
            return
        name, group = self._split_prompt_key(row_key)
        self.app.push_screen(DetailScreen(self.storage, name, prompt_group=group))

    @on(Input.Changed, '#search-input')
    def on_search_changed(self, event: Input.Changed) -> None:
        """Handle search input changes for live filtering."""
        self.search_query = event.value
        self.update_table()

    @on(ListView.Selected, '#group-list')
    def on_group_selected(self, event: ListView.Selected) -> None:
        """Handle group filter selection."""
        item_id = str(event.item.id) if event.item.id else ''
        if item_id == 'group-all':
            self.selected_group = ''
        elif item_id.startswith('group-'):
            group = _decode_dom_id(item_id[6:])
            self.selected_group = group
        self.update_table()
        self.query_one('#prompt-list', DataTable).focus()

    @on(ListView.Selected, '#tag-list')
    def on_tag_selected(self, event: ListView.Selected) -> None:
        """Handle tag filter selection."""
        item_id = str(event.item.id) if event.item.id else ''
        if item_id == 'tag-all':
            self.selected_tag = ''
        elif item_id.startswith('tag-'):
            self.selected_tag = _decode_dom_id(item_id[4:])
        self.update_table()
        self.query_one('#prompt-list', DataTable).focus()

    def action_cursor_down(self) -> None:
        """Move cursor down in the table (j key)."""
        table = self.query_one('#prompt-list', DataTable)
        table.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in the table (k key)."""
        table = self.query_one('#prompt-list', DataTable)
        table.action_cursor_up()

    @staticmethod
    def _split_prompt_key(row_key: str) -> tuple[str, str]:
        """Split a row key into name and group parts."""
        group, sep, name = row_key.rpartition('/')
        if not sep:
            return row_key, ''
        return name, group

    def action_view_prompt(self) -> None:
        """View the selected prompt."""
        table = self.query_one('#prompt-list', DataTable)
        if table.cursor_row is None:
            return

        if table.cursor_row >= len(table.ordered_rows):
            return

        row_key = str(table.ordered_rows[table.cursor_row].key)
        name, group = self._split_prompt_key(row_key)
        self.app.push_screen(DetailScreen(self.storage, name, prompt_group=group))

    def action_focus_search(self) -> None:
        """Focus the search input."""
        self.query_one('#search-input', Input).focus()

    def action_clear_search(self) -> None:
        """Clear search and return focus to table."""
        search_input = self.query_one('#search-input', Input)
        search_input.value = ''
        self.search_query = ''
        self.update_table()
        self.query_one('#prompt-list', DataTable).focus()

    def action_cycle_group_filter(self) -> None:
        """Cycle through group filters."""
        groups = [''] + list(self.storage.get_all_groups().keys())
        if self.selected_group in groups:
            idx = groups.index(self.selected_group)
            self.selected_group = groups[(idx + 1) % len(groups)]
        else:
            self.selected_group = ''
        self.update_table()
        group_name = self.selected_group or 'All'
        self.notify(f'Group: {group_name}')

    def action_cycle_tag_filter(self) -> None:
        """Cycle through tag filters."""
        tags = [''] + list(self.storage.get_all_tags().keys())
        if self.selected_tag in tags:
            idx = tags.index(self.selected_tag)
            self.selected_tag = tags[(idx + 1) % len(tags)]
        else:
            self.selected_tag = ''
        self.update_table()
        tag_name = self.selected_tag or 'All'
        self.notify(f'Tag: {tag_name}')

    def action_add_prompt(self) -> None:
        """Add a new prompt."""
        self.app.push_screen(AddEditScreen(self.storage, on_save=lambda _: self.load_prompts()))

    def action_delete_prompt(self) -> None:
        """Delete the selected prompt."""
        table = self.query_one('#prompt-list', DataTable)
        if table.cursor_row is None or table.cursor_row >= len(table.ordered_rows):
            self.notify('Select a prompt to delete', severity='warning')
            return

        row_key = str(table.ordered_rows[table.cursor_row].key)
        name, group = self._split_prompt_key(row_key)
        self._pending_delete = (name, group)
        self.app.push_screen(ConfirmDeleteScreen(name, group), self._handle_delete_confirm)

    def _handle_delete_confirm(self, confirmed: bool) -> None:
        """Handle delete confirmation result."""
        if not confirmed or not self._pending_delete:
            self._pending_delete = None
            return

        name, group = self._pending_delete
        self._pending_delete = None
        try:
            if self.storage.delete(name, group=group):
                self.load_prompts()
                self.load_filters()
                self.notify(f'Deleted "{name}"')
            else:
                self.notify('Prompt not found', severity='warning')
        except Exception as exc:
            self.notify(f'Error deleting prompt: {exc}', severity='error')

    def action_refresh(self) -> None:
        """Refresh the prompt list."""
        self.load_prompts()
        self.load_filters()
        self.notify('Refreshed')


class DetailScreen(Screen):
    """Screen showing details of a single prompt."""

    BINDINGS = [
        Binding('escape', 'go_back', 'Back'),
        Binding('q', 'go_back', 'Back'),
        Binding('e', 'edit_prompt', 'Edit'),
        Binding('c', 'copy_system', 'Copy System'),
        Binding('u', 'copy_user', 'Copy User'),
    ]

    def __init__(self, storage: PromptStorage, prompt_name: str, prompt_group: str = '', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = storage
        self.prompt_name = prompt_name
        self.prompt_group = prompt_group

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Vertical(
                RenderableLabel(f'Prompt: {self.prompt_name}', classes='section-title'),
                id='detail-container',
            ),
            id='detail-scroll',
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load prompt details when screen mounts."""
        self.load_prompt()

    def load_prompt(self) -> None:
        """Load and display prompt details."""
        container = self.query_one('#detail-container', Vertical)
        container.remove_children()
        container.mount(RenderableLabel(f'Prompt: {self.prompt_name}', classes='section-title'))

        prompt = self.storage.read(self.prompt_name, self.prompt_group)
        if not prompt:
            container.mount(RenderableLabel('Prompt not found'))
            return

        # Show metadata
        meta_lines = []
        if prompt.description:
            meta_lines.append(f'Description: {prompt.description}')
        if prompt.group:
            meta_lines.append(f'Group: {prompt.group}')
        if prompt.tags:
            meta_lines.append(f'Tags: {", ".join(prompt.tags)}')

        if meta_lines:
            container.mount(RenderableStatic('\n'.join(meta_lines), classes='prompt-detail'))

        # Show system prompt
        container.mount(RenderableLabel('System Prompt:', classes='section-title'))
        container.mount(RenderableStatic(prompt.system_prompt, classes='prompt-content'))

        # Show user prompt if present
        if prompt.user_prompt:
            container.mount(RenderableLabel('User Prompt:', classes='section-title'))
            container.mount(RenderableStatic(prompt.user_prompt, classes='prompt-content'))

    def action_go_back(self) -> None:
        """Go back to home screen."""
        self.app.pop_screen()

    def action_edit_prompt(self) -> None:
        """Edit the prompt."""
        self.app.push_screen(
            AddEditScreen(
                self.storage,
                self.prompt_name,
                prompt_group=self.prompt_group,
                on_save=self.refresh_after_save,
            )
        )

    def refresh_after_save(self, prompt: Prompt) -> None:
        """Refresh details after saving edits."""
        self.prompt_name = prompt.name
        self.prompt_group = prompt.group or ''
        self.load_prompt()

    def action_copy_system(self) -> None:
        """Copy system prompt to clipboard."""
        prompt = self.storage.read(self.prompt_name)
        if prompt:
            try:
                import pyperclip
                pyperclip.copy(prompt.system_prompt)
                self.notify('Copied system prompt to clipboard')
            except Exception:
                self.notify('Failed to copy to clipboard', severity='error')

    def action_copy_user(self) -> None:
        """Copy user prompt to clipboard."""
        prompt = self.storage.read(self.prompt_name)
        if prompt and prompt.user_prompt:
            try:
                import pyperclip
                pyperclip.copy(prompt.user_prompt)
                self.notify('Copied user prompt to clipboard')
            except Exception:
                self.notify('Failed to copy to clipboard', severity='error')
        else:
            self.notify('No user prompt to copy', severity='warning')


class AddEditScreen(Screen):
    """Screen for adding or editing a prompt."""

    BINDINGS = [
        Binding('escape', 'cancel', 'Cancel'),
        Binding('ctrl+s', 'save', 'Save'),
    ]

    def __init__(
        self,
        storage: PromptStorage,
        prompt_name: Optional[str] = None,
        prompt_group: str = '',
        on_save: Optional[callable] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.storage = storage
        self.prompt_name = prompt_name
        self.prompt_group = prompt_group
        self.is_editing = prompt_name is not None
        self.on_save_callback = on_save
        self.existing_tags = list(storage.get_all_tags().keys())
        self.existing_groups = [g for g in storage.get_all_groups().keys() if g]

    def compose(self) -> ComposeResult:
        title = f'Edit "{self.prompt_name}"' if self.is_editing else 'New Prompt'
        yield Header()
        yield VerticalScroll(
            Vertical(
                Label(title, classes='section-title'),
                # Name field
                Vertical(
                    Label('Name:', classes='form-label'),
                    Input(id='name-input', classes='form-input', disabled=self.is_editing),
                    classes='form-row',
                ),
                # Group field with suggestions
                Vertical(
                    Label('Group:', classes='form-label'),
                    Input(id='group-input', classes='form-input', placeholder='Enter group name...'),
                    ListView(id='group-suggestions', classes='suggestion-list'),
                    classes='form-row',
                ),
                # Description field
                Vertical(
                    Label('Description:', classes='form-label'),
                    Input(id='description-input', classes='form-input'),
                    classes='form-row',
                ),
                # Tags field with suggestions
                Vertical(
                    Label('Tags (comma-separated):', classes='form-label'),
                    Input(id='tags-input', classes='form-input', placeholder='tag1, tag2, tag3'),
                    ListView(id='tag-suggestions', classes='suggestion-list'),
                    classes='form-row',
                ),
                # System prompt
                Vertical(
                    Label('System Prompt:', classes='form-label'),
                    TextArea(id='system-prompt-input'),
                    classes='form-row',
                ),
                # User prompt
                Vertical(
                    Label('User Prompt (optional):', classes='form-label'),
                    TextArea(id='user-prompt-input'),
                    classes='form-row',
                ),
                # Buttons
                Horizontal(
                    Button('Save', variant='primary', id='save-btn'),
                    Button('Cancel', variant='default', id='cancel-btn'),
                    id='button-row',
                ),
                id='edit-form',
            ),
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load prompt data if editing."""
        if self.is_editing and self.prompt_name:
            prompt = self.storage.read(self.prompt_name, self.prompt_group)
            if prompt:
                self.query_one('#name-input', Input).value = prompt.name
                self.query_one('#group-input', Input).value = prompt.group or ''
                self.query_one('#description-input', Input).value = prompt.description or ''
                self.query_one('#tags-input', Input).value = ', '.join(prompt.tags) if prompt.tags else ''
                self.query_one('#system-prompt-input', TextArea).text = prompt.system_prompt
                self.query_one('#user-prompt-input', TextArea).text = prompt.user_prompt or ''

    @on(Input.Changed, '#group-input')
    def on_group_changed(self, event: Input.Changed) -> None:
        """Show group suggestions as user types."""
        suggestions = self.query_one('#group-suggestions', ListView)
        suggestions.clear()

        if event.value:
            query = event.value.lower()
            matches = [g for g in self.existing_groups if query in g.lower()]
            if matches:
                for group in matches[:5]:
                    suggestions.append(ListItem(Label(group), id=_make_dom_id('suggest-group', group)))
                suggestions.add_class('-visible')
            else:
                suggestions.remove_class('-visible')
        else:
            suggestions.remove_class('-visible')

    @on(Input.Changed, '#tags-input')
    def on_tags_changed(self, event: Input.Changed) -> None:
        """Show tag suggestions for the last tag being typed."""
        suggestions = self.query_one('#tag-suggestions', ListView)
        suggestions.clear()

        if event.value:
            # Get the last tag being typed
            parts = event.value.split(',')
            current = parts[-1].strip().lower()

            if current:
                already_added = [p.strip() for p in parts[:-1]]
                matches = [t for t in self.existing_tags if current in t.lower() and t not in already_added]
                if matches:
                    for tag in matches[:5]:
                        suggestions.append(ListItem(Label(tag), id=_make_dom_id('suggest-tag', tag)))
                    suggestions.add_class('-visible')
                else:
                    suggestions.remove_class('-visible')
            else:
                suggestions.remove_class('-visible')
        else:
            suggestions.remove_class('-visible')

    @on(ListView.Selected, '#group-suggestions')
    def on_group_suggestion_selected(self, event: ListView.Selected) -> None:
        """Apply selected group suggestion."""
        item_id = str(event.item.id) if event.item.id else ''
        if item_id.startswith('suggest-group-'):
            group = _decode_dom_id(item_id[14:])
            self.query_one('#group-input', Input).value = group
            self.query_one('#group-suggestions', ListView).remove_class('-visible')

    @on(ListView.Selected, '#tag-suggestions')
    def on_tag_suggestion_selected(self, event: ListView.Selected) -> None:
        """Apply selected tag suggestion."""
        item_id = str(event.item.id) if event.item.id else ''
        if item_id.startswith('suggest-tag-'):
            tag = _decode_dom_id(item_id[12:])
            tags_input = self.query_one('#tags-input', Input)
            parts = tags_input.value.split(',')
            parts[-1] = f' {tag}'
            tags_input.value = ','.join(parts).strip()
            self.query_one('#tag-suggestions', ListView).remove_class('-visible')

    @on(Button.Pressed, '#save-btn')
    def on_save_pressed(self) -> None:
        """Handle save button click."""
        self.action_save()

    @on(Button.Pressed, '#cancel-btn')
    def on_cancel_pressed(self) -> None:
        """Handle cancel button click."""
        self.action_cancel()

    def action_save(self) -> None:
        """Save the prompt."""
        name = self.query_one('#name-input', Input).value.strip()
        group = self.query_one('#group-input', Input).value.strip()
        description = self.query_one('#description-input', Input).value.strip()
        tags_str = self.query_one('#tags-input', Input).value.strip()
        system_prompt = self.query_one('#system-prompt-input', TextArea).text.strip()
        user_prompt = self.query_one('#user-prompt-input', TextArea).text.strip()

        # Validation
        if not name:
            self.notify('Name is required', severity='error')
            return
        if not system_prompt:
            self.notify('System prompt is required', severity='error')
            return

        # Parse tags
        tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []

        # Create prompt object
        prompt = Prompt(
            name=name,
            description=description,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            group=group,
            tags=tags,
        )

        try:
            if self.is_editing:
                self.storage.update(self.prompt_name, prompt, self.prompt_group)
                self.notify(f'Updated prompt "{name}"')
            else:
                self.storage.create(prompt)
                self.notify(f'Created prompt "{name}"')

            if self.on_save_callback:
                self.on_save_callback(prompt)

            self.app.pop_screen()
        except Exception as e:
            self.notify(f'Error: {e}', severity='error')

    def action_cancel(self) -> None:
        """Cancel and go back."""
        self.app.pop_screen()


class PromptButlerApp(App):
    """Prompt Butler Terminal User Interface."""

    TITLE = 'Prompt Butler'
    SUB_TITLE = 'Manage your AI prompts'

    CSS = THEME_CSS

    def __init__(self, storage: Optional[PromptStorage] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = storage or PromptStorage()

    def on_mount(self) -> None:
        """Set up the app when it mounts."""
        self.push_screen(HomeScreen(self.storage))


def main():
    """Entry point for the TUI application."""
    app = PromptButlerApp()
    app.run()


if __name__ == '__main__':
    main()
