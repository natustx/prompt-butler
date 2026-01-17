"""Prompt Butler CLI entry point."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

import typer
from rapidfuzz import fuzz
from rich.console import Console
from rich.table import Table

from prompt_butler.models import Prompt
from prompt_butler.services.storage import (
    GroupExistsError,
    GroupNotFoundError,
    PromptExistsError,
    PromptStorage,
)

app = typer.Typer(help='Prompt Butler - AI prompt management tool', add_completion=False)
tag_app = typer.Typer(help='Manage tags')
group_app = typer.Typer(help='Manage groups')

app.add_typer(tag_app, name='tag')
app.add_typer(group_app, name='group')

console = Console()
error_console = Console(stderr=True)


@app.callback(invoke_without_command=True)
def show_help(ctx: typer.Context) -> None:
    """Show help text when no subcommand is provided."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)


def get_storage() -> PromptStorage:
    """Get the storage service instance."""
    return PromptStorage()


def output_json(data: dict | list) -> None:
    """Output data as JSON."""
    typer.echo(json.dumps(data, indent=2))


def prompt_to_dict(prompt: Prompt) -> dict:
    """Convert a Prompt to a dictionary for JSON output."""
    return {
        'name': prompt.name,
        'description': prompt.description,
        'system_prompt': prompt.system_prompt,
        'user_prompt': prompt.user_prompt,
        'tags': prompt.tags,
        'group': prompt.group,
    }


def display_group(group: str) -> str:
    return group if group else 'ungrouped'


def normalize_group(group: str | None) -> str:
    return group or ''


def open_editor(content: str = '') -> str | None:
    """Open $EDITOR with content and return the edited text."""
    editor = os.environ.get('EDITOR', os.environ.get('VISUAL', 'vim'))

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        result = subprocess.run([editor, temp_path], check=False)
        if result.returncode != 0:
            return None

        with open(temp_path, encoding='utf-8') as f:
            return f.read()
    finally:
        os.unlink(temp_path)


def fuzzy_filter(prompts: list[Prompt], query: str) -> list[Prompt]:
    results: list[tuple[int, Prompt]] = []
    for prompt in prompts:
        searchable = f'{prompt.name} {prompt.description} {" ".join(prompt.tags)}'
        score = fuzz.partial_ratio(query.lower(), searchable.lower())
        if score >= 50:
            results.append((score, prompt))
    results.sort(key=lambda x: x[0], reverse=True)
    return [prompt for _, prompt in results]


@app.command('add')
def add_prompt(
    name: str | None = typer.Option(None, '--name', '-n', help='Prompt name'),
    group: str | None = typer.Option(None, '--group', '-g', help='Group name (empty for ungrouped)'),
    edit: bool = typer.Option(False, '--edit', '-e', help='Open in $EDITOR for editing'),
    json_output: bool = typer.Option(False, '--json', help='Output as JSON'),
) -> None:
    """Add a new prompt."""
    storage = get_storage()
    group_value = normalize_group(group)

    if edit or not name:
        template = """---
name: {name}
description: Enter description here
tags:
  - example
---
Enter your system prompt here.

---user---
Enter your user prompt here (optional, delete if not needed).
""".format(name=name or 'my-prompt')

        edited = open_editor(template)
        if edited is None:
            error_console.print('[red]Editor was closed without saving.[/red]')
            raise typer.Exit(code=1)

        import frontmatter

        try:
            post = frontmatter.loads(edited)
        except Exception as e:
            error_console.print(f'[red]Invalid frontmatter format: {e}[/red]')
            raise typer.Exit(code=1) from e

        name = post.get('name', name or 'my-prompt')
        description = post.get('description', '')
        tags = post.get('tags', [])

        content = post.content
        if '---user---' in content:
            parts = content.split('---user---', 1)
            system_prompt = parts[0].strip()
            user_prompt = parts[1].strip() if len(parts) > 1 else ''
        else:
            system_prompt = content.strip()
            user_prompt = ''
    else:
        if not json_output:
            console.print('[cyan]Enter system prompt (Ctrl+D to finish):[/cyan]')
        try:
            system_prompt = sys.stdin.read().strip()
        except KeyboardInterrupt as e:
            if not json_output:
                console.print('\n[yellow]Cancelled.[/yellow]')
            raise typer.Exit(code=1) from e

        if not system_prompt:
            error_console.print('[red]System prompt cannot be empty.[/red]')
            raise typer.Exit(code=1)

        description = ''
        tags = []
        user_prompt = ''

    if not name:
        error_console.print('[red]Prompt name is required.[/red]')
        raise typer.Exit(code=1)

    prompt = Prompt(
        name=name,
        description=description,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        tags=tags,
        group=group_value,
    )

    try:
        storage.create(prompt)
        if json_output:
            output_json({'status': 'created', 'prompt': prompt_to_dict(prompt)})
        else:
            console.print(f"[green]Created prompt '{name}' in group '{display_group(group_value)}'.[/green]")
    except PromptExistsError as e:
        msg = f"Prompt '{name}' already exists in group '{display_group(group_value)}'"
        if json_output:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}.[/red]')
        raise typer.Exit(code=1) from e


