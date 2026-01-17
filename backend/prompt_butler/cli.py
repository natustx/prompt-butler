"""Prompt Butler CLI - Manage your AI prompts from the command line.

A CLI tool for managing AI prompts stored in markdown files with YAML frontmatter.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.prompt import Prompt as RichPrompt
from rich.table import Table
from rich.text import Text

import prompt_butler.services.config as config_module
from prompt_butler.models import Prompt as PromptModel
from prompt_butler.services.config import get_config, reload_config
from prompt_butler.services.migrate import migrate_prompts
from prompt_butler.services.storage import PromptExistsError, PromptStorage, StorageError

__version__ = '1.0.0'

# Global console for rich output
console = Console()
error_console = Console(stderr=True)

# Main Typer app
app = typer.Typer(
    name='pb',
    help='Prompt Butler - Manage your AI prompts from the command line.',
    no_args_is_help=True,
    add_completion=False,
)

# Tag subcommands
tag_app = typer.Typer(help='Manage tags across prompts.')
app.add_typer(tag_app, name='tag')

# Group subcommands
group_app = typer.Typer(help='Manage groups for organizing prompts.')
app.add_typer(group_app, name='group')

# Config subcommands
config_app = typer.Typer(help='Manage Prompt Butler configuration.')
app.add_typer(config_app, name='config')


# Global state for --json flag
class State:
    json_output: bool = False


state = State()


def version_callback(value: bool) -> None:
    """Display version and exit."""
    if value:
        if state.json_output:
            print(json.dumps({'version': __version__}))
        else:
            console.print(f'Prompt Butler v{__version__}')
        raise typer.Exit()


@app.callback()
def main(
    json_output: bool = typer.Option(
        False,
        '--json',
        '-j',
        help='Output in machine-readable JSON format.',
    ),
    version: Optional[bool] = typer.Option(
        None,
        '--version',
        '-v',
        callback=version_callback,
        is_eager=True,
        help='Show version and exit.',
    ),
) -> None:
    """Prompt Butler - Manage your AI prompts from the command line.

    Use --json for machine-readable output in scripts and automation.
    """
    state.json_output = json_output


@app.command('list')
def list_prompts(
    query: Optional[str] = typer.Argument(None, help='Optional search query for fuzzy matching.'),
    tag: Optional[str] = typer.Option(None, '--tag', '-t', help='Filter by tag.'),
    group: Optional[str] = typer.Option(None, '--group', '-g', help='Filter by group.'),
) -> None:
    """List all prompts, optionally with fuzzy search.

    Provide a query to search by name and description. Use --tag and --group to filter.
    Filters can be combined with search.
    """
    storage = PromptStorage()

    try:
        if query:
            # Fuzzy search first, then apply filters
            prompts = storage.search(query, limit=100)
            # Apply filters to search results
            if tag:
                prompts = [p for p in prompts if tag in p.tags]
            if group is not None:
                prompts = [p for p in prompts if p.group == group]
        else:
            prompts = storage.list_all(tag=tag, group=group if group != '' else None)

        if state.json_output:
            print(json.dumps([p.model_dump() for p in prompts], indent=2))
        else:
            if not prompts:
                if query:
                    console.print(f'[dim]No prompts matching "{query}".[/dim]')
                else:
                    console.print('[dim]No prompts found.[/dim]')
                return

            title = f'Search Results: "{query}"' if query else 'Prompts'
            table = Table(title=title, show_header=True, header_style='bold green')
            table.add_column('Name', style='cyan')
            table.add_column('Group', style='yellow')
            table.add_column('Description', style='white')
            table.add_column('Tags', style='magenta')

            for p in prompts:
                tags_str = ', '.join(p.tags) if p.tags else '-'
                description = p.description or '-'
                if len(description) > 50:
                    description = f'{description[:50]}...'
                table.add_row(p.name, p.group or '-', description, tags_str)

            console.print(table)
            console.print(f'\n[dim]{len(prompts)} prompt(s) found.[/dim]')
    except StorageError as e:
        _handle_error(str(e))


@app.command('show')
def show_prompt(
    name: str = typer.Argument(..., help='Name of the prompt to show.'),
    group: Optional[str] = typer.Option(None, '--group', '-g', help='Group of the prompt.'),
) -> None:
    """Show details of a specific prompt."""
    storage = PromptStorage()

    try:
        prompt = storage.read(name, group=group or '')

        if not prompt:
            _handle_error(f'Prompt "{name}" not found.')
            raise typer.Exit(1)

        if state.json_output:
            print(json.dumps(prompt.model_dump(), indent=2))
        else:
            _display_prompt(prompt)
    except StorageError as e:
        _handle_error(str(e))


@app.command('search')
def search_prompts(
    query: str = typer.Argument(..., help='Search query (fuzzy matching).'),
    limit: int = typer.Option(10, '--limit', '-n', help='Maximum results to return.'),
) -> None:
    """Search prompts by name and description."""
    storage = PromptStorage()

    try:
        prompts = storage.search(query, limit=limit)

        if state.json_output:
            print(json.dumps([p.model_dump() for p in prompts], indent=2))
        else:
            if not prompts:
                console.print(f'[dim]No prompts matching "{query}".[/dim]')
                return

            table = Table(title=f'Search Results: "{query}"', show_header=True, header_style='bold green')
            table.add_column('Name', style='cyan')
            table.add_column('Group', style='yellow')
            table.add_column('Description', style='white')

            for p in prompts:
                description = p.description or '-'
                if len(description) > 60:
                    description = f'{description[:60]}...'
                table.add_row(p.name, p.group or '-', description)

            console.print(table)
    except StorageError as e:
        _handle_error(str(e))


@tag_app.command('list')
def tag_list() -> None:
    """List all unique tags with usage counts."""
    storage = PromptStorage()

    try:
        tag_counts = storage.get_all_tags()

        if state.json_output:
            print(json.dumps(tag_counts, indent=2))
        else:
            if not tag_counts:
                console.print('[dim]No tags found.[/dim]')
                return

            table = Table(title='Tags', show_header=True, header_style='bold green')
            table.add_column('Tag', style='cyan')
            table.add_column('Count', style='yellow', justify='right')

            for tag, count in sorted(tag_counts.items()):
                table.add_row(tag, str(count))

            console.print(table)
    except StorageError as e:
        _handle_error(str(e))


@tag_app.command('rename')
def tag_rename(
    old_tag: str = typer.Argument(..., help='The tag to rename.'),
    new_tag: str = typer.Argument(..., help='The new tag name.'),
) -> None:
    """Rename a tag across all prompts that use it."""
    storage = PromptStorage()

    try:
        # Get all prompts with the old tag
        prompts = storage.list_all(tag=old_tag)

        if not prompts:
            _handle_error(f'No prompts found with tag "{old_tag}".')
            raise typer.Exit(1)

        # Update each prompt
        updated_count = 0
        for prompt in prompts:
            # Replace the old tag with the new tag
            new_tags = [new_tag if t == old_tag else t for t in prompt.tags]

            # Skip if tag already renamed (avoid duplicates)
            if new_tag in prompt.tags and old_tag in prompt.tags:
                new_tags = [t for t in new_tags if t != old_tag or t == new_tag]
                new_tags = list(dict.fromkeys(new_tags))  # Remove duplicates

            updated_prompt = prompt.model_copy(update={'tags': new_tags})
            storage.update(prompt.name, updated_prompt, group=prompt.group)
            updated_count += 1

        if state.json_output:
            print(json.dumps({
                'renamed': True,
                'old_tag': old_tag,
                'new_tag': new_tag,
                'prompts_updated': updated_count,
            }, indent=2))
        else:
            console.print(f'[green]✓[/green] Renamed tag [cyan]{old_tag}[/cyan] to [cyan]{new_tag}[/cyan]')
            console.print(f'  [dim]{updated_count} prompt(s) updated.[/dim]')

    except StorageError as e:
        _handle_error(str(e))
        raise typer.Exit(1) from e


# Keep legacy 'tags' command for backward compatibility
@app.command('tags', hidden=True)
def tags_legacy() -> None:
    """[Deprecated] Use 'pb tag list' instead."""
    tag_list()


@group_app.command('list')
def group_list() -> None:
    """List all groups with prompt counts."""
    storage = PromptStorage()

    try:
        group_counts = storage.get_all_groups()

        if state.json_output:
            print(json.dumps(group_counts, indent=2))
        else:
            if not group_counts:
                console.print('[dim]No groups found.[/dim]')
                return

            table = Table(title='Groups', show_header=True, header_style='bold green')
            table.add_column('Group', style='cyan')
            table.add_column('Count', style='yellow', justify='right')

            for group, count in sorted(group_counts.items()):
                table.add_row(group or '(root)', str(count))

            console.print(table)
    except StorageError as e:
        _handle_error(str(e))


@group_app.command('create')
def group_create(
    name: str = typer.Argument(..., help='Name of the group to create.'),
) -> None:
    """Create a new group folder for organizing prompts."""
    storage = PromptStorage()

    # Validate group name
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        _handle_error('Group name must contain only alphanumeric characters, underscores, and hyphens.')
        raise typer.Exit(1)

    # Check if group already exists
    group_path = storage.prompts_dir / name
    if group_path.exists():
        _handle_error(f'Group "{name}" already exists.')
        raise typer.Exit(1)

    # Create the group folder
    try:
        group_path.mkdir(parents=True, exist_ok=False)

        if state.json_output:
            print(json.dumps({
                'created': True,
                'name': name,
                'path': str(group_path),
            }, indent=2))
        else:
            console.print(f'[green]✓[/green] Created group [cyan]{name}[/cyan]')
            console.print(f'  [dim]Path:[/dim] {group_path}')

    except OSError as e:
        _handle_error(f'Failed to create group folder: {e}')
        raise typer.Exit(1) from e


@group_app.command('rename')
def group_rename(
    old_name: str = typer.Argument(..., help='The group to rename.'),
    new_name: str = typer.Argument(..., help='The new group name.'),
) -> None:
    """Rename a group folder, moving all prompts to the new location."""
    storage = PromptStorage()

    # Validate new group name
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', new_name):
        _handle_error('Group name must contain only alphanumeric characters, underscores, and hyphens.')
        raise typer.Exit(1)

    old_path = storage.prompts_dir / old_name
    new_path = storage.prompts_dir / new_name

    # Check source exists
    if not old_path.exists():
        _handle_error(f'Group "{old_name}" does not exist.')
        raise typer.Exit(1)

    # Check target doesn't exist
    if new_path.exists():
        _handle_error(f'Group "{new_name}" already exists.')
        raise typer.Exit(1)

    try:
        # Count prompts before rename
        prompt_count = len(list(old_path.glob('*.md')))

        # Rename the folder
        old_path.rename(new_path)

        if state.json_output:
            print(json.dumps({
                'renamed': True,
                'old_name': old_name,
                'new_name': new_name,
                'prompts_moved': prompt_count,
            }, indent=2))
        else:
            console.print(f'[green]✓[/green] Renamed group [cyan]{old_name}[/cyan] to [cyan]{new_name}[/cyan]')
            console.print(f'  [dim]{prompt_count} prompt(s) moved.[/dim]')

    except OSError as e:
        _handle_error(f'Failed to rename group: {e}')
        raise typer.Exit(1) from e


# Keep legacy 'groups' command for backward compatibility
@app.command('groups', hidden=True)
def groups_legacy() -> None:
    """[Deprecated] Use 'pb group list' instead."""
    group_list()


@config_app.callback(invoke_without_command=True)
def config_show(ctx: typer.Context) -> None:
    """Show current configuration or manage settings.

    Without subcommand: displays current config.
    Use 'pb config set <key> <value>' to change settings.
    """
    # Only show config if no subcommand was invoked
    if ctx.invoked_subcommand is not None:
        return

    config = get_config()

    if state.json_output:
        print(json.dumps({
            'prompts_dir': str(config.prompts_dir),
            'editor': config.editor,
            'default_group': config.default_group,
            'config_file': str(config_module.DEFAULT_CONFIG_FILE),
        }, indent=2))
    else:
        table = Table(title='Configuration', show_header=True, header_style='bold green')
        table.add_column('Setting', style='cyan')
        table.add_column('Value', style='white')

        table.add_row('prompts_dir', str(config.prompts_dir))
        table.add_row('editor', config.editor)
        table.add_row('default_group', config.default_group or '(none)')
        table.add_row('config_file', str(config_module.DEFAULT_CONFIG_FILE))

        console.print(table)


@config_app.command('set')
def config_set(
    key: str = typer.Argument(..., help='Configuration key to set (prompts_dir, editor, default_group).'),
    value: str = typer.Argument(..., help='Value to set.'),
) -> None:
    """Set a configuration value."""
    valid_keys = ['prompts_dir', 'editor', 'default_group']

    if key not in valid_keys:
        _handle_error(f'Unknown config key "{key}". Valid keys: {", ".join(valid_keys)}')
        raise typer.Exit(1)

    config = get_config()

    # Update the config value
    if key == 'prompts_dir':
        new_config = config.update(prompts_dir=value)
    elif key == 'editor':
        new_config = config.update(editor=value)
    else:  # default_group
        new_config = config.update(default_group=value)

    # Save the config
    try:
        new_config.save()
        reload_config()  # Reload the global config

        if state.json_output:
            print(json.dumps({
                'updated': True,
                'key': key,
                'value': value,
            }, indent=2))
        else:
            console.print(f'[green]✓[/green] Set [cyan]{key}[/cyan] = [yellow]{value}[/yellow]')
            console.print(f'  [dim]Saved to:[/dim] {config_module.DEFAULT_CONFIG_FILE}')

    except OSError as e:
        _handle_error(f'Failed to save configuration: {e}')
        raise typer.Exit(1) from e


@config_app.command('path')
def config_path() -> None:
    """Show the path to the configuration file."""
    if state.json_output:
        print(json.dumps({
            'config_file': str(config_module.DEFAULT_CONFIG_FILE),
            'exists': config_module.DEFAULT_CONFIG_FILE.exists(),
        }, indent=2))
    else:
        exists = (
            '[green]exists[/green]'
            if config_module.DEFAULT_CONFIG_FILE.exists()
            else '[yellow]not created yet[/yellow]'
        )
        console.print(f'Configuration file: [cyan]{config_module.DEFAULT_CONFIG_FILE}[/cyan] ({exists})')


@app.command('migrate')
def migrate(
    source: Optional[str] = typer.Option(
        None,
        '--source',
        '-s',
        help='Directory containing legacy YAML prompt files (defaults to prompts_dir).',
    ),
    overwrite: bool = typer.Option(
        False,
        '--overwrite',
        help='Overwrite existing prompts instead of skipping them.',
    ),
) -> None:
    """Migrate legacy YAML prompts to markdown format."""
    config = get_config()
    source_dir = Path(source).expanduser() if source else config.prompts_dir

    if not source_dir.exists():
        _handle_error(f'Source directory does not exist: {source_dir}')
        raise typer.Exit(1)

    storage = PromptStorage(prompts_dir=config.prompts_dir)

    def on_progress(action: str, message: str) -> None:
        if state.json_output:
            return
        if action == 'error':
            error_console.print(f'[red]Error:[/red] {message}')
        else:
            console.print(message)

    result = migrate_prompts(
        source_dir=source_dir,
        target_storage=storage,
        on_progress=on_progress,
        skip_existing=not overwrite,
    )

    if state.json_output:
        print(json.dumps({
            'source_dir': str(source_dir),
            'prompts_dir': str(storage.prompts_dir),
            'succeeded': result.success_count,
            'failed': result.failure_count,
            'skipped': result.skipped_count,
            'total': result.total_processed,
            'errors': [{'file': name, 'error': error} for name, error in result.errors],
        }, indent=2))
    else:
        console.print(
            f'\n[green]✓[/green] Migration complete: '
            f'{result.success_count} succeeded, '
            f'{result.failure_count} failed, '
            f'{result.skipped_count} skipped'
        )


@app.command('index')
def index_prompts() -> None:
    """Rescan prompts directory and rebuild index.

    Scans the prompts directory to count all prompts.
    Useful to verify prompt discovery is working correctly.
    """
    storage = PromptStorage()

    try:
        prompts = storage.list_all()
        count = len(prompts)

        # Count by group
        groups: dict[str, int] = {}
        for prompt in prompts:
            group = prompt.group or '(root)'
            groups[group] = groups.get(group, 0) + 1

        if state.json_output:
            print(json.dumps({
                'indexed': True,
                'count': count,
                'groups': dict(sorted(groups.items())),
                'prompts_dir': str(storage.prompts_dir),
            }, indent=2))
        else:
            console.print(f'[green]✓[/green] Indexed [cyan]{count}[/cyan] prompt(s)')
            if groups:
                for group, group_count in sorted(groups.items()):
                    console.print(f'  {group}: {group_count}')
            console.print(f'  [dim]Directory:[/dim] {storage.prompts_dir}')

    except StorageError as e:
        _handle_error(str(e))
        raise typer.Exit(1) from e


@app.command('add')
def add_prompt(
    name: Optional[str] = typer.Option(None, '--name', '-n', help='Name of the prompt (skips interactive prompt).'),
    group: Optional[str] = typer.Option(None, '--group', '-g', help='Group for the prompt (skips interactive prompt).'),
    description: Optional[str] = typer.Option(None, '--description', '-d', help='Description of the prompt.'),
    tags: Optional[str] = typer.Option(None, '--tags', '-t', help='Comma-separated tags.'),
    edit: bool = typer.Option(False, '--edit', '-e', help='Open in $EDITOR after creation.'),
) -> None:
    """Create a new prompt.

    In interactive mode, prompts for name, description, group, and tags.
    Use flags to skip interactive prompts for specific fields.
    """
    storage = PromptStorage()

    # Interactive mode for missing fields
    if name is None:
        name = RichPrompt.ask('[cyan]Prompt name[/cyan]')

    if not name:
        _handle_error('Name is required.')
        raise typer.Exit(1)

    if description is None:
        description = RichPrompt.ask('[cyan]Description[/cyan]', default='')

    if group is None:
        group = RichPrompt.ask('[cyan]Group[/cyan] (leave empty for root)', default='')

    if tags is None:
        tags_input = RichPrompt.ask('[cyan]Tags[/cyan] (comma-separated)', default='')
    else:
        tags_input = tags

    # Parse tags
    tag_list = [t.strip() for t in tags_input.split(',') if t.strip()] if tags_input else []

    # Create prompt with minimal system_prompt
    prompt = PromptModel(
        name=name,
        description=description or '',
        system_prompt='# Your system prompt here\n\nDescribe the AI behavior and context.',
        user_prompt='',
        group=group or '',
        tags=tag_list,
    )

    try:
        storage.create(prompt)
        file_path = storage._get_prompt_path(name, group or '')

        if state.json_output:
            print(json.dumps({
                'created': True,
                'name': name,
                'path': str(file_path),
            }, indent=2))
        else:
            console.print(f'\n[green]✓[/green] Created prompt [cyan]{name}[/cyan]')
            console.print(f'  [dim]File:[/dim] {file_path}')

        # Open in editor if requested
        if edit:
            _open_in_editor(file_path)

    except PromptExistsError:
        _handle_error(f'Prompt "{name}" already exists.')
        raise typer.Exit(1) from None
    except StorageError as e:
        _handle_error(str(e))
        raise typer.Exit(1) from e


@app.command('edit')
def edit_prompt(
    name: str = typer.Argument(..., help='Name of the prompt to edit.'),
    group: Optional[str] = typer.Option(None, '--group', '-g', help='Group of the prompt.'),
) -> None:
    """Edit an existing prompt in your default editor.

    Opens the prompt file in $EDITOR (or $VISUAL, or vi).
    Validates the file after editing.
    """
    storage = PromptStorage()

    # Find the prompt
    try:
        prompt = storage.read(name, group=group or '')

        if not prompt:
            _handle_error(f'Prompt "{name}" not found.')
            raise typer.Exit(1)

        # Get the file path
        file_path = storage._get_prompt_path(prompt.name, prompt.group)

        if not file_path.exists():
            # Try to find it by searching
            for match in storage.prompts_dir.rglob(f'{storage.slugify(name)}.md'):
                file_path = match
                break
            else:
                _handle_error(f'Prompt file not found for "{name}".')
                raise typer.Exit(1)

        # Open in editor
        _open_in_editor(file_path)

        # Re-parse and validate after editing
        try:
            updated_prompt = storage._read_prompt(file_path)

            if state.json_output:
                print(json.dumps({
                    'edited': True,
                    'name': updated_prompt.name,
                    'path': str(file_path),
                }, indent=2))
            else:
                console.print(f'\n[green]✓[/green] Updated prompt [cyan]{updated_prompt.name}[/cyan]')
                console.print(f'  [dim]File:[/dim] {file_path}')

        except Exception as e:
            _handle_error(f'Validation failed after edit: {e}')
            console.print('[yellow]The file may contain invalid syntax. Please check and try again.[/yellow]')
            raise typer.Exit(1) from e

    except StorageError as e:
        _handle_error(str(e))
        raise typer.Exit(1) from e


@app.command('delete')
def delete_prompt(
    name: str = typer.Argument(..., help='Name of the prompt to delete.'),
    group: Optional[str] = typer.Option(None, '--group', '-g', help='Group of the prompt.'),
    force: bool = typer.Option(False, '--force', '-f', help='Skip confirmation prompt.'),
) -> None:
    """Delete a prompt.

    Shows confirmation prompt before deletion unless --force is used.
    """
    storage = PromptStorage()

    try:
        prompt = storage.read(name, group=group or '')

        if not prompt:
            _handle_error(f'Prompt "{name}" not found.')
            raise typer.Exit(1)

        # Confirm deletion unless --force is used
        if not force and not state.json_output:
            confirm = Confirm.ask(
                f'Are you sure you want to delete [cyan]{prompt.name}[/cyan]'
                + (f' (group: {prompt.group})' if prompt.group else '') + '?'
            )
            if not confirm:
                console.print('[dim]Cancelled.[/dim]')
                raise typer.Exit(0)

        # Delete the prompt
        if storage.delete(name, group=prompt.group):
            if state.json_output:
                print(json.dumps({
                    'deleted': True,
                    'name': prompt.name,
                    'group': prompt.group,
                }, indent=2))
            else:
                console.print(f'[green]✓[/green] Deleted prompt [cyan]{prompt.name}[/cyan]')
        else:
            _handle_error(f'Failed to delete prompt "{name}".')
            raise typer.Exit(1)

    except StorageError as e:
        _handle_error(str(e))
        raise typer.Exit(1) from e


@app.command('copy')
def copy_prompt(
    name: str = typer.Argument(..., help='Name of the prompt to copy.'),
    group: Optional[str] = typer.Option(None, '--group', '-g', help='Group of the prompt.'),
    user: bool = typer.Option(False, '--user', '-u', help='Copy user prompt instead of system prompt.'),
    all_prompts: bool = typer.Option(False, '--all', '-a', help='Copy both system and user prompts.'),
) -> None:
    """Copy prompt content to clipboard.

    By default, copies the system prompt. Use --user for user prompt or --all for both.
    """
    import pyperclip

    storage = PromptStorage()

    try:
        prompt = storage.read(name, group=group or '')

        if not prompt:
            _handle_error(f'Prompt "{name}" not found.')
            raise typer.Exit(1)

        # Determine what to copy
        if all_prompts:
            content = prompt.system_prompt
            if prompt.user_prompt:
                content += '\n\n---\n\n' + prompt.user_prompt
            what = 'system and user prompts'
        elif user:
            if not prompt.user_prompt:
                _handle_error(f'Prompt "{name}" has no user prompt.')
                raise typer.Exit(1)
            content = prompt.user_prompt
            what = 'user prompt'
        else:
            content = prompt.system_prompt
            what = 'system prompt'

        # Copy to clipboard
        try:
            pyperclip.copy(content)
        except pyperclip.PyperclipException as e:
            _handle_error(f'Failed to copy to clipboard: {e}')
            raise typer.Exit(1) from e

        if state.json_output:
            print(json.dumps({
                'copied': True,
                'name': prompt.name,
                'type': 'all' if all_prompts else ('user' if user else 'system'),
                'length': len(content),
            }, indent=2))
        else:
            console.print(f'[green]✓[/green] Copied {what} from [cyan]{prompt.name}[/cyan] to clipboard')

    except StorageError as e:
        _handle_error(str(e))
        raise typer.Exit(1) from e


@app.command('clone')
def clone_prompt(
    source: str = typer.Argument(..., help='Name of the prompt to clone.'),
    new_name: str = typer.Argument(..., help='Name for the cloned prompt.'),
    source_group: Optional[str] = typer.Option(
        None,
        '--source-group',
        '-s',
        help='Group of the source prompt.',
    ),
    group: Optional[str] = typer.Option(
        None,
        '--group',
        '-g',
        help='Group for the new prompt (defaults to source group).',
    ),
) -> None:
    """Clone an existing prompt with a new name.

    Creates a copy of the prompt with all content preserved but a new name.
    Use --group to place the clone in a different group.
    """
    storage = PromptStorage()

    try:
        # Find the source prompt
        source_prompt = storage.read(source, group=source_group or '')

        if not source_prompt:
            _handle_error(f'Source prompt "{source}" not found.')
            raise typer.Exit(1)

        # Determine target group
        target_group = group if group is not None else source_prompt.group

        # Create the cloned prompt with new name
        cloned_prompt = PromptModel(
            name=new_name,
            description=source_prompt.description,
            system_prompt=source_prompt.system_prompt,
            user_prompt=source_prompt.user_prompt,
            group=target_group,
            tags=source_prompt.tags.copy(),
        )

        # Try to create the new prompt
        storage.create(cloned_prompt)
        file_path = storage._get_prompt_path(new_name, target_group)

        if state.json_output:
            print(json.dumps({
                'cloned': True,
                'source': source_prompt.name,
                'name': new_name,
                'group': target_group,
                'path': str(file_path),
            }, indent=2))
        else:
            console.print(f'[green]✓[/green] Cloned [cyan]{source}[/cyan] to [cyan]{new_name}[/cyan]')
            console.print(f'  [dim]File:[/dim] {file_path}')

    except PromptExistsError:
        _handle_error(f'Prompt "{new_name}" already exists.')
        raise typer.Exit(1) from None
    except StorageError as e:
        _handle_error(str(e))
        raise typer.Exit(1) from e


def _open_in_editor(file_path) -> None:
    """Open a file in the user's preferred editor."""
    editor = os.environ.get('EDITOR', os.environ.get('VISUAL', 'vi'))

    try:
        console.print(f'\n[dim]Opening in {editor}...[/dim]')
        subprocess.run([editor, str(file_path)], check=True)
    except subprocess.CalledProcessError as e:
        error_console.print(f'[yellow]Warning:[/yellow] Editor exited with code {e.returncode}')
    except FileNotFoundError:
        error_console.print(f'[yellow]Warning:[/yellow] Editor "{editor}" not found. Set $EDITOR environment variable.')


