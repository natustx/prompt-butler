"""Prompt Butler CLI entry point."""

import argparse
import sys


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

    args = parser.parse_args()

    if args.command == 'serve':
        import uvicorn

        uvicorn.run(
            'prompt_butler.main:app',
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level='info',
        )
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == '__main__':
    main()
