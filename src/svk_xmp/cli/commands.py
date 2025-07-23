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
@click.argument('path', type=click.Path(exists=True))
@click.option('--args-file', '-a', type=click.Path(exists=True), 
              default='arg_files/metadata_sync_images.args',
              help='Path to exiftool arguments file')
@click.option('--extensions', '-e', multiple=True, 
              help='File extensions to process (e.g., .jpg .tiff)')
@click.option('--recursive/--no-recursive', '-r/-R', default=True,
              help='Process subdirectories recursively')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--format', '-f', type=click.Choice(['json', 'summary']), default='summary')
@click.pass_context
def sync(ctx, path, args_file, extensions, recursive, verbose, format):
    """Synchronize metadata between EXIF, IPTC, and XMP formats."""
    try:
        processor = MetadataProcessor(ctx.obj['exiftool_path'])
        
        # Convert extensions to list
        file_extensions = list(extensions) if extensions else None
        
        # Perform sync
        result = processor.sync_metadata(
            path=path,
            args_file=args_file,
            file_extensions=file_extensions,
            recursive=recursive,
            verbose=verbose
        )
        
        if format == 'json':
            import json
            click.echo(json.dumps(result, indent=2))
        else:
            # Summary format
            summary = result['summary']
            click.echo(f"Metadata synchronization completed:")
            click.echo(f"  Total files: {summary['total_files']}")
            click.echo(f"  Processed: {summary['processed']}")
            click.echo(f"  Errors: {summary['errors']}")
            click.echo(f"  Warnings: {summary['warnings']}")
            click.echo(f"  Skipped: {summary['skipped']}")
            
            if summary['errors'] > 0 and not verbose:
                click.echo(f"\nUse --verbose to see error details.")
            
            if verbose and (result['errors'] or result['warnings']):
                if result['errors']:
                    click.echo(f"\nErrors:")
                    for error in result['errors']:
                        click.echo(f"  {error['file']}: {error['error']}")
                
                if result['warnings']:
                    click.echo(f"\nWarnings:")
                    for warning in result['warnings']:
                        click.echo(f"  {warning['file']}: {warning['warning']}")

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