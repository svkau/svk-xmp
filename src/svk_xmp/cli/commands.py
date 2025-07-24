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
@click.argument('path', type=click.Path(exists=True))
@click.option('--recursive/--no-recursive', '-r/-R', default=False,
              help='Process subdirectories recursively')
@click.option('--save', '-s', type=click.Path(), 
              help='Save XMP packets: for single file, save to specified file; for directory, save individual .xmp files to specified directory')
@click.option('--format', '-f', type=click.Choice(['table', 'raw', 'json']), default='table',
              help='Output format: table (key fields), raw (XML), json (structured data)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def xmp(ctx, path, recursive, save, format, verbose):
    """Extract XMP metadata from images."""
    try:
        processor = MetadataProcessor(ctx.obj['exiftool_path'])
        path_obj = Path(path)
        
        if path_obj.is_file():
            # Single file processing
            if save:
                # Save XMP packet to file
                xmp_packet = processor.extract_xmp_packet(path)
                if xmp_packet:
                    with open(save, 'w', encoding='utf-8') as f:
                        f.write(xmp_packet)
                    click.echo(f"XMP packet saved to {save}")
                else:
                    click.echo(f"No XMP metadata found in {path}")
                return
            
            # Extract XMP for display
            if format == 'raw':
                xmp_xml = processor.extract_xmp_xml(path)
                if xmp_xml:
                    click.echo(xmp_xml)
                else:
                    click.echo(f"No XMP metadata found in {path}")
            elif format == 'json':
                xmp_xml = processor.extract_xmp_xml(path)
                if xmp_xml:
                    fields = processor.parse_xmp_fields(xmp_xml)
                    import json
                    click.echo(json.dumps({
                        'file': str(path),
                        'xmp_xml': xmp_xml,
                        'fields': fields
                    }, indent=2))
                else:
                    import json
                    click.echo(json.dumps({
                        'file': str(path),
                        'xmp_xml': '',
                        'fields': {}
                    }, indent=2))
            else:  # table format
                xmp_xml = processor.extract_xmp_xml(path)
                if xmp_xml:
                    fields = processor.parse_xmp_fields(xmp_xml)
                    click.echo(f"File: {path}")
                    click.echo("=" * (len(str(path)) + 6))
                    for key, value in fields.items():
                        if value:
                            display_key = key.replace('_', ' ').title()
                            # Truncate long values for table display
                            if len(value) > 60:
                                value = value[:57] + "..."
                            click.echo(f"{display_key:<15}: {value}")
                else:
                    click.echo(f"No XMP metadata found in {path}")
        
        else:
            # Directory processing
            if save:
                # Save XMP files for directory processing
                save_path = Path(save)
                
                # Create output directory if it doesn't exist
                if not save_path.exists():
                    save_path.mkdir(parents=True, exist_ok=True)
                elif not save_path.is_dir():
                    click.echo(f"Error: {save} is not a directory", err=True)
                    raise click.Abort()
                
                result = processor.batch_extract_xmp(path, recursive)
                saved_count = 0
                
                for item in result['processed']:
                    source_file = Path(item['file'])
                    # Create .xmp filename based on source filename
                    xmp_filename = source_file.stem + '.xmp'
                    xmp_path = save_path / xmp_filename
                    
                    # Get the full XMP packet for saving
                    try:
                        xmp_packet = processor.extract_xmp_packet(item['file'])
                        if xmp_packet:
                            with open(xmp_path, 'w', encoding='utf-8') as f:
                                f.write(xmp_packet)
                            saved_count += 1
                            if verbose:
                                click.echo(f"Saved: {xmp_path}")
                    except Exception as e:
                        if verbose:
                            click.echo(f"Error saving {source_file}: {e}")
                
                # Summary
                click.echo(f"XMP extraction completed:")
                click.echo(f"  Total files processed: {result['summary']['total_files']}")
                click.echo(f"  XMP files saved: {saved_count}")
                click.echo(f"  Skipped (no XMP): {result['summary']['skipped']}")
                click.echo(f"  Errors: {result['summary']['errors']}")
                click.echo(f"  Output directory: {save_path}")
                
            else:
                # Regular directory processing without saving
                result = processor.batch_extract_xmp(path, recursive)
                
                if format == 'json':
                    import json
                    click.echo(json.dumps(result, indent=2))
                elif format == 'raw':
                    for item in result['processed']:
                        click.echo(f"\n--- {item['file']} ---")
                        click.echo(item['xmp_xml'])
                else:  # table format
                    if result['processed']:
                        for item in result['processed']:
                            fields = item['fields']
                            click.echo(f"\nFile: {item['file']}")
                            click.echo("=" * (len(item['file']) + 6))
                            for key, value in fields.items():
                                if value:
                                    display_key = key.replace('_', ' ').title()
                                    if len(value) > 60:
                                        value = value[:57] + "..."
                                    click.echo(f"{display_key:<15}: {value}")
                    
                    # Summary
                    summary = result['summary']
                    click.echo(f"\nSummary:")
                    click.echo(f"  Total files: {summary['total_files']}")
                    click.echo(f"  Processed: {summary['processed']}")
                    click.echo(f"  Skipped: {summary['skipped']} (no XMP metadata)")
                    click.echo(f"  Errors: {summary['errors']}")
                    
                    if verbose and result['skipped']:
                        click.echo(f"\nSkipped files:")
                        for skipped in result['skipped']:
                            click.echo(f"  {skipped['file']}: {skipped['reason']}")
                    
                    if verbose and result['errors']:
                        click.echo(f"\nErrors:")
                        for error in result['errors']:
                            click.echo(f"  {error['file']}: {error['error']}")

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