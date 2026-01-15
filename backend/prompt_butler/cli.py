"""Prompt Butler CLI entry point."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from argparse import ArgumentParser, Namespace

from rich.console import Console
from rich.table import Table

from prompt_butler.models import Prompt
from prompt_butler.services.storage import (
    GroupExistsError,
    GroupNotFoundError,
    PromptExistsError,
    PromptStorage,
)

console = Console()
error_console = Console(stderr=True)


def get_storage() -> PromptStorage:
    """Get the storage service instance."""
    return PromptStorage()


def fuzzy_match(query: str, text: str) -> bool:
    """Simple fuzzy matching - check if all query chars appear in order."""
    query = query.lower()
    text = text.lower()
    query_idx = 0
    for char in text:
        if query_idx < len(query) and char == query[query_idx]:
            query_idx += 1
    return query_idx == len(query)


def output_json(data: dict | list) -> None:
    """Output data as JSON."""
    print(json.dumps(data, indent=2))


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


def cmd_add(args: Namespace) -> int:
    """Add a new prompt."""
    storage = get_storage()

    name = args.name
    group = args.group

    if args.edit or not name:
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
            return 1

        import frontmatter

        try:
            post = frontmatter.loads(edited)
        except Exception as e:
            error_console.print(f'[red]Invalid frontmatter format: {e}[/red]')
            return 1

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
        if not args.json:
            console.print('[cyan]Enter system prompt (Ctrl+D to finish):[/cyan]')
        try:
            system_prompt = sys.stdin.read().strip()
        except KeyboardInterrupt:
            if not args.json:
                console.print('\n[yellow]Cancelled.[/yellow]')
            return 1

        if not system_prompt:
            error_console.print('[red]System prompt cannot be empty.[/red]')
            return 1

        description = ''
        tags = []
        user_prompt = ''

    prompt = Prompt(
        name=name,
        description=description,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        tags=tags,
        group=group,
    )

    try:
        storage.create(prompt)
        if args.json:
            output_json({'status': 'created', 'prompt': prompt_to_dict(prompt)})
        else:
            console.print(f"[green]Created prompt '{name}' in group '{group}'.[/green]")
        return 0
    except PromptExistsError:
        if args.json:
            output_json({'status': 'error', 'message': f"Prompt '{name}' already exists in group '{group}'"})
        else:
            error_console.print(f"[red]Prompt '{name}' already exists in group '{group}'.[/red]")
        return 1


def cmd_list(args: Namespace) -> int:
    """List all prompts."""
    storage = get_storage()

    prompts = storage.list(group=args.group)

    if args.tag:
        prompts = [p for p in prompts if args.tag in p.tags]

    if args.query:
        query = args.query
        prompts = [
            p
            for p in prompts
            if fuzzy_match(query, p.name)
            or fuzzy_match(query, p.description)
            or any(fuzzy_match(query, t) for t in p.tags)
        ]

    if args.json:
        output_json([prompt_to_dict(p) for p in prompts])
        return 0

    if not prompts:
        console.print('[yellow]No prompts found.[/yellow]')
        return 0

    table = Table(title='Prompts')
    table.add_column('Name', style='cyan')
    table.add_column('Group', style='blue')
    table.add_column('Description')
    table.add_column('Tags', style='green')

    for p in prompts:
        desc = p.description[:50] + '...' if len(p.description) > 50 else p.description
        table.add_row(p.name, p.group, desc, ', '.join(p.tags))

    console.print(table)
    return 0


def cmd_show(args: Namespace) -> int:
    """Show a prompt's content."""
    storage = get_storage()

    prompt = storage.get(args.name, group=args.group)

    if not prompt:
        if args.json:
            output_json({'status': 'error', 'message': f"Prompt '{args.name}' not found in group '{args.group}'"})
        else:
            error_console.print(f"[red]Prompt '{args.name}' not found in group '{args.group}'.[/red]")
        return 1

    if args.json:
        output_json(prompt_to_dict(prompt))
        return 0

    console.print(f'[bold cyan]Name:[/bold cyan] {prompt.name}')
    console.print(f'[bold cyan]Group:[/bold cyan] {prompt.group}')
    console.print(f'[bold cyan]Description:[/bold cyan] {prompt.description}')
    console.print(f'[bold cyan]Tags:[/bold cyan] {", ".join(prompt.tags)}')
    console.print()
    console.print('[bold cyan]System Prompt:[/bold cyan]')
    console.print(prompt.system_prompt)
    if prompt.user_prompt:
        console.print()
        console.print('[bold cyan]User Prompt:[/bold cyan]')
        console.print(prompt.user_prompt)

    return 0


