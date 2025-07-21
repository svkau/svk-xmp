"""Command-line interface for metadata operations."""

import click
from pathlib import Path
from ..core.metadata_processor import MetadataProcessor
from ..core.exceptions import MyProjectError


@click.group()
@click.option('--exiftool-path', help='Path to exiftool executable')
@click.pass_context
def main(ctx, exiftool_path):
    """Metadata processing tool using exiftool."""
    ctx.ensure_object(dict)
    ctx.obj['exiftool_path'] = exiftool_path


@main.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--format', '-f', type=click.Choice(['json', 'table']), default='table')
@click.pass_context
def extract(ctx, file_path, format):
    """Extract metadata from a file."""
    try:
        processor = MetadataProcessor(ctx.obj['exiftool_path'])
        metadata = processor.extract_basic_info(file_path)

        if format == 'json':
            import json
            click.echo(json.dumps(metadata, indent=2))
        else:
            for key, value in metadata.items():
                click.echo(f"{key}: {value}")

    except MyProjectError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@main.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--tags', '-t', multiple=True, help='Specific tags to remove')
@click.option('--all', 'remove_all', is_flag=True, help='Remove all metadata')
@click.pass_context
def remove(ctx, file_path, tags, remove_all):
    """Remove metadata from a file."""
    try:
        processor = MetadataProcessor(ctx.obj['exiftool_path'])

        if remove_all:
            success = processor.exiftool.remove_metadata(file_path)
        else:
            success = processor.exiftool.remove_metadata(file_path, list(tags))

        if success:
            click.echo(f"Metadata removed from {file_path}")
        else:
            click.echo(f"Failed to remove metadata from {file_path}")

    except MyProjectError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@main.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
@click.option('--extensions', '-e', multiple=True, help='File extensions to process')
@click.pass_context
def scan(ctx, directory, extensions):
    """Scan directory for files without metadata."""
    try:
        processor = MetadataProcessor(ctx.obj['exiftool_path'])
        files = processor.find_files_without_metadata(
            directory,
            list(extensions) if extensions else None
        )

        if files:
            click.echo(f"Found {len(files)} files without metadata:")
            for file_path in files:
                click.echo(f"  {file_path}")
        else:
            click.echo("No files without metadata found.")

    except MyProjectError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option('--host', '-h', default='127.0.0.1', help='Host to bind to')
@click.option('--port', '-p', default=5000, help='Port to bind to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def serve(host, port, debug):
    """Start the web server."""
    try:
        from ..web.app import create_app
        app = create_app()
        app.run(host=host, port=port, debug=debug)
    except ImportError:
        click.echo("Error: Flask not available. Install with: pip install flask", err=True)
        raise click.Abort()