"""Tests for web functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from svk_xmp.web.app import create_app
from svk_xmp.web.routes import bp


class TestWebApp:
    """Test Flask web application."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = create_app({'TESTING': True})
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def teardown_method(self):
        """Clean up after tests."""
        self.app_context.pop()

    def test_create_app_default_config(self):
        """Test app creation with default configuration."""
        app = create_app()
        assert app is not None
        assert app.config['TESTING'] is False

    def test_create_app_custom_config(self):
        """Test app creation with custom configuration."""
        config = {'TESTING': True, 'SECRET_KEY': 'test-key'}
        app = create_app(config)
        assert app.config['TESTING'] is True
        assert app.config['SECRET_KEY'] == 'test-key'

    def test_blueprint_registration(self):
        """Test that blueprint is properly registered."""
        app = create_app()
        assert 'main' in app.blueprints

    def test_index_route(self):
        """Test index route health check."""
        response = self.client.get('/')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'MyProject web service is running' in data['message']

    @patch('svk_xmp.web.routes.MetadataProcessor')
    def test_process_route_success(self, mock_processor):
        """Test successful processing via HTTP API."""
        mock_instance = mock_processor.return_value
        mock_instance.extract_basic_info.return_value = {
            'filename': 'test.jpg',
            'camera_make': 'Canon'
        }
        
        response = self.client.post('/process', 
                                  json={'input': 'test.jpg'},
                                  content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == {'filename': 'test.jpg', 'camera_make': 'Canon'}

    def test_process_route_missing_input(self):
        """Test process route with missing input data."""
        response = self.client.post('/process', 
                                  json={},
                                  content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Missing input data'

    def test_process_route_no_json(self):
        """Test process route with no JSON data."""
        response = self.client.post('/process')
        
        # Flask returns 500 for JSON parsing errors
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data

    def test_process_route_invalid_json(self):
        """Test process route with invalid JSON."""
        response = self.client.post('/process', 
                                  data='invalid json',
                                  content_type='application/json')
        
        # Flask returns 500 for JSON parsing errors  
        assert response.status_code == 500

    @patch('svk_xmp.web.routes.MetadataProcessor')
    def test_process_route_processing_error(self, mock_processor):
        """Test process route with processing error."""
        mock_instance = mock_processor.return_value
        
        # Mock the extract_basic_info method to raise an exception
        mock_instance.extract_basic_info.side_effect = Exception('Processing failed')
        
        response = self.client.post('/process', 
                                  json={'input': 'test.jpg'},
                                  content_type='application/json')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['error'] == 'Processing failed'

    def test_process_route_content_type_validation(self):
        """Test that process route requires JSON content type."""
        response = self.client.post('/process', 
                                  data='{"input": "test"}',
                                  content_type='text/plain')
        
        # Flask will return 500 for our implementation
        assert response.status_code == 500


class TestWebRoutes:
    """Test individual route functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = create_app({'TESTING': True})
        self.client = self.app.test_client()

    def test_index_route_direct(self):
        """Test index route function directly."""
        with self.app.app_context():
            from svk_xmp.web.routes import index
            result = index()
            assert result['status'] == 'ok'
            assert 'MyProject web service is running' in result['message']

    @patch('svk_xmp.web.routes.MetadataProcessor')
    def test_process_route_direct(self, mock_processor):
        """Test process route function directly."""
        mock_instance = mock_processor.return_value
        mock_instance.extract_basic_info.return_value = {'filename': 'test.jpg'}
        
        with self.app.app_context():
            with self.app.test_request_context('/process', 
                                             method='POST',
                                             json={'input': 'test.jpg'}):
                from svk_xmp.web.routes import process
                from flask import request
                
                result = process()
                assert result == {'result': {'filename': 'test.jpg'}}

    def test_blueprint_url_prefix(self):
        """Test that blueprint has correct URL prefix."""
        assert bp.url_prefix is None  # Default prefix

    def test_blueprint_name(self):
        """Test that blueprint has correct name."""
        assert bp.name == 'main'


class TestWebIntegration:
    """Integration tests for web components."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = create_app({'TESTING': True})
        self.client = self.app.test_client()

    @patch('svk_xmp.web.routes.MetadataProcessor')
    def test_full_app_creation_and_routing(self, mock_processor):
        """Test complete app creation and routing."""
        mock_instance = mock_processor.return_value
        mock_instance.extract_basic_info.return_value = {'filename': 'test.jpg'}
        
        # Test that app is created correctly
        assert self.app is not None
        assert self.app.config['TESTING'] is True
        
        # Test that routes are accessible
        response = self.client.get('/')
        assert response.status_code == 200
        
        # Test that POST route exists and works
        response = self.client.post('/process', json={'input': 'test.jpg'})
        assert response.status_code == 200

    def test_error_handling_consistency(self):
        """Test that error handling is consistent across routes."""
        # Test missing input
        response = self.client.post('/process', json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        
        # Test malformed JSON
        response = self.client.post('/process', 
                                  data='{"invalid": json}',
                                  content_type='application/json')
        assert response.status_code == 500

    def test_response_format_consistency(self):
        """Test that response format is consistent."""
        # Test successful health check
        response = self.client.get('/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        assert 'message' in data
        
        # Test error response
        response = self.client.post('/process', json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert isinstance(data['error'], str)


class TestWebConfiguration:
    """Test web application configuration."""

    def test_default_configuration(self):
        """Test default configuration values."""
        app = create_app()
        assert app.config['TESTING'] is False
        assert app.config.get('SECRET_KEY') is None

    def test_custom_configuration_override(self):
        """Test that custom configuration overrides defaults."""
        custom_config = {
            'TESTING': True,
            'SECRET_KEY': 'test-secret',
            'CUSTOM_VALUE': 'custom'
        }
        app = create_app(custom_config)
        
        assert app.config['TESTING'] is True
        assert app.config['SECRET_KEY'] == 'test-secret'
        assert app.config['CUSTOM_VALUE'] == 'custom'

    def test_config_isolation(self):
        """Test that different app instances have isolated configuration."""
        app1 = create_app({'TESTING': True})
        app2 = create_app({'TESTING': False})
        
        assert app1.config['TESTING'] is True
        assert app2.config['TESTING'] is False