def cmd_edit(args: Namespace) -> int:
    """Edit a prompt in $EDITOR."""
    storage = get_storage()

    prompt = storage.get(args.name, group=args.group)

    if not prompt:
        if args.json:
            output_json({'status': 'error', 'message': f"Prompt '{args.name}' not found in group '{args.group}'"})
        else:
            error_console.print(f"[red]Prompt '{args.name}' not found in group '{args.group}'.[/red]")
        return 1

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
        return 1

    if edited == original_text:
        console.print('[yellow]No changes made.[/yellow]')
        return 0

    try:
        post = frontmatter.loads(edited)
    except Exception as e:
        error_console.print(f'[red]Invalid frontmatter format: {e}[/red]')
        return 1

    new_content = post.content
    if '---user---' in new_content:
        parts = new_content.split('---user---', 1)
        system_prompt = parts[0].strip()
        user_prompt = parts[1].strip() if len(parts) > 1 else ''
    else:
        system_prompt = new_content.strip()
        user_prompt = ''

    storage.update(
        args.name,
        args.group,
        description=post.get('description', prompt.description),
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        tags=post.get('tags', prompt.tags),
    )

    if args.json:
        updated = storage.get(args.name, group=args.group)
        output_json({'status': 'updated', 'prompt': prompt_to_dict(updated)})
    else:
        console.print(f"[green]Updated prompt '{args.name}'.[/green]")

    return 0


def cmd_delete(args: Namespace) -> int:
    """Delete a prompt."""
    storage = get_storage()

    prompt = storage.get(args.name, group=args.group)

    if not prompt:
        if args.json:
            output_json({'status': 'error', 'message': f"Prompt '{args.name}' not found in group '{args.group}'"})
        else:
            error_console.print(f"[red]Prompt '{args.name}' not found in group '{args.group}'.[/red]")
        return 1

    if not args.force:
        console.print(f"[yellow]Delete prompt '{args.name}' from group '{args.group}'?[/yellow]")
        response = input('Type "yes" to confirm: ')
        if response.lower() != 'yes':
            console.print('[cyan]Cancelled.[/cyan]')
            return 0

    storage.delete(args.name, group=args.group)

    if args.json:
        output_json({'status': 'deleted', 'name': args.name, 'group': args.group})
    else:
        console.print(f"[green]Deleted prompt '{args.name}'.[/green]")

    return 0


def cmd_copy(args: Namespace) -> int:
    """Copy a prompt to clipboard."""
    storage = get_storage()

    prompt = storage.get(args.name, group=args.group)

    if not prompt:
        if args.json:
            output_json({'status': 'error', 'message': f"Prompt '{args.name}' not found in group '{args.group}'"})
        else:
            error_console.print(f"[red]Prompt '{args.name}' not found in group '{args.group}'.[/red]")
        return 1

    if args.user:
        content = prompt.user_prompt
        content_type = 'user prompt'
    else:
        content = prompt.system_prompt
        content_type = 'system prompt'

    if not content:
        if args.json:
            output_json({'status': 'error', 'message': f'{content_type.capitalize()} is empty'})
        else:
            error_console.print(f'[red]{content_type.capitalize()} is empty.[/red]')
        return 1

    try:
        import pyperclip

        pyperclip.copy(content)
    except Exception as e:
        if args.json:
            output_json({'status': 'error', 'message': f'Failed to copy to clipboard: {e}'})
        else:
            error_console.print(f'[red]Failed to copy to clipboard: {e}[/red]')
        return 1

    if args.json:
        output_json({'status': 'copied', 'name': args.name, 'content_type': content_type})
    else:
        console.print(f"[green]Copied {content_type} of '{args.name}' to clipboard.[/green]")

    return 0