@app.command('tui')
def launch_tui() -> None:
    """Launch the Terminal User Interface (TUI).

    Opens an interactive terminal interface for browsing and managing prompts.
    Requires the 'textual' package to be installed.
    """
    try:
        from prompt_butler.tui.app import PromptButlerApp
    except ImportError:
        _handle_error(
            'TUI requires the textual package.\n'
            'Install it with: pip install textual'
        )
        raise typer.Exit(1) from None

    # Create storage with current config
    config = get_config()
    storage = PromptStorage(prompts_dir=config.prompts_dir)

    # Launch the TUI
    tui_app = PromptButlerApp(storage=storage)
    tui_app.run()


def _display_prompt(prompt: PromptModel) -> None:
    """Display a prompt with rich formatting."""
    # Header with name and group
    header = Text()
    header.append(prompt.name, style='bold cyan')
    if prompt.group:
        header.append(f' ({prompt.group})', style='yellow')

    console.print(Panel(header, title='Prompt', border_style='green'))

    # Description
    if prompt.description:
        console.print(f'\n[bold]Description:[/bold] {prompt.description}')

    # Tags
    if prompt.tags:
        tags_display = ' '.join(f'[magenta]#{tag}[/magenta]' for tag in prompt.tags)
        console.print(f'\n[bold]Tags:[/bold] {tags_display}')

    # System Prompt
    console.print('\n[bold green]System Prompt:[/bold green]')
    console.print(Panel(prompt.system_prompt or '[dim]Empty[/dim]', border_style='dim'))

    # User Prompt (if present)
    if prompt.user_prompt:
        console.print('\n[bold yellow]User Prompt:[/bold yellow]')
        console.print(Panel(prompt.user_prompt, border_style='dim'))


def _handle_error(message: str) -> None:
    """Handle error output in JSON or rich format."""
    if state.json_output:
        print(json.dumps({'error': message}), file=sys.stderr)
    else:
        error_console.print(f'[red]Error:[/red] {message}')


if __name__ == '__main__':
    app()
