#!/usr/bin/env python3
"""
MIDI Input Debug Script

This script helps diagnose MIDI input issues by:
1. Listing all available MIDI input ports
2. Testing connection to the configured port
3. Listening for all MIDI messages on all channels
4. Providing detailed logging of received messages
5. Testing specific port names and auto-discovery

Usage:
    python debug_midi_input.py [port_name]
    
If no port_name is provided, it will use the port from config.yaml
"""

import sys
import os
import time
import signal
import threading
from typing import Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import mido
import yaml

class MidiInputDebugger:
    def __init__(self):
        self.running = False
        self.port: Optional[mido.ports.BaseInput] = None
        self.message_count = 0
        self.start_time = time.time()
        
    def list_available_ports(self):
        """List all available MIDI input ports."""
        print("🎹 Available MIDI Input Ports:")
        print("-" * 40)
        
        try:
            ports = mido.get_input_names()
            if not ports:
                print("❌ No MIDI input ports found!")
                return []
            
            for i, port in enumerate(ports, 1):
                print(f"  {i}. {port}")
            
            print(f"\n📊 Total: {len(ports)} port(s) available")
            return ports
            
        except Exception as e:
            print(f"❌ Error listing MIDI ports: {e}")
            return []
    
    def load_config_port(self):
        """Load the MIDI input port from config.yaml."""
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            port_name = config.get('midi', {}).get('input_port', 'auto')
            input_channel = config.get('midi', {}).get('input_channel', 1)
            
            print(f"📋 Config Settings:")
            print(f"   Input Port: {port_name}")
            print(f"   Input Channel: {input_channel}")
            print(f"   (Note: This debug script listens on ALL channels)")
            
            return port_name
            
        except Exception as e:
            print(f"⚠️  Could not load config.yaml: {e}")
            return 'auto'
    
    def auto_select_port(self, available_ports):
        """Auto-select a MIDI input port."""
        if not available_ports:
            return None
        
        # Prefer ports that aren't virtual or loopback
        preferred_ports = [p for p in available_ports 
                         if not any(keyword in p.lower() 
                                  for keyword in ['virtual', 'loopback', 'through', 'iac'])]
        
        if preferred_ports:
            selected = preferred_ports[0]
            print(f"🎯 Auto-selected: {selected}")
            return selected
        else:
            selected = available_ports[0]
            print(f"🎯 Auto-selected (fallback): {selected}")
            return selected
    
    def connect_to_port(self, port_name: str):
        """Connect to a specific MIDI input port."""
        print(f"\n🔌 Attempting to connect to: '{port_name}'")
        
        try:
            # Handle auto selection
            if port_name == 'auto':
                available_ports = mido.get_input_names()
                if not available_ports:
                    print("❌ No MIDI input ports available for auto-selection")
                    return False
                port_name = self.auto_select_port(available_ports)
                if not port_name:
                    return False
            
            # Try to open the port
            self.port = mido.open_input(port_name)
            print(f"✅ Successfully connected to: {port_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to '{port_name}': {e}")
            
            # If the specific port failed, try auto-selection
            if port_name != 'auto':
                print("🔄 Trying auto-selection as fallback...")
                available_ports = mido.get_input_names()
                if available_ports:
                    fallback_port = self.auto_select_port(available_ports)
                    if fallback_port and fallback_port != port_name:
                        return self.connect_to_port(fallback_port)
            
            return False
    
    def format_message(self, msg):
        """Format a MIDI message for display."""
        timestamp = time.time() - self.start_time
        
        # Basic message info
        parts = [
            f"[{timestamp:6.2f}s]",
            f"Ch:{msg.channel + 1:2d}" if hasattr(msg, 'channel') else "Ch:--",
            f"{msg.type:>15}"
        ]
        
        # Add message-specific details
        if msg.type in ('note_on', 'note_off'):
            note_name = mido.number_to_note(msg.note) if hasattr(mido, 'number_to_note') else f"#{msg.note}"
            parts.extend([
                f"Note:{note_name:>4}({msg.note:3d})",
                f"Vel:{msg.velocity:3d}"
            ])
        elif msg.type == 'control_change':
            parts.extend([
                f"CC:{msg.control:3d}",
                f"Val:{msg.value:3d}"
            ])
        elif msg.type == 'pitchwheel':
            parts.append(f"Pitch:{msg.pitch:5d}")
        elif msg.type == 'program_change':
            parts.append(f"Prog:{msg.program:3d}")
        elif hasattr(msg, 'value'):
            parts.append(f"Val:{msg.value:3d}")
        
        return " ".join(parts)
    
    def listen_for_messages(self):
        """Listen for MIDI messages and log them."""
        print(f"\n🎧 Listening for MIDI messages...")
        print(f"   Press Ctrl+C to stop")
        print(f"   Monitoring ALL channels (configured channel filtering disabled)")
        print("-" * 80)
        print("Timestamp  Ch   Message Type      Details")
        print("-" * 80)
        
        self.running = True
        self.start_time = time.time()
        
        try:
            while self.running:
                # Check for messages (with timeout to allow for clean shutdown)
                for msg in self.port.iter_pending():
                    self.message_count += 1
                    formatted = self.format_message(msg)
                    print(formatted)
                    
                    # Flush output to ensure real-time display
                    sys.stdout.flush()
                
                # Small sleep to prevent busy waiting
                time.sleep(0.001)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping...")
        except Exception as e:
            print(f"\n❌ Error while listening: {e}")
        finally:
            self.running = False
    
    def show_statistics(self):
        """Show statistics about received messages."""
        duration = time.time() - self.start_time
        print(f"\n📊 Session Statistics:")
        print(f"   Duration: {duration:.1f} seconds")
        print(f"   Messages received: {self.message_count}")
        if duration > 0:
            rate = self.message_count / duration
            print(f"   Average rate: {rate:.1f} messages/second")
    
    def cleanup(self):
        """Clean up resources."""
        if self.port:
            try:
                self.port.close()
                print("🔌 MIDI port closed")
            except Exception as e:
                print(f"⚠️  Error closing port: {e}")
    
    def run(self, port_name: Optional[str] = None):
        """Main debug routine."""
        print("🎹 MIDI Input Debug Tool")
        print("=" * 50)
        
        # List available ports
        available_ports = self.list_available_ports()
        
        # Determine which port to use
        if port_name:
            target_port = port_name
            print(f"\n🎯 Using specified port: {target_port}")
        else:
            target_port = self.load_config_port()
            print(f"\n🎯 Using config port: {target_port}")
        
        # Connect to port
        if not self.connect_to_port(target_port):
            print("\n❌ Could not connect to any MIDI input port")
            print("\n🔧 Troubleshooting suggestions:")
            print("   1. Check that your MIDI device is connected")
            print("   2. Verify the device is recognized by your system")
            print("   3. Try a different port name")
            print("   4. Check if another application is using the port")
            return False
        
        # Set up signal handler for clean shutdown
        def signal_handler(signum, frame):
            print(f"\n📡 Received signal {signum}")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Listen for messages
            self.listen_for_messages()
        finally:
            self.show_statistics()
            self.cleanup()
        
        return True

def main():
    debugger = MidiInputDebugger()
    
    # Check command line arguments
    port_name = None
    if len(sys.argv) > 1:
        port_name = sys.argv[1]
        if port_name in ['-h', '--help']:
            print(__doc__)
            return
    
    try:
        success = debugger.run(port_name)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        debugger.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()