def cmd_clone(args: Namespace) -> int:
    """Clone a prompt to a new name."""
    storage = get_storage()

    source = storage.get(args.name, group=args.group)

    if not source:
        if args.json:
            output_json({'status': 'error', 'message': f"Prompt '{args.name}' not found in group '{args.group}'"})
        else:
            error_console.print(f"[red]Prompt '{args.name}' not found in group '{args.group}'.[/red]")
        return 1

    target_group = args.target_group or args.group

    new_prompt = Prompt(
        name=args.newname,
        description=source.description,
        system_prompt=source.system_prompt,
        user_prompt=source.user_prompt,
        tags=source.tags.copy(),
        group=target_group,
    )

    try:
        storage.create(new_prompt)
        if args.json:
            output_json({'status': 'cloned', 'source': args.name, 'target': args.newname, 'group': target_group})
        else:
            console.print(f"[green]Cloned '{args.name}' to '{args.newname}' in group '{target_group}'.[/green]")
        return 0
    except PromptExistsError:
        msg = f"Prompt '{args.newname}' already exists in group '{target_group}'"
        if args.json:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}.[/red]')
        return 1


def cmd_migrate(args: Namespace) -> int:
    """Run the migration from YAML to markdown format."""
    from prompt_butler.services.migration import MigrationService

    service = MigrationService()
    yaml_files = service.find_yaml_prompts()

    if not yaml_files:
        if args.json:
            output_json({'status': 'complete', 'message': 'No YAML prompt files found to migrate.'})
        else:
            console.print('[yellow]No YAML prompt files found to migrate.[/yellow]')
        return 0

    if not args.json:
        console.print(f'Found {len(yaml_files)} YAML file(s) to migrate.')

    if args.dry_run:
        if args.json:
            files = []
            for f in yaml_files:
                prompt = service.read_yaml_prompt(f)
                if prompt:
                    group = prompt.group or args.group
                    files.append({'source': f.name, 'target': f'{group}/{prompt.name}.md'})
                else:
                    files.append({'source': f.name, 'target': None, 'error': 'invalid/unreadable'})
            output_json({'status': 'dry_run', 'files': files})
        else:
            console.print('\n[cyan]Dry run - files that would be migrated:[/cyan]')
            for f in yaml_files:
                prompt = service.read_yaml_prompt(f)
                if prompt:
                    group = prompt.group or args.group
                    console.print(f'  {f.name} -> {group}/{prompt.name}.md')
                else:
                    console.print(f'  {f.name} -> [invalid/unreadable]')
        return 0

    result = service.migrate_all(default_group=args.group, remove_source=args.remove_source)

    if args.json:
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

    return 1 if result.failure_count > 0 else 0


def cmd_serve(args: Namespace) -> int:
    """Start the API server."""
    import uvicorn

    uvicorn.run(
        'prompt_butler.main:app',
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level='info',
    )
    return 0


def cmd_index(args: Namespace) -> int:
    """Rebuild the in-memory prompt index."""
    storage = get_storage()

    prompts = storage.list()
    groups = storage.list_groups()

    if args.json:
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

    return 0


def cmd_config(args: Namespace) -> int:
    """Show or edit configuration."""
    from prompt_butler.services.config import ConfigService

    config_service = ConfigService()

    if args.edit:
        config_service.load()
        if not config_service.config_file_path.exists():
            config_service.save()

        editor = config_service.get_editor()
        result = subprocess.run([editor, str(config_service.config_file_path)], check=False)
        if result.returncode != 0:
            error_console.print('[red]Editor exited with an error.[/red]')
            return 1
        console.print('[green]Configuration updated.[/green]')
        return 0

    if args.key:
        if args.value is not None:
            if config_service.set(args.key, args.value):
                if args.json:
                    output_json({'status': 'updated', 'key': args.key, 'value': args.value})
                else:
                    console.print(f'[green]Set {args.key} = {args.value}[/green]')
                return 0
            else:
                if args.json:
                    output_json({'status': 'error', 'message': f"Unknown config key: '{args.key}'"})
                else:
                    error_console.print(f"[red]Unknown config key: '{args.key}'[/red]")
                return 1
        else:
            value = config_service.get(args.key)
            if value is None:
                if args.json:
                    output_json({'status': 'error', 'message': f"Unknown config key: '{args.key}'"})
                else:
                    error_console.print(f"[red]Unknown config key: '{args.key}'[/red]")
                return 1
            if args.json:
                output_json({'key': args.key, 'value': value})
            else:
                console.print(f'{args.key} = {value}')
            return 0

    config_data = config_service.as_dict()

    if args.json:
        output_json({'config_file': str(config_service.config_file_path), **config_data})
    else:
        console.print(f'[bold cyan]Config file:[/bold cyan] {config_service.config_file_path}')
        console.print()
        for key, value in config_data.items():
            console.print(f'[cyan]{key}:[/cyan] {value}')

    return 0