@app.command('list')
def list_prompts(
    query: str | None = typer.Argument(None, help='Fuzzy search query'),
    group: str | None = typer.Option(None, '--group', '-g', help='Filter by group'),
    tag: str | None = typer.Option(None, '--tag', '-t', help='Filter by tag'),
    json_output: bool = typer.Option(False, '--json', help='Output as JSON'),
) -> None:
    """List all prompts."""
    storage = get_storage()

    prompts = storage.list(group=group)

    if tag:
        prompts = [p for p in prompts if tag in p.tags]

    if query:
        prompts = fuzzy_filter(prompts, query)

    if json_output:
        output_json([prompt_to_dict(p) for p in prompts])
        return

    if not prompts:
        console.print('[yellow]No prompts found.[/yellow]')
        return

    table = Table(title='Prompts')
    table.add_column('Name', style='cyan')
    table.add_column('Group', style='blue')
    table.add_column('Description')
    table.add_column('Tags', style='green')

    for prompt in prompts:
        desc = prompt.description[:50] + '...' if len(prompt.description) > 50 else prompt.description
        table.add_row(prompt.name, display_group(prompt.group), desc, ', '.join(prompt.tags))

    console.print(table)


@app.command('show')
def show_prompt(
    name: str = typer.Argument(..., help='Prompt name'),
    group: str | None = typer.Option(None, '--group', '-g', help='Group name (empty for ungrouped)'),
    json_output: bool = typer.Option(False, '--json', help='Output as JSON'),
) -> None:
    """Show a prompt's content."""
    storage = get_storage()
    group_value = normalize_group(group)

    prompt = storage.get(name, group=group_value)

    if not prompt:
        msg = f"Prompt '{name}' not found in group '{display_group(group_value)}'"
        if json_output:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}.[/red]')
        raise typer.Exit(code=1)

    if json_output:
        output_json(prompt_to_dict(prompt))
        return

    console.print(f'[bold cyan]Name:[/bold cyan] {prompt.name}')
    console.print(f'[bold cyan]Group:[/bold cyan] {display_group(prompt.group)}')
    console.print(f'[bold cyan]Description:[/bold cyan] {prompt.description}')
    console.print(f'[bold cyan]Tags:[/bold cyan] {", ".join(prompt.tags)}')
    console.print()
    console.print('[bold cyan]System Prompt:[/bold cyan]')
    console.print(prompt.system_prompt)
    if prompt.user_prompt:
        console.print()
        console.print('[bold cyan]User Prompt:[/bold cyan]')
        console.print(prompt.user_prompt)


