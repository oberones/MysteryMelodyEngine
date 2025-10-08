"""
Tests for the Mystery Music Engine CLI Client

Tests the CLI functionality and command parsing.
"""

import pytest
import subprocess
import sys
from unittest.mock import Mock, patch
import json

# Import the CLI module
sys.path.insert(0, '.')
import importlib.util
spec = importlib.util.spec_from_file_location("mme_cli", "mme-cli.py")
mme_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mme_cli)

MMEClient = mme_cli.MMEClient
parse_value = mme_cli.parse_value
format_value = mme_cli.format_value
create_parser = mme_cli.create_parser


class TestMMEClient:
    """Test the MME client class."""
    
    def test_client_initialization(self):
        """Test client initialization with different URL formats."""
        # Default URL
        client = MMEClient()
        assert client.base_url == "http://localhost:8080"
        
        # URL without protocol
        client = MMEClient("localhost:9090")
        assert client.base_url == "http://localhost:9090"
        
        # Full URL
        client = MMEClient("http://192.168.1.100:8080")
        assert client.base_url == "http://192.168.1.100:8080"
        
        # URL without port
        client = MMEClient("http://localhost")
        assert client.base_url == "http://localhost:8080"
    
    def test_timeout_setting(self):
        """Test timeout configuration."""
        client = MMEClient(timeout=10.0)
        assert client.timeout == 10.0
        assert client.session.timeout == 10.0


class TestValueParsing:
    """Test value parsing and formatting functions."""
    
    def test_parse_value(self):
        """Test parsing string values to appropriate types."""
        # Numbers
        assert parse_value("123") == 123
        assert parse_value("123.45") == 123.45
        assert parse_value("-10") == -10
        
        # Booleans
        assert parse_value("true") is True
        assert parse_value("false") is False
        
        # Strings
        assert parse_value('"hello"') == "hello"
        assert parse_value("hello") == "hello"  # Non-JSON string
        
        # Lists
        assert parse_value('[1, 2, 3]') == [1, 2, 3]
        
        # Objects
        assert parse_value('{"key": "value"}') == {"key": "value"}
    
    def test_format_value(self):
        """Test formatting values for display."""
        # Simple values
        assert format_value(123) == "123"
        assert format_value("hello") == "hello"
        assert format_value(True) == "True"
        
        # Complex values (should be JSON formatted)
        result = format_value({"key": "value"})
        assert '"key"' in result
        assert '"value"' in result
        
        result = format_value([1, 2, 3])
        assert "[\n" in result  # JSON indented format


