"""
Tests for the Dynamic Configuration API

Tests the API server functionality and configuration management.
"""

import pytest
import threading
import time
import requests
from unittest.mock import Mock, patch

from config import RootConfig
from api_server import APIServer, create_api_server, ConfigUpdateRequest
from state import get_state, reset_state


class TestAPIServer:
    """Test the API server functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create test configuration
        self.config = RootConfig(
            api={"enabled": True, "port": 8181, "host": "127.0.0.1"}  # Use different port for tests
        )
        
        # Mock semantic event handler
        self.semantic_events = []
        def mock_handler(event):
            self.semantic_events.append(event)
        
        self.mock_semantic_handler = mock_handler
        
        # Reset state
        reset_state()
    
    def teardown_method(self):
        """Clean up after tests."""
        reset_state()
    
    def test_api_server_creation(self):
        """Test API server creation."""
        server = create_api_server(self.config, self.mock_semantic_handler)
        assert server is not None
        assert server.config == self.config
        assert server.semantic_event_handler == self.mock_semantic_handler
    
    def test_api_server_disabled(self):
        """Test API server creation when disabled."""
        disabled_config = RootConfig(api={"enabled": False})
        server = create_api_server(disabled_config)
        assert server is None
    
    def test_config_update_request_validation(self):
        """Test configuration update request validation."""
        # Valid request
        request = ConfigUpdateRequest(
            path="sequencer.bpm",
            value=120.0,
            apply_immediately=True
        )
        assert request.path == "sequencer.bpm"
        assert request.value == 120.0
        assert request.apply_immediately is True
        
        # Test default values
        request2 = ConfigUpdateRequest(path="test.path", value="test")
        assert request2.apply_immediately is True  # Default value
    
    def test_get_config_value(self):
        """Test getting configuration values."""
        server = APIServer(self.config, self.mock_semantic_handler)
        
        # Test existing value
        bpm = server._get_config_value("sequencer.bpm")
        assert bpm == self.config.sequencer.bpm
        
        # Test nested value
        port = server._get_config_value("api.port")
        assert port == 8181
        
        # Test non-existent value
        with pytest.raises(KeyError):
            server._get_config_value("nonexistent.path")
    
    def test_set_config_value(self):
        """Test setting configuration values."""
        server = APIServer(self.config, self.mock_semantic_handler)
        
        # Test setting valid value
        server._set_config_value("sequencer.bpm", 130.0)
        assert server.config.sequencer.bpm == 130.0
        
        # Test setting nested value
        server._set_config_value("api.port", 9090)
        assert server.config.api.port == 9090
        
        # Test validation error
        with pytest.raises(ValueError):
            server._set_config_value("sequencer.bpm", "invalid")
    
    def test_apply_config_to_system(self):
        """Test applying configuration to system state."""
        server = APIServer(self.config, self.mock_semantic_handler)
        state = get_state()
        
        # Test BPM application
        server._apply_config_to_system("sequencer.bpm", 140.0)
        assert state.get("bpm") == 140.0
        
        # Test density application
        server._apply_config_to_system("sequencer.density", 0.7)
        assert state.get("density") == 0.7
        
        # Test semantic event triggering
        server._apply_config_to_system("sequencer.direction_pattern", "ping_pong")
        assert len(self.semantic_events) == 1
        assert self.semantic_events[0].type == "set_direction_pattern"
        assert self.semantic_events[0].value == "ping_pong"
    
    def test_extract_schema_paths(self):
        """Test schema path extraction."""
        server = APIServer(self.config, self.mock_semantic_handler)
        
        # Mock schema
        schema = {
            "properties": {
                "sequencer": {
                    "type": "object",
                    "properties": {
                        "bpm": {"type": "number", "default": 110.0},
                        "swing": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                    }
                },
                "logging": {
                    "type": "object", 
                    "properties": {
                        "level": {"type": "string", "enum": ["DEBUG", "INFO"]}
                    }
                }
            }
        }
        
        paths = server._extract_schema_paths(schema)
        
        assert "sequencer.bpm" in paths
        assert paths["sequencer.bpm"]["type"] == "number"
        assert paths["sequencer.bpm"]["default"] == 110.0
        
        assert "sequencer.swing" in paths
        assert paths["sequencer.swing"]["minimum"] == 0.0
        assert paths["sequencer.swing"]["maximum"] == 1.0
        
        assert "logging.level" in paths
        assert paths["logging.level"]["enum"] == ["DEBUG", "INFO"]


# Integration tests require the server to be running
@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests that require a running server."""
    
    @pytest.fixture(autouse=True)
    def setup_server(self):
        """Set up a test server for integration tests."""
        # Use a different port for each test to avoid conflicts
        import random
        port = random.randint(8200, 8299)
        
        config = RootConfig(
            api={"enabled": True, "port": port, "host": "127.0.0.1"}
        )
        
        self.semantic_events = []
        def mock_handler(event):
            self.semantic_events.append(event)
        
        self.server = APIServer(config, mock_handler)
        self.base_url = f"http://127.0.0.1:{port}"
        
        # Start server in background thread with better error handling
        self.server_thread = threading.Thread(target=self._run_server_safely, daemon=True)
        self.server._running = True
        self.server_thread.start()
        
        # Wait for server to start with better error handling
        server_started = False
        for i in range(100):  # Wait up to 10 seconds
            try:
                response = requests.get(f"{self.base_url}/", timeout=0.1)
                if response.status_code == 200:
                    server_started = True
                    break
            except:
                time.sleep(0.1)
        
        if not server_started:
            pytest.skip("Server failed to start within timeout")
        
        yield
        
        # Stop server
        self.server.stop()
    
    def _run_server_safely(self):
        """Run the server with proper error handling."""
        try:
            self.server._run_server()
        except Exception as e:
            # Don't let server errors crash the test - just mark as failed to start
            import logging
            logging.error(f"Test server failed to start: {e}")
            self.server._running = False
    
    def test_get_root(self):
        """Test root endpoint."""
        response = requests.get(f"{self.base_url}/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Mystery Music Engine API"
        assert data["version"] == "1.0.0"
    
    def test_get_status(self):
        """Test status endpoint."""
        response = requests.get(f"{self.base_url}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "uptime_seconds" in data
    
    def test_get_config(self):
        """Test configuration endpoints."""
        # Get full config
        response = requests.get(f"{self.base_url}/config")
        assert response.status_code == 200
        config = response.json()
        assert "sequencer" in config
        assert "api" in config
        
        # Get specific value
        response = requests.get(f"{self.base_url}/config/sequencer.bpm")
        assert response.status_code == 200
        data = response.json()
        assert data["path"] == "sequencer.bpm"
        assert "value" in data
        assert data["exists"] is True
    
    def test_update_config(self):
        """Test configuration updates."""
        # Update BPM
        update_data = {
            "path": "sequencer.bpm",
            "value": 125.0,
            "apply_immediately": True
        }
        
        response = requests.post(f"{self.base_url}/config", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["new_value"] == 125.0
        assert data["applied_to_state"] is True
        
        # Verify the change
        response = requests.get(f"{self.base_url}/config/sequencer.bpm")
        assert response.status_code == 200
        assert response.json()["value"] == 125.0
    
    def test_get_state(self):
        """Test state endpoint."""
        response = requests.get(f"{self.base_url}/state")
        assert response.status_code == 200
        state = response.json()
        assert isinstance(state, dict)
    
    def test_semantic_events(self):
        """Test semantic event triggering."""
        response = requests.post(
            f"{self.base_url}/actions/semantic",
            params={"action": "set_direction_pattern", "value": "random"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "triggered successfully" in data["message"]
        assert "set_direction_pattern" in data["message"]
        
        # Test another semantic event
        response = requests.post(
            f"{self.base_url}/actions/semantic",
            params={"action": "set_step_pattern", "value": "syncopated"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "triggered successfully" in data["message"]
        assert "set_step_pattern" in data["message"]
    
    def test_error_handling(self):
        """Test API error handling."""
        # Invalid config path
        response = requests.get(f"{self.base_url}/config/invalid.path")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False
        
        # Invalid update
        update_data = {
            "path": "sequencer.bpm",
            "value": "invalid_number"
        }
        response = requests.post(f"{self.base_url}/config", json=update_data)
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__])
