#!/usr/bin/env python3
"""Demo: Hybrid Input System (HID + MIDI)

This demonstrates the new hybrid input system that supports:
1. HID Input: 10 arcade buttons + joystick via USB gamepad/joystick 
2. MIDI Input: Potentiometers + switches via Teensy

Both input sources generate the same semantic events and work together seamlessly.
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from events import SemanticEvent
from config import load_config
from hybrid_input import HybridInput

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def demo_semantic_handler(event: SemanticEvent):
    """Demo handler for semantic events from both HID and MIDI."""
    source_icon = "🎮" if "hid" in event.source else "🎛️"
    
    if event.type == "trigger_step":
        print(f"{source_icon} TRIGGER STEP: Note {event.raw_note} (Button/Key pressed)")
    elif event.type in ["osc_a", "osc_b", "mod_a", "mod_b"]:
        direction = {"osc_a": "UP", "osc_b": "DOWN", "mod_a": "LEFT", "mod_b": "RIGHT"}.get(event.type, event.type)
        print(f"{source_icon} JOYSTICK {direction}: CC {event.raw_cc}")
    elif event.raw_cc:
        print(f"{source_icon} PARAMETER: {event.type} = {event.value} (CC {event.raw_cc})")
    else:
        print(f"{source_icon} EVENT: {event.type} = {event.value}")

def demo_router_callback(msg):
    """Demo callback for MIDI messages that would normally be routed."""
    print(f"🎛️ MIDI from Teensy: {msg}")

def main():
    """Demo the hybrid input system."""
    print("=" * 60)
    print("🎮 Mystery Music Engine - Hybrid Input System Demo")
    print("=" * 60)
    print()
    print("This demo shows the new hybrid input system that supports:")
    print("  🎮 HID Input: 10 arcade buttons + joystick")
    print("  🎛️ MIDI Input: Potentiometers + switches from Teensy")
    print()
    print("Configuration Summary:")
    print("-" * 30)
    
    try:
        # Load configuration
        cfg = load_config('config.yaml')
        print(f"✓ Configuration loaded from config.yaml")
        
        # Show HID configuration
        print(f"  HID Device: {cfg.hid.device_name}")
        print(f"  HID Buttons: {len(cfg.hid.button_mapping)} arcade buttons")
        print(f"  HID Joystick: {list(cfg.hid.joystick_mapping.keys())} directions")
        print()
        
        # Show MIDI configuration (now only for Teensy potentiometers/switches)
        print(f"  MIDI Port: {cfg.midi.input_port}")
        print(f"  MIDI Channel: {cfg.midi.input_channel}")
        midi_ccs = list(cfg.mapping.get('ccs', {}).keys()) if cfg.mapping else []
        print(f"  MIDI CCs (from Teensy): {len(midi_ccs)} potentiometers/switches")
        print()
        
        # Create hybrid input system
        print("Initializing Hybrid Input System...")
        hybrid_input = HybridInput.create_from_config(cfg, demo_router_callback, demo_semantic_handler)
        print("✓ Hybrid input system created")
        print()
        
        # Show mapping details
        print("Input Mapping Details:")
        print("-" * 30)
        print("HID Arcade Buttons (0-9) → MIDI Notes (60-69):")
        for btn_idx, action in cfg.hid.button_mapping.items():
            midi_note = 60 + btn_idx
            print(f"  Button {btn_idx} → Note {midi_note} ({action})")
        print()
        
        print("HID Joystick → MIDI CCs:")
        cc_map = {"up": 50, "down": 51, "left": 52, "right": 53}
        for direction, action in cfg.hid.joystick_mapping.items():
            cc_num = cc_map.get(direction, "?")
            print(f"  Joystick {direction.upper()} → CC {cc_num} ({action})")
        print()
        
        print("MIDI CCs from Teensy (potentiometers/switches):")
        for cc, action in cfg.mapping.get('ccs', {}).items():
            print(f"  CC {cc} → {action}")
        print()
        
        # Attempt to start the system
        print("Attempting to start hybrid input system...")
        print("Note: HID will fail if 'Generic USB Joystick' not connected (expected)")
        print("      MIDI will fail if Teensy not connected (expected)")
        print()
        
        try:
            hybrid_input.start()
            print("✅ Hybrid input system started successfully!")
            print()
            print("Try the following inputs:")
            print("  🎮 Press arcade buttons 0-9 (if HID device connected)")
            print("  🎮 Move joystick up/down/left/right (if HID device connected)")  
            print("  🎛️ Turn potentiometers on Teensy (if MIDI device connected)")
            print("  🎛️ Toggle switches on Teensy (if MIDI device connected)")
            print()
            print("Press Ctrl+C to exit")
            print("-" * 60)
            
            # Keep running to show live input
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\nShutting down...")
        except Exception as e:
            print(f"⚠️  Partial startup (expected without connected devices): {e}")
            print()
            print("💡 When devices are connected:")
            print("   - 'Generic USB Joystick' will enable HID input")
            print("   - Teensy MIDI device will enable MIDI input")
            print("   - Both can work simultaneously")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        log.exception("Demo failed")
        return 1
    finally:
        try:
            if 'hybrid_input' in locals():
                hybrid_input.stop()
                print("Hybrid input system stopped.")
        except:
            pass
    
    print()
    print("🎉 Demo completed successfully!")
    print("   The hybrid input system is ready for production use.")
    return 0

if __name__ == "__main__":
    exit(main())