class TestArgumentParsing:
    """Test CLI argument parsing."""
    
    def test_parser_creation(self):
        """Test that parser is created correctly."""
        parser = create_parser()
        assert parser is not None
        
        # Test that required subcommands are present
        args = parser.parse_args(['status'])
        assert args.command == 'status'
        
        args = parser.parse_args(['config', 'get', 'sequencer.bpm'])
        assert args.command == 'config'
        assert args.config_action == 'get'
        assert args.path == 'sequencer.bpm'
    
    def test_url_argument(self):
        """Test URL argument parsing."""
        parser = create_parser()
        
        # Default URL
        args = parser.parse_args(['status'])
        assert args.url == 'http://localhost:8080'
        
        # Custom URL
        args = parser.parse_args(['--url', 'http://192.168.1.100:8080', 'status'])
        assert args.url == 'http://192.168.1.100:8080'
        
        # Short form
        args = parser.parse_args(['-u', 'localhost:9090', 'status'])
        assert args.url == 'localhost:9090'
    
    def test_timeout_argument(self):
        """Test timeout argument parsing."""
        parser = create_parser()
        
        # Default timeout
        args = parser.parse_args(['status'])
        assert args.timeout == 5.0
        
        # Custom timeout
        args = parser.parse_args(['--timeout', '10.0', 'status'])
        assert args.timeout == 10.0
        
        # Short form
        args = parser.parse_args(['-t', '2.5', 'status'])
        assert args.timeout == 2.5
    
    def test_config_commands(self):
        """Test config command parsing."""
        parser = create_parser()
        
        # Config get
        args = parser.parse_args(['config', 'get', 'sequencer.bpm'])
        assert args.command == 'config'
        assert args.config_action == 'get'
        assert args.path == 'sequencer.bpm'
        
        # Config get all
        args = parser.parse_args(['config', 'get'])
        assert args.path is None
        
        # Config set
        args = parser.parse_args(['config', 'set', 'sequencer.bpm', '120'])
        assert args.config_action == 'set'
        assert args.path == 'sequencer.bpm'
        assert args.value == '120'
        assert args.no_apply is False
        
        # Config set with no-apply
        args = parser.parse_args(['config', 'set', 'sequencer.bpm', '120', '--no-apply'])
        assert args.no_apply is True
        
        # Config list
        args = parser.parse_args(['config', 'list'])
        assert args.config_action == 'list'
    
    def test_state_commands(self):
        """Test state command parsing."""
        parser = create_parser()
        
        # State show
        args = parser.parse_args(['state', 'show'])
        assert args.command == 'state'
        assert args.state_action == 'show'
        assert args.key is None
        
        # State show specific key
        args = parser.parse_args(['state', 'show', 'bpm'])
        assert args.key == 'bpm'
        
        # State reset
        args = parser.parse_args(['state', 'reset'])
        assert args.state_action == 'reset'
        assert args.confirm is False
        
        # State reset with confirm
        args = parser.parse_args(['state', 'reset', '--confirm'])
        assert args.confirm is True
    
    def test_event_commands(self):
        """Test event command parsing."""
        parser = create_parser()
        
        # Event trigger without value
        args = parser.parse_args(['event', 'trigger', 'reload_cc_profile'])
        assert args.command == 'event'
        assert args.event_action == 'trigger'
        assert args.action == 'reload_cc_profile'
        assert args.value is None
        
        # Event trigger with value
        args = parser.parse_args(['event', 'trigger', 'set_direction_pattern', 'ping_pong'])
        assert args.action == 'set_direction_pattern'
        assert args.value == 'ping_pong'
    
    def test_quick_commands(self):
        """Test quick command parsing."""
        parser = create_parser()
        
        args = parser.parse_args(['quick', 'bpm', '120'])
        assert args.command == 'quick'
        assert args.param == 'bpm'
        assert args.value == '120'
    
    def test_monitor_commands(self):
        """Test monitor command parsing."""
        parser = create_parser()
        
        # Default interval
        args = parser.parse_args(['monitor'])
        assert args.command == 'monitor'
        assert args.interval == 1.0
        
        # Custom interval
        args = parser.parse_args(['monitor', '--interval', '0.5'])
        assert args.interval == 0.5


# Integration tests that require subprocess execution
@pytest.mark.integration
class TestCLIExecution:
    """Test CLI execution via subprocess."""
    
    def test_help_output(self):
        """Test that CLI shows help correctly."""
        result = subprocess.run(
            ['./mme-cli', '--help'],
            capture_output=True,
            text=True,
            cwd='.'
        )
        
        assert result.returncode == 0
        assert 'Mystery Music Engine CLI Client' in result.stdout
        assert 'status' in result.stdout
        assert 'config' in result.stdout
    
    def test_connection_error(self):
        """Test CLI behavior when server is not running."""
        result = subprocess.run(
            ['./mme-cli', 'status'],
            capture_output=True,
            text=True,
            cwd='.'
        )
        
        assert result.returncode == 1
        assert 'Could not connect to Mystery Music Engine' in result.stdout
    
    def test_invalid_command(self):
        """Test CLI behavior with invalid commands."""
        result = subprocess.run(
            ['./mme-cli', 'invalid_command'],
            capture_output=True,
            text=True,
            cwd='.'
        )
        
        assert result.returncode != 0


if __name__ == "__main__":
    pytest.main([__file__])