@app.command('edit')
def edit_prompt(
    name: str = typer.Argument(..., help='Prompt name'),
    group: str | None = typer.Option(None, '--group', '-g', help='Group name (empty for ungrouped)'),
    json_output: bool = typer.Option(False, '--json', help='Output as JSON'),
) -> None:
    """Edit a prompt in $EDITOR."""
    storage = get_storage()
    group_value = normalize_group(group)

    prompt = storage.get(name, group=group_value)

    if not prompt:
        msg = f"Prompt '{name}' not found in group '{display_group(group_value)}'"
        if json_output:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}.[/red]')
        raise typer.Exit(code=1)

    import frontmatter

    if prompt.user_prompt:
        content = f'{prompt.system_prompt}\n\n---user---\n{prompt.user_prompt}'
    else:
        content = prompt.system_prompt

    post = frontmatter.Post(
        content=content,
        name=prompt.name,
        description=prompt.description,
        tags=prompt.tags,
    )
    original_text = frontmatter.dumps(post)

    edited = open_editor(original_text)
    if edited is None:
        error_console.print('[red]Editor was closed without saving.[/red]')
        raise typer.Exit(code=1)

    if edited == original_text:
        console.print('[yellow]No changes made.[/yellow]')
        return

    try:
        post = frontmatter.loads(edited)
    except Exception as e:
        error_console.print(f'[red]Invalid frontmatter format: {e}[/red]')
        raise typer.Exit(code=1) from e

    new_content = post.content
    if '---user---' in new_content:
        parts = new_content.split('---user---', 1)
        system_prompt = parts[0].strip()
        user_prompt = parts[1].strip() if len(parts) > 1 else ''
    else:
        system_prompt = new_content.strip()
        user_prompt = ''

    storage.update(
        name,
        group_value,
        description=post.get('description', prompt.description),
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        tags=post.get('tags', prompt.tags),
    )

    if json_output:
        updated = storage.get(name, group=group_value)
        output_json({'status': 'updated', 'prompt': prompt_to_dict(updated)})
    else:
        console.print(f"[green]Updated prompt '{name}'.[/green]")


@app.command('delete')
def delete_prompt(
    name: str = typer.Argument(..., help='Prompt name'),
    group: str | None = typer.Option(None, '--group', '-g', help='Group name (empty for ungrouped)'),
    force: bool = typer.Option(False, '--force', '-f', help='Skip confirmation'),
    json_output: bool = typer.Option(False, '--json', help='Output as JSON'),
) -> None:
    """Delete a prompt."""
    storage = get_storage()
    group_value = normalize_group(group)

    prompt = storage.get(name, group=group_value)

    if not prompt:
        msg = f"Prompt '{name}' not found in group '{display_group(group_value)}'"
        if json_output:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}.[/red]')
        raise typer.Exit(code=1)

    if not force:
        console.print(f"[yellow]Delete prompt '{name}' from group '{display_group(group_value)}'?[/yellow]")
        response = typer.prompt('Type "yes" to confirm', default='', show_default=False)
        if response.lower() != 'yes':
            console.print('[cyan]Cancelled.[/cyan]')
            return

    storage.delete(name, group=group_value)

    if json_output:
        output_json({'status': 'deleted', 'name': name, 'group': group_value})
    else:
        console.print(f"[green]Deleted prompt '{name}'.[/green]")


@app.command('copy')
def copy_prompt(
    name: str = typer.Argument(..., help='Prompt name'),
    group: str | None = typer.Option(None, '--group', '-g', help='Group name (empty for ungrouped)'),
    user: bool = typer.Option(False, '--user', '-u', help='Copy user prompt instead of system prompt'),
    json_output: bool = typer.Option(False, '--json', help='Output as JSON'),
) -> None:
    """Copy a prompt to clipboard."""
    storage = get_storage()
    group_value = normalize_group(group)

    prompt = storage.get(name, group=group_value)

    if not prompt:
        msg = f"Prompt '{name}' not found in group '{display_group(group_value)}'"
        if json_output:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}.[/red]')
        raise typer.Exit(code=1)

    if user:
        content = prompt.user_prompt
        content_type = 'user prompt'
    else:
        content = prompt.system_prompt
        content_type = 'system prompt'

    if not content:
        msg = f'{content_type.capitalize()} is empty'
        if json_output:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}.[/red]')
        raise typer.Exit(code=1)

    try:
        import pyperclip

        pyperclip.copy(content)
    except Exception as e:
        msg = f'Failed to copy to clipboard: {e}'
        if json_output:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}[/red]')
        raise typer.Exit(code=1) from e

    if json_output:
        output_json({'status': 'copied', 'name': name, 'content_type': content_type})
    else:
        console.print(f"[green]Copied {content_type} of '{name}' to clipboard.[/green]")