def cmd_tag(args: Namespace) -> int:
    """Handle tag subcommands."""
    if args.tag_command == 'list':
        return cmd_tag_list(args)
    elif args.tag_command == 'rename':
        return cmd_tag_rename(args)
    else:
        error_console.print('[red]Unknown tag command. Use: list, rename[/red]')
        return 1


def cmd_tag_list(args: Namespace) -> int:
    """List all tags with their counts."""
    storage = get_storage()
    tags = storage.list_all_tags()

    if args.json:
        output_json({'tags': [{'name': name, 'count': count} for name, count in tags.items()]})
        return 0

    if not tags:
        console.print('[yellow]No tags found.[/yellow]')
        return 0

    table = Table(title='Tags')
    table.add_column('Tag', style='green')
    table.add_column('Count', style='cyan', justify='right')

    for name, count in tags.items():
        table.add_row(name, str(count))

    console.print(table)
    return 0


def cmd_tag_rename(args: Namespace) -> int:
    """Rename a tag across all prompts."""
    storage = get_storage()

    tag_counts = storage.list_all_tags()
    if args.old not in tag_counts:
        msg = f"Tag '{args.old}' not found"
        if args.json:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}.[/red]')
        return 1

    updated_count = storage.rename_tag(args.old, args.new)

    if args.json:
        output_json({'status': 'renamed', 'old': args.old, 'new': args.new, 'updated_count': updated_count})
    else:
        console.print(f"[green]Renamed tag '{args.old}' to '{args.new}' in {updated_count} prompt(s).[/green]")

    return 0


def cmd_group(args: Namespace) -> int:
    """Handle group subcommands."""
    if args.group_command == 'list':
        return cmd_group_list(args)
    elif args.group_command == 'create':
        return cmd_group_create(args)
    elif args.group_command == 'rename':
        return cmd_group_rename(args)
    else:
        error_console.print('[red]Unknown group command. Use: list, create, rename[/red]')
        return 1


def cmd_group_list(args: Namespace) -> int:
    """List all groups."""
    storage = get_storage()
    groups = storage.list_groups(include_empty=args.all)

    if args.json:
        output_json({'groups': groups})
        return 0

    if not groups:
        console.print('[yellow]No groups found.[/yellow]')
        return 0

    table = Table(title='Groups')
    table.add_column('Group', style='blue')

    for group in groups:
        table.add_row(group)

    console.print(table)
    return 0


def cmd_group_create(args: Namespace) -> int:
    """Create an empty group folder."""
    storage = get_storage()

    if storage.create_group(args.name):
        if args.json:
            output_json({'status': 'created', 'group': args.name})
        else:
            console.print(f"[green]Created group '{args.name}'.[/green]")
        return 0
    else:
        msg = f"Group '{args.name}' already exists"
        if args.json:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}.[/red]')
        return 1


def cmd_group_rename(args: Namespace) -> int:
    """Rename a group folder."""
    storage = get_storage()

    try:
        moved_count = storage.rename_group(args.old, args.new)
        if args.json:
            output_json({'status': 'renamed', 'old': args.old, 'new': args.new, 'moved_count': moved_count})
        else:
            console.print(f"[green]Renamed group '{args.old}' to '{args.new}' ({moved_count} prompt(s) moved).[/green]")
        return 0
    except GroupNotFoundError:
        msg = f"Group '{args.old}' not found"
        if args.json:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}.[/red]')
        return 1
    except GroupExistsError:
        msg = f"Group '{args.new}' already exists with prompts"
        if args.json:
            output_json({'status': 'error', 'message': msg})
        else:
            error_console.print(f'[red]{msg}.[/red]')
        return 1


def cmd_tui(args: Namespace) -> int:
    """Launch the TUI application."""
    from prompt_butler.tui import run_tui

    run_tui()
    return 0


