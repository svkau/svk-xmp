"""Web routes."""

from flask import Blueprint, request, jsonify
from ..core.metadata_processor import MetadataProcessor

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Health check endpoint."""
    return {'status': 'ok', 'message': 'MyProject web service is running'}


@bp.route('/process', methods=['POST'])
def process():
    """Process data via HTTP API."""
    try:
        data = request.get_json(force=True)

        if not data or 'input' not in data:
            return {'error': 'Missing input data'}, 400

        processor = MetadataProcessor()
        
        # Extract basic info from the provided file path
        file_path = data['input']
        result = processor.extract_basic_info(file_path)

        return {'result': result}

    except Exception as e:
        return {'error': str(e)}, 500


@bp.route('/xmp', methods=['GET'])
def extract_xmp():
    """Extract XMP metadata from a file."""
    try:
        file_path = request.args.get('file')
        format_type = request.args.get('format', 'json')  # json, xml, both
        
        if not file_path:
            return {'error': 'Missing file parameter'}, 400
        
        processor = MetadataProcessor()
        
        if format_type == 'xml':
            # Return just XML
            xmp_xml = processor.extract_xmp_xml(file_path)
            if not xmp_xml:
                return {'error': 'No XMP metadata found'}, 404
            return {'file': file_path, 'xmp_xml': xmp_xml}
        
        elif format_type == 'both':
            # Return both XML and parsed fields
            xmp_xml = processor.extract_xmp_xml(file_path)
            if not xmp_xml:
                return {'error': 'No XMP metadata found'}, 404
            fields = processor.parse_xmp_fields(xmp_xml)
            return {
                'file': file_path,
                'xmp_xml': xmp_xml,
                'fields': fields
            }
        
        else:  # json format (default)
            # Return parsed fields as JSON
            xmp_xml = processor.extract_xmp_xml(file_path)
            if not xmp_xml:
                return {'error': 'No XMP metadata found'}, 404
            fields = processor.parse_xmp_fields(xmp_xml)
            return {
                'file': file_path,
                'fields': fields
            }
    
    except FileNotFoundError:
        return {'error': 'File not found'}, 404
    except Exception as e:
        return {'error': str(e)}, 500


@bp.route('/xmp/batch', methods=['POST'])
def extract_xmp_batch():
    """Extract XMP metadata from multiple files."""
    try:
        data = request.get_json(force=True)
        
        if not data or 'path' not in data:
            return {'error': 'Missing path data'}, 400
        
        path = data['path']
        recursive = data.get('recursive', False)
        format_type = data.get('format', 'json')  # json, xml, both
        
        processor = MetadataProcessor()
        result = processor.batch_extract_xmp(path, recursive)
        
        # Modify result based on format preference
        if format_type == 'xml':
            # Only include XML, not parsed fields
            for item in result['processed']:
                if 'fields' in item:
                    del item['fields']
        elif format_type == 'json':
            # Only include parsed fields, not XML
            for item in result['processed']:
                if 'xmp_xml' in item:
                    del item['xmp_xml']
        # 'both' format keeps everything
        
        return result
    
    except Exception as e:
        return {'error': str(e)}, 500