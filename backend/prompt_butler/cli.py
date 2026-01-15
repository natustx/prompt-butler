"""Prompt Butler CLI entry point."""

import argparse
import sys


def cmd_migrate(args):
    """Run the migration from YAML to markdown format."""
    from prompt_butler.services.migration import MigrationService

    service = MigrationService()
    yaml_files = service.find_yaml_prompts()

    if not yaml_files:
        print('No YAML prompt files found to migrate.')
        return

    print(f'Found {len(yaml_files)} YAML file(s) to migrate.')

    if args.dry_run:
        print('\nDry run - files that would be migrated:')
        for f in yaml_files:
            prompt = service.read_yaml_prompt(f)
            if prompt:
                group = prompt.group or args.group
                print(f'  {f.name} -> {group}/{prompt.name}.md')
            else:
                print(f'  {f.name} -> [invalid/unreadable]')
        return

    result = service.migrate_all(default_group=args.group, remove_source=args.remove_source)

    print('\nMigration complete:')
    print(f'  Migrated: {result.success_count}')
    print(f'  Skipped (already exist): {result.skipped_count}')
    print(f'  Failed: {result.failure_count}')

    if result.errors:
        print('\nErrors:')
        for error in result.errors:
            print(f'  - {error}')

    if result.failure_count > 0:
        sys.exit(1)


def cmd_serve(args):
    """Start the API server."""
    import uvicorn

    uvicorn.run(
        'prompt_butler.main:app',
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level='info',
    )


def main():
    """Main CLI entry point for Prompt Butler."""
    parser = argparse.ArgumentParser(
        prog='pb',
        description='Prompt Butler - AI prompt management tool',
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0',
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Server command
    server_parser = subparsers.add_parser('serve', help='Start the API server')
    server_parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    server_parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    server_parser.add_argument('--reload', action='store_true', help='Enable auto-reload')

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

    args = parser.parse_args()

    if args.command == 'serve':
        cmd_serve(args)
    elif args.command == 'migrate':
        cmd_migrate(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == '__main__':
    main()