def main() -> int:
    """Main CLI entry point for Prompt Butler."""
    parser = ArgumentParser(
        prog='pb',
        description='Prompt Butler - AI prompt management tool',
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0',
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new prompt')
    add_parser.add_argument('--name', '-n', help='Prompt name')
    add_parser.add_argument('--group', '-g', default='default', help='Group name (default: default)')
    add_parser.add_argument('--edit', '-e', action='store_true', help='Open in $EDITOR for editing')
    add_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # List command
    list_parser = subparsers.add_parser('list', help='List all prompts')
    list_parser.add_argument('query', nargs='?', help='Fuzzy search query')
    list_parser.add_argument('--group', '-g', help='Filter by group')
    list_parser.add_argument('--tag', '-t', help='Filter by tag')
    list_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Show command
    show_parser = subparsers.add_parser('show', help='Show a prompt')
    show_parser.add_argument('name', help='Prompt name')
    show_parser.add_argument('--group', '-g', default='default', help='Group name (default: default)')
    show_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Edit command
    edit_parser = subparsers.add_parser('edit', help='Edit a prompt in $EDITOR')
    edit_parser.add_argument('name', help='Prompt name')
    edit_parser.add_argument('--group', '-g', default='default', help='Group name (default: default)')
    edit_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a prompt')
    delete_parser.add_argument('name', help='Prompt name')
    delete_parser.add_argument('--group', '-g', default='default', help='Group name (default: default)')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    delete_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Copy command
    copy_parser = subparsers.add_parser('copy', help='Copy prompt to clipboard')
    copy_parser.add_argument('name', help='Prompt name')
    copy_parser.add_argument('--group', '-g', default='default', help='Group name (default: default)')
    copy_parser.add_argument('--user', '-u', action='store_true', help='Copy user prompt instead of system prompt')
    copy_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Clone command
    clone_parser = subparsers.add_parser('clone', help='Clone a prompt to a new name')
    clone_parser.add_argument('name', help='Source prompt name')
    clone_parser.add_argument('newname', help='New prompt name')
    clone_parser.add_argument('--group', '-g', default='default', help='Source group name (default: default)')
    clone_parser.add_argument('--target-group', '-t', help='Target group name (default: same as source)')
    clone_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate YAML prompts to markdown format')
    migrate_parser.add_argument(
        '--group',
        default='default',
        help='Default group for prompts without a group (default: default)',
    )
    migrate_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without making changes',
    )
    migrate_parser.add_argument(
        '--remove-source',
        action='store_true',
        help='Remove YAML files after successful migration',
    )
    migrate_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Server command
    server_parser = subparsers.add_parser('serve', help='Start the API server')
    server_parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    server_parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    server_parser.add_argument('--reload', action='store_true', help='Enable auto-reload')

    # Index command
    index_parser = subparsers.add_parser('index', help='Rebuild the prompt index')
    index_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Config command
    config_parser = subparsers.add_parser('config', help='Show or edit configuration')
    config_parser.add_argument('key', nargs='?', help='Config key to get or set')
    config_parser.add_argument('value', nargs='?', help='Value to set (if setting)')
    config_parser.add_argument('--edit', '-e', action='store_true', help='Open config in $EDITOR')
    config_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # TUI command
    subparsers.add_parser('tui', help='Launch TUI application')

    # Tag command with subcommands
    tag_parser = subparsers.add_parser('tag', help='Manage tags')
    tag_subparsers = tag_parser.add_subparsers(dest='tag_command', help='Tag commands')

    # tag list
    tag_list_parser = tag_subparsers.add_parser('list', help='List all tags with counts')
    tag_list_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # tag rename
    tag_rename_parser = tag_subparsers.add_parser('rename', help='Rename a tag across all prompts')
    tag_rename_parser.add_argument('old', help='Current tag name')
    tag_rename_parser.add_argument('new', help='New tag name')
    tag_rename_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Group command with subcommands
    group_parser = subparsers.add_parser('group', help='Manage groups')
    group_subparsers = group_parser.add_subparsers(dest='group_command', help='Group commands')

    # group list
    group_list_parser = group_subparsers.add_parser('list', help='List all groups')
    group_list_parser.add_argument('--all', '-a', action='store_true', help='Include empty groups')
    group_list_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # group create
    group_create_parser = group_subparsers.add_parser('create', help='Create an empty group')
    group_create_parser.add_argument('name', help='Group name to create')
    group_create_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # group rename
    group_rename_parser = group_subparsers.add_parser('rename', help='Rename a group')
    group_rename_parser.add_argument('old', help='Current group name')
    group_rename_parser.add_argument('new', help='New group name')
    group_rename_parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    commands = {
        'add': cmd_add,
        'list': cmd_list,
        'show': cmd_show,
        'edit': cmd_edit,
        'delete': cmd_delete,
        'copy': cmd_copy,
        'clone': cmd_clone,
        'migrate': cmd_migrate,
        'serve': cmd_serve,
        'index': cmd_index,
        'config': cmd_config,
        'tui': cmd_tui,
        'tag': cmd_tag,
        'group': cmd_group,
    }

    if args.command in commands:
        return commands[args.command](args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
