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