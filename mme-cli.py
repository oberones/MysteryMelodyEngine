#!/usr/bin/env python3
"""
Mystery Music Engine CLI Client

A command-line interface for interacting with the Mystery Music Engine's
Dynamic Configuration API. Provides easy access to configuration management,
system monitoring, and event triggering.

Usage:
    mme-cli config get sequencer.bpm
    mme-cli config set sequencer.bpm 120
    mme-cli state show
    mme-cli event trigger set_direction_pattern ping_pong
    mme-cli status
"""

import argparse
import json
import sys
import time
from typing import Any, Dict, Optional
import requests
from urllib.parse import urlparse


class MMEClient:
    """Client for Mystery Music Engine API."""
    
    def __init__(self, base_url: str = "http://localhost:8080", timeout: float = 5.0):
        """Initialize the client."""
        # Ensure URL has proper format
        if not base_url.startswith(('http://', 'https://')):
            base_url = f"http://{base_url}"
        
        parsed = urlparse(base_url)
        if not parsed.port:
            base_url = f"{base_url}:8080"
        
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.timeout = timeout
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make a request with error handling."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError:
            print(f"Error: Could not connect to Mystery Music Engine at {self.base_url}")
            print("Make sure the engine is running with API enabled.")
            sys.exit(1)
        except requests.exceptions.Timeout:
            print(f"Error: Request timed out after {self.timeout}s")
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"Error: API endpoint not found: {endpoint}")
            else:
                try:
                    error_detail = e.response.json().get('detail', str(e))
                    print(f"Error: {error_detail}")
                except Exception:
                    print(f"Error: HTTP {e.response.status_code}")
            sys.exit(1)
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        response = self._request('GET', '/status')
        return response.json()
    
    def get_config(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration."""
        if path:
            response = self._request('GET', f'/config/{path}')
        else:
            response = self._request('GET', '/config')
        return response.json()
    
    def set_config(self, path: str, value: Any, apply_immediately: bool = True) -> Dict[str, Any]:
        """Set configuration value."""
        data = {
            "path": path,
            "value": value,
            "apply_immediately": apply_immediately
        }
        response = self._request('POST', '/config', json=data)
        return response.json()
    
    def get_state(self) -> Dict[str, Any]:
        """Get system state."""
        response = self._request('GET', '/state')
        return response.json()
    
    def reset_state(self) -> Dict[str, Any]:
        """Reset system state."""
        response = self._request('POST', '/state/reset')
        return response.json()
    
    def trigger_event(self, action: str, value: Optional[Any] = None) -> Dict[str, Any]:
        """Trigger semantic event."""
        params = {"action": action}
        if value is not None:
            params["value"] = value
        response = self._request('POST', '/actions/semantic', params=params)
        return response.json()
    
    def get_schema(self) -> Dict[str, Any]:
        """Get configuration schema."""
        response = self._request('GET', '/config/schema')
        return response.json()
    
    def get_mappings(self) -> Dict[str, Any]:
        """Get configuration mappings."""
        response = self._request('GET', '/config/mappings')
        return response.json()


def format_value(value: Any) -> str:
    """Format a value for display."""
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2)
    return str(value)


def parse_value(value_str: str) -> Any:
    """Parse a string value to the appropriate type."""
    # Try to parse as JSON first (handles numbers, booleans, strings, lists, dicts)
    try:
        return json.loads(value_str)
    except json.JSONDecodeError:
        # If not valid JSON, treat as string
        return value_str


def cmd_status(client: MMEClient, args: argparse.Namespace) -> None:
    """Show system status."""
    status = client.get_status()
    
    print("Mystery Music Engine Status")
    print("=" * 30)
    print(f"Status: {status['status']}")
    print(f"Uptime: {status['uptime_seconds']:.1f} seconds")
    print(f"Config Version: {status.get('config_version', 'Unknown')}")
    print(f"API Version: {status.get('api_version', 'Unknown')}")


def cmd_config_get(client: MMEClient, args: argparse.Namespace) -> None:
    """Get configuration value(s)."""
    config = client.get_config(args.path)
    
    if args.path:
        if config.get('exists', True):
            print(f"{args.path}: {format_value(config['value'])}")
        else:
            print(f"Configuration path '{args.path}' not found")
            sys.exit(1)
    else:
        print("Complete Configuration:")
        print("=" * 25)
        print(json.dumps(config, indent=2))


def cmd_config_set(client: MMEClient, args: argparse.Namespace) -> None:
    """Set configuration value."""
    value = parse_value(args.value)
    
    result = client.set_config(args.path, value, not args.no_apply)
    
    if result['success']:
        print(f"✓ {result['message']}")
        if result.get('old_value') is not None:
            print(f"  Old value: {format_value(result['old_value'])}")
        print(f"  New value: {format_value(result['new_value'])}")
    else:
        print(f"✗ Failed to update configuration")
        sys.exit(1)


def cmd_config_list(client: MMEClient, args: argparse.Namespace) -> None:
    """List available configuration paths."""
    mappings = client.get_mappings()
    
    print("Available Configuration Paths:")
    print("=" * 35)
    
    # Group by category
    categories = {}
    for path, info in mappings.items():
        category = path.split('.')[0]
        if category not in categories:
            categories[category] = []
        categories[category].append((path, info))
    
    for category, paths in sorted(categories.items()):
        print(f"\n{category.upper()}:")
        for path, info in sorted(paths):
            type_info = info.get('type', 'unknown')
            desc = info.get('description', '')
            if desc:
                print(f"  {path:30} ({type_info}) - {desc}")
            else:
                print(f"  {path:30} ({type_info})")


def cmd_state_show(client: MMEClient, args: argparse.Namespace) -> None:
    """Show system state."""
    state = client.get_state()
    
    print("System State:")
    print("=" * 15)
    
    if args.key:
        if args.key in state:
            print(f"{args.key}: {format_value(state[args.key])}")
        else:
            print(f"State key '{args.key}' not found")
            available_keys = list(state.keys())
            if available_keys:
                print(f"Available keys: {', '.join(sorted(available_keys))}")
            sys.exit(1)
    else:
        for key, value in sorted(state.items()):
            print(f"{key:25}: {format_value(value)}")


def cmd_state_reset(client: MMEClient, args: argparse.Namespace) -> None:
    """Reset system state."""
    if not args.confirm:
        response = input("Are you sure you want to reset the system state? (y/N): ")
        if response.lower() not in ('y', 'yes'):
            print("Reset cancelled")
            return
    
    result = client.reset_state()
    print(f"✓ {result['message']}")


def cmd_event_trigger(client: MMEClient, args: argparse.Namespace) -> None:
    """Trigger semantic event."""
    value = parse_value(args.value) if args.value else None
    
    result = client.trigger_event(args.action, value)
    print(f"✓ {result['message']}")


def cmd_monitor(client: MMEClient, args: argparse.Namespace) -> None:
    """Monitor system in real-time."""
    print("Monitoring Mystery Music Engine (Ctrl+C to stop)")
    print("=" * 45)
    
    try:
        while True:
            try:
                status = client.get_status()
                state = client.get_state()
                
                # Clear screen (works on most terminals)
                print("\033[H\033[J", end="")
                
                print(f"Status: {status['status']} | Uptime: {status['uptime_seconds']:.1f}s")
                print("-" * 50)
                
                # Show key parameters
                key_params = ['bpm', 'density', 'swing', 'sequence_length', 'root_note']
                for param in key_params:
                    if param in state:
                        print(f"{param:15}: {state[param]}")
                
                print(f"\nLast update: {time.strftime('%H:%M:%S')}")
                time.sleep(args.interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error during monitoring: {e}")
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nMonitoring stopped")


def cmd_quick_set(client: MMEClient, args: argparse.Namespace) -> None:
    """Quick set commands for common parameters."""
    quick_commands = {
        'bpm': ('sequencer.bpm', float),
        'density': ('sequencer.density', float),
        'swing': ('sequencer.swing', float),
        'steps': ('sequencer.steps', int),
        'gate': ('sequencer.gate_length', float),
        'root': ('sequencer.root_note', int),
    }
    
    if args.param not in quick_commands:
        print(f"Unknown quick parameter: {args.param}")
        print(f"Available: {', '.join(quick_commands.keys())}")
        sys.exit(1)
    
    path, type_func = quick_commands[args.param]
    try:
        value = type_func(args.value)
    except ValueError:
        print(f"Invalid value '{args.value}' for {args.param} (expected {type_func.__name__})")
        sys.exit(1)
    
    result = client.set_config(path, value)
    if result['success']:
        print(f"✓ Set {args.param} to {value}")
    else:
        print(f"✗ Failed to set {args.param}")
        sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Mystery Music Engine CLI Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                              # Show system status
  %(prog)s config get sequencer.bpm            # Get BPM value
  %(prog)s config set sequencer.bpm 120       # Set BPM to 120
  %(prog)s config list                         # List all config paths
  %(prog)s state show                          # Show current state
  %(prog)s event trigger set_direction_pattern ping_pong
  %(prog)s monitor                             # Real-time monitoring
  %(prog)s quick bpm 140                       # Quick BPM change
        """
    )
    
    parser.add_argument(
        '--url', '-u',
        default='http://localhost:8080',
        help='API server URL (default: http://localhost:8080)'
    )
    
    parser.add_argument(
        '--timeout', '-t',
        type=float,
        default=5.0,
        help='Request timeout in seconds (default: 5.0)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    subparsers.add_parser('status', help='Show system status')
    
    # Config commands
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_subparsers = config_parser.add_subparsers(dest='config_action')
    
    # Config get
    config_get = config_subparsers.add_parser('get', help='Get configuration value')
    config_get.add_argument('path', nargs='?', help='Configuration path (omit for full config)')
    
    # Config set
    config_set = config_subparsers.add_parser('set', help='Set configuration value')
    config_set.add_argument('path', help='Configuration path')
    config_set.add_argument('value', help='New value (JSON format)')
    config_set.add_argument('--no-apply', action='store_true', help='Don\'t apply to running system')
    
    # Config list
    config_subparsers.add_parser('list', help='List available configuration paths')
    
    # State commands
    state_parser = subparsers.add_parser('state', help='System state management')
    state_subparsers = state_parser.add_subparsers(dest='state_action')
    
    # State show
    state_show = state_subparsers.add_parser('show', help='Show system state')
    state_show.add_argument('key', nargs='?', help='Specific state key to show')
    
    # State reset
    state_reset = state_subparsers.add_parser('reset', help='Reset system state')
    state_reset.add_argument('--confirm', '-y', action='store_true', help='Skip confirmation')
    
    # Event commands
    event_parser = subparsers.add_parser('event', help='Event management')
    event_subparsers = event_parser.add_subparsers(dest='event_action')
    
    # Event trigger
    event_trigger = event_subparsers.add_parser('trigger', help='Trigger semantic event')
    event_trigger.add_argument('action', help='Event action name')
    event_trigger.add_argument('value', nargs='?', help='Event value (optional)')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Real-time system monitoring')
    monitor_parser.add_argument('--interval', '-i', type=float, default=1.0, help='Update interval in seconds')
    
    # Quick commands
    quick_parser = subparsers.add_parser('quick', help='Quick parameter changes')
    quick_parser.add_argument('param', choices=['bpm', 'density', 'swing', 'steps', 'gate', 'root'], help='Parameter to change')
    quick_parser.add_argument('value', help='New value')
    
    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Create client
    client = MMEClient(args.url, args.timeout)
    
    # Route to appropriate command handler
    try:
        if args.command == 'status':
            cmd_status(client, args)
        
        elif args.command == 'config':
            if args.config_action == 'get':
                cmd_config_get(client, args)
            elif args.config_action == 'set':
                cmd_config_set(client, args)
            elif args.config_action == 'list':
                cmd_config_list(client, args)
            else:
                parser.parse_args(['config', '--help'])
        
        elif args.command == 'state':
            if args.state_action == 'show':
                cmd_state_show(client, args)
            elif args.state_action == 'reset':
                cmd_state_reset(client, args)
            else:
                parser.parse_args(['state', '--help'])
        
        elif args.command == 'event':
            if args.event_action == 'trigger':
                cmd_event_trigger(client, args)
            else:
                parser.parse_args(['event', '--help'])
        
        elif args.command == 'monitor':
            cmd_monitor(client, args)
        
        elif args.command == 'quick':
            cmd_quick_set(client, args)
        
        else:
            parser.print_help()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(1)


if __name__ == '__main__':
    main()