@app.command('clone')
def clone_prompt(
    name: str = typer.Argument(..., help='Source prompt name'),
    newname: str = typer.Argument(..., help='New prompt name'),
    group: str | None = typer.Option(None, '--group', '-g', help='Source group name (empty for ungrouped)'),
    target_group: str | None = typer.Option(None, '--target-group', '-t', help='Target group name'),
    json_output: bool = typer.Option(False, '--json', help='Output as JSON'),
) -> None:
    """Clone a prompt to a new name."""
    storage = get_storage()
    group_value = normalize_group(group)

    source = storage.get(name, group=group_value)

    if not source:
        msg = f"Prompt '{name}' not found in group '{display_group(group_value)}'"
        if json_output:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}.[/red]')
        raise typer.Exit(code=1)

    target_group_value = normalize_group(target_group) if target_group is not None else group_value

    new_prompt = Prompt(
        name=newname,
        description=source.description,
        system_prompt=source.system_prompt,
        user_prompt=source.user_prompt,
        tags=source.tags.copy(),
        group=target_group_value,
    )

    try:
        storage.create(new_prompt)
        if json_output:
            output_json({'status': 'cloned', 'source': name, 'target': newname, 'group': target_group_value})
        else:
            console.print(
                f"[green]Cloned '{name}' to '{newname}' in group '{display_group(target_group_value)}'.[/green]"
            )
    except PromptExistsError as e:
        msg = f"Prompt '{newname}' already exists in group '{display_group(target_group_value)}'"
        if json_output:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}.[/red]')
        raise typer.Exit(code=1) from e


@app.command('migrate')
def migrate_prompts(
    group: str = typer.Option('', '--group', help='Default group for prompts without a group (empty for ungrouped)'),
    dry_run: bool = typer.Option(False, '--dry-run', help='Show what would be migrated without making changes'),
    remove_source: bool = typer.Option(False, '--remove-source', help='Remove YAML files after successful migration'),
    json_output: bool = typer.Option(False, '--json', help='Output as JSON'),
) -> None:
    """Run the migration from YAML to markdown format."""
    from prompt_butler.services.migration import MigrationService

    service = MigrationService()
    yaml_files = service.find_yaml_prompts()

    if not yaml_files:
        if json_output:
            output_json({'status': 'complete', 'message': 'No YAML prompt files found to migrate.'})
        else:
            console.print('[yellow]No YAML prompt files found to migrate.[/yellow]')
        return

    if not json_output:
        console.print(f'Found {len(yaml_files)} YAML file(s) to migrate.')

    if dry_run:
        if json_output:
            files = []
            for yaml_file in yaml_files:
                prompt = service.read_yaml_prompt(yaml_file)
                if prompt:
                    target_group = prompt.group or group
                    target_path = f'{target_group}/{prompt.name}.md' if target_group else f'{prompt.name}.md'
                    files.append({'source': yaml_file.name, 'target': target_path})
                else:
                    files.append({'source': yaml_file.name, 'target': None, 'error': 'invalid/unreadable'})
            output_json({'status': 'dry_run', 'files': files})
        else:
            console.print('\n[cyan]Dry run - files that would be migrated:[/cyan]')
            for yaml_file in yaml_files:
                prompt = service.read_yaml_prompt(yaml_file)
                if prompt:
                    target_group = prompt.group or group
                    target_path = f'{target_group}/{prompt.name}.md' if target_group else f'{prompt.name}.md'
                    console.print(f'  {yaml_file.name} -> {target_path}')
                else:
                    console.print(f'  {yaml_file.name} -> [invalid/unreadable]')
        return

    result = service.migrate_all(default_group=group, remove_source=remove_source)

    if json_output:
        output_json({
            'status': 'complete',
            'migrated': result.success_count,
            'skipped': result.skipped_count,
            'failed': result.failure_count,
            'errors': result.errors,
        })
    else:
        console.print('\n[bold]Migration complete:[/bold]')
        console.print(f'  [green]Migrated:[/green] {result.success_count}')
        console.print(f'  [yellow]Skipped (already exist):[/yellow] {result.skipped_count}')
        console.print(f'  [red]Failed:[/red] {result.failure_count}')

        if result.errors:
            console.print('\n[red]Errors:[/red]')
            for error in result.errors:
                console.print(f'  - {error}')

    if result.failure_count > 0:
        raise typer.Exit(code=1)


