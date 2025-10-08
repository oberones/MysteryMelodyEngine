#!/usr/bin/env python3
"""
Test script for the Mystery Music Engine Dynamic Configuration API

This script demonstrates how to interact with the API to modify configuration
values at runtime. Run this script while the main engine is running.
"""

import requests
import json
import time
import sys
from typing import Dict, Any


class APIClient:
    """Simple client for interacting with the Mystery Music Engine API."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        response = self.session.get(f"{self.base_url}/status")
        response.raise_for_status()
        return response.json()
    
    def get_config(self, path: str = None) -> Dict[str, Any]:
        """Get configuration. If path is None, returns full config."""
        if path:
            url = f"{self.base_url}/config/{path}"
        else:
            url = f"{self.base_url}/config"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def update_config(self, path: str, value: Any, apply_immediately: bool = True) -> Dict[str, Any]:
        """Update a configuration value."""
        data = {
            "path": path,
            "value": value,
            "apply_immediately": apply_immediately
        }
        
        response = self.session.post(f"{self.base_url}/config", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_state(self) -> Dict[str, Any]:
        """Get current system state."""
        response = self.session.get(f"{self.base_url}/state")
        response.raise_for_status()
        return response.json()
    
    def trigger_semantic_event(self, action: str, value: Any = None) -> Dict[str, Any]:
        """Trigger a semantic event."""
        params = {"action": action}
        if value is not None:
            params["value"] = value
        
        response = self.session.post(f"{self.base_url}/actions/semantic", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_schema(self) -> Dict[str, Any]:
        """Get configuration schema."""
        response = self.session.get(f"{self.base_url}/config/schema")
        response.raise_for_status()
        return response.json()
    
    def get_mappings(self) -> Dict[str, Any]:
        """Get supported configuration mappings."""
        response = self.session.get(f"{self.base_url}/config/mappings")
        response.raise_for_status()
        return response.json()


def demo_basic_usage():
    """Demonstrate basic API usage."""
    print("=== Mystery Music Engine API Demo ===")
    
    client = APIClient()
    
    try:
        # Check if server is running
        status = client.get_status()
        print(f"✓ Server is running (uptime: {status['uptime_seconds']:.1f}s)")
        
        # Get current BPM
        current_bpm = client.get_config("sequencer.bpm")
        print(f"✓ Current BPM: {current_bpm['value']}")
        
        # Update BPM
        new_bpm = current_bpm['value'] + 10
        result = client.update_config("sequencer.bpm", new_bpm)
        print(f"✓ Updated BPM to {new_bpm}: {result['message']}")
        
        # Verify the change
        updated_bpm = client.get_config("sequencer.bpm")
        print(f"✓ Verified BPM is now: {updated_bpm['value']}")
        
        # Update density
        result = client.update_config("sequencer.density", 0.75)
        print(f"✓ Updated density: {result['message']}")
        
        # Change direction pattern
        result = client.trigger_semantic_event("set_direction_pattern", "ping_pong")
        print(f"✓ Changed direction pattern: {result['message']}")
        
        # Get current state
        state = client.get_state()
        print(f"✓ Current sequencer state: BPM={state.get('bpm')}, density={state.get('density')}")
        
        print("\n=== Demo completed successfully! ===")
        
    except requests.exceptions.ConnectionError:
        print("✗ Failed to connect to API server. Is the engine running with API enabled?")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)


def demo_advanced_usage():
    """Demonstrate advanced API features."""
    print("\n=== Advanced API Features Demo ===")
    
    client = APIClient()
    
    try:
        # Get available configuration paths
        mappings = client.get_mappings()
        print(f"✓ Found {len(mappings)} configurable parameters")
        
        # Show some interesting parameters
        interesting_params = [
            "sequencer.swing", "sequencer.gate_length", "mutation.interval_min_s",
            "idle.timeout_ms", "midi.cc_profile.active_profile"
        ]
        
        for param in interesting_params:
            if param in mappings:
                value = client.get_config(param)
                param_info = mappings[param]
                print(f"  {param}: {value['value']} (type: {param_info['type']})")
        
        # Demonstrate updating MIDI settings
        print("\n--- Testing MIDI Configuration ---")
        current_profile = client.get_config("midi.cc_profile.active_profile")
        print(f"Current CC profile: {current_profile['value']}")
        
        # Change swing setting
        print("\n--- Testing Sequencer Parameters ---")
        result = client.update_config("sequencer.swing", 0.15)
        print(f"Updated swing: {result['message']}")
        
        result = client.update_config("sequencer.gate_length", 0.6)
        print(f"Updated gate length: {result['message']}")
        
        # Test mutation settings
        print("\n--- Testing Mutation Settings ---")
        result = client.update_config("mutation.interval_min_s", 45)
        print(f"Updated mutation interval: {result['message']}")
        
        print("\n=== Advanced demo completed! ===")
        
    except Exception as e:
        print(f"✗ Error in advanced demo: {e}")


def interactive_mode():
    """Interactive mode for testing the API."""
    print("\n=== Interactive API Mode ===")
    print("Commands:")
    print("  get <path>           - Get configuration value")
    print("  set <path> <value>   - Set configuration value")
    print("  state                - Show current state")
    print("  status               - Show server status")
    print("  event <action> [val] - Trigger semantic event")
    print("  quit                 - Exit")
    
    client = APIClient()
    
    while True:
        try:
            cmd = input("\napi> ").strip().split()
            if not cmd:
                continue
            
            if cmd[0] == "quit":
                break
            elif cmd[0] == "get":
                if len(cmd) < 2:
                    print("Usage: get <path>")
                    continue
                result = client.get_config(cmd[1])
                print(f"{cmd[1]}: {result['value']}")
            
            elif cmd[0] == "set":
                if len(cmd) < 3:
                    print("Usage: set <path> <value>")
                    continue
                # Try to parse value as number or boolean
                value = cmd[2]
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    if value.lower() in ('true', 'false'):
                        value = value.lower() == 'true'
                    # Keep as string otherwise
                
                result = client.update_config(cmd[1], value)
                print(f"✓ {result['message']}")
            
            elif cmd[0] == "state":
                state = client.get_state()
                for key, value in sorted(state.items()):
                    print(f"  {key}: {value}")
            
            elif cmd[0] == "status":
                status = client.get_status()
                print(f"Status: {status['status']}, uptime: {status['uptime_seconds']:.1f}s")
            
            elif cmd[0] == "event":
                if len(cmd) < 2:
                    print("Usage: event <action> [value]")
                    continue
                value = cmd[2] if len(cmd) > 2 else None
                result = client.trigger_semantic_event(cmd[1], value)
                print(f"✓ {result['message']}")
            
            else:
                print(f"Unknown command: {cmd[0]}")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        demo_basic_usage()
        demo_advanced_usage()
        
        print("\nTry running with --interactive for interactive mode!")


if __name__ == "__main__":
    main()