@app.command('serve')
def serve_api(
    host: str = typer.Option('0.0.0.0', '--host', help='Host to bind to'),
    port: int = typer.Option(8000, '--port', help='Port to bind to'),
    reload: bool = typer.Option(False, '--reload', help='Enable auto-reload'),
) -> None:
    """Start the API server."""
    import uvicorn

    uvicorn.run('prompt_butler.main:app', host=host, port=port, reload=reload, log_level='info')


@app.command('index')
def index_prompts(
    json_output: bool = typer.Option(False, '--json', help='Output as JSON'),
) -> None:
    """Rebuild the in-memory prompt index."""
    storage = get_storage()

    prompts = storage.list()
    groups = storage.list_groups()

    if json_output:
        output_json({
            'status': 'indexed',
            'prompts_count': len(prompts),
            'groups_count': len(groups),
            'groups': groups,
        })
    else:
        console.print(f'[green]Indexed {len(prompts)} prompt(s) in {len(groups)} group(s).[/green]')
        if groups:
            console.print(f'[cyan]Groups:[/cyan] {", ".join(groups)}')


@app.command('config')
def config(
    key: str | None = typer.Argument(None, help='Config key to get or set'),
    value: str | None = typer.Argument(None, help='Value to set (if setting)'),
    edit: bool = typer.Option(False, '--edit', '-e', help='Open config in $EDITOR'),
    json_output: bool = typer.Option(False, '--json', help='Output as JSON'),
) -> None:
    """Show or edit configuration."""
    from prompt_butler.services.config import ConfigService

    config_service = ConfigService()

    if edit:
        config_service.load()
        if not config_service.config_file_path.exists():
            config_service.save()

        editor = config_service.get_editor()
        result = subprocess.run([editor, str(config_service.config_file_path)], check=False)
        if result.returncode != 0:
            error_console.print('[red]Editor exited with an error.[/red]')
            raise typer.Exit(code=1)
        console.print('[green]Configuration updated.[/green]')
        return

    if key:
        if value is not None:
            if config_service.set(key, value):
                if json_output:
                    output_json({'status': 'updated', 'key': key, 'value': value})
                else:
                    console.print(f'[green]Set {key} = {value}[/green]')
                return
            msg = f"Unknown config key: '{key}'"
            if json_output:
                output_json({'status': 'error', 'message': msg})
            else:
                error_console.print(f'[red]{msg}[/red]')
            raise typer.Exit(code=1)
        else:
            current_value = config_service.get(key)
            if current_value is None:
                msg = f"Unknown config key: '{key}'"
                if json_output:
                    output_json({'status': 'error', 'message': msg})
                else:
                    error_console.print(f'[red]{msg}[/red]')
                raise typer.Exit(code=1)
            if json_output:
                output_json({'key': key, 'value': current_value})
            else:
                console.print(f'{key} = {current_value}')
            return

    config_data = config_service.as_dict()

    if json_output:
        output_json({'config_file': str(config_service.config_file_path), **config_data})
    else:
        console.print(f'[bold cyan]Config file:[/bold cyan] {config_service.config_file_path}')
        console.print()
        for config_key, config_value in config_data.items():
            console.print(f'[cyan]{config_key}:[/cyan] {config_value}')


@app.command('tui')
def run_tui() -> None:
    """Launch the TUI application."""
    from prompt_butler.tui import run_tui as run_textual

    run_textual()


@tag_app.command('list')
def tag_list(
    json_output: bool = typer.Option(False, '--json', help='Output as JSON'),
) -> None:
    """List all tags with their counts."""
    storage = get_storage()
    tags = storage.list_all_tags()

    if json_output:
        output_json({'tags': [{'name': name, 'count': count} for name, count in tags.items()]})
        return

    if not tags:
        console.print('[yellow]No tags found.[/yellow]')
        return

    table = Table(title='Tags')
    table.add_column('Tag', style='green')
    table.add_column('Count', style='cyan', justify='right')

    for name, count in tags.items():
        table.add_row(name, str(count))

    console.print(table)


@tag_app.command('rename')
def tag_rename(
    old: str = typer.Argument(..., help='Current tag name'),
    new: str = typer.Argument(..., help='New tag name'),
    json_output: bool = typer.Option(False, '--json', help='Output as JSON'),
) -> None:
    """Rename a tag across all prompts."""
    storage = get_storage()

    tag_counts = storage.list_all_tags()
    if old not in tag_counts:
        msg = f"Tag '{old}' not found"
        if json_output:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}.[/red]')
        raise typer.Exit(code=1)

    updated_count = storage.rename_tag(old, new)

    if json_output:
        output_json({'status': 'renamed', 'old': old, 'new': new, 'updated_count': updated_count})
    else:
        console.print(f"[green]Renamed tag '{old}' to '{new}' in {updated_count} prompt(s).[/green]")


@group_app.command('list')
def group_list(
    all_groups: bool = typer.Option(False, '--all', '-a', help='Include empty groups'),
    json_output: bool = typer.Option(False, '--json', help='Output as JSON'),
) -> None:
    """List all groups."""
    storage = get_storage()
    groups = storage.list_groups(include_empty=all_groups)

    if json_output:
        output_json({'groups': groups})
        return

    if not groups:
        console.print('[yellow]No groups found.[/yellow]')
        return

    table = Table(title='Groups')
    table.add_column('Group', style='blue')

    for group_name in groups:
        table.add_row(group_name)

    console.print(table)


@group_app.command('create')
def group_create(
    name: str = typer.Argument(..., help='Group name to create'),
    json_output: bool = typer.Option(False, '--json', help='Output as JSON'),
) -> None:
    """Create an empty group folder."""
    storage = get_storage()

    if storage.create_group(name):
        if json_output:
            output_json({'status': 'created', 'group': name})
        else:
            console.print(f"[green]Created group '{name}'.[/green]")
        return

    msg = f"Group '{name}' already exists"
    if json_output:
        output_json({'status': 'error', 'message': msg})
    else:
        error_console.print(f'[red]{msg}.[/red]')
    raise typer.Exit(code=1)


@group_app.command('rename')
def group_rename(
    old: str = typer.Argument(..., help='Current group name'),
    new: str = typer.Argument(..., help='New group name'),
    json_output: bool = typer.Option(False, '--json', help='Output as JSON'),
) -> None:
    """Rename a group folder."""
    storage = get_storage()

    try:
        moved_count = storage.rename_group(old, new)
        if json_output:
            output_json({'status': 'renamed', 'old': old, 'new': new, 'moved_count': moved_count})
        else:
            console.print(f"[green]Renamed group '{old}' to '{new}' ({moved_count} prompt(s) moved).[/green]")
    except GroupNotFoundError as e:
        msg = f"Group '{old}' not found"
        if json_output:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}.[/red]')
        raise typer.Exit(code=1) from e
    except GroupExistsError as e:
        msg = f"Group '{new}' already exists with prompts"
        if json_output:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}.[/red]')
        raise typer.Exit(code=1) from e


def main() -> None:
    app()


if __name__ == '__main__':
    main()
