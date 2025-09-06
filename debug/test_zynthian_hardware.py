#!/usr/bin/env python3
"""
Quick test script for Zynthian v4 hardware integration.

This script tests basic functionality of the Zynthian hardware interface
without starting the full Mystery Melody Machine.

Usage:
    python debug/test_zynthian_hardware.py

Requirements:
    - Must be run on Raspberry Pi with Zynthian v4 hardware
    - RPi.GPIO library installed
    - Proper GPIO permissions
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("zynthian_test")

def test_hardware_interface():
    """Test basic hardware interface functionality."""
    log.info("Testing Zynthian hardware interface...")
    
    try:
        from zynthian_hardware import ZynthianHardwareInterface, ZynthianEncoder, ZynthianButton
        
        # Create hardware interface
        hw = ZynthianHardwareInterface()
        log.info("✓ Hardware interface created")
        
        # Test event callbacks
        def encoder_callback(event):
            if event.is_button:
                log.info(f"Encoder {event.encoder.name} button pressed")
            else:
                direction = "clockwise" if event.direction > 0 else "counter-clockwise"
                log.info(f"Encoder {event.encoder.name} rotated {direction}")
        
        def button_callback(event):
            action = "pressed" if event.pressed else "released"
            log.info(f"Button {event.button.name} {action}")
        
        hw.set_encoder_callback(encoder_callback)
        hw.set_button_callback(button_callback)
        
        # Start monitoring
        hw.start()
        log.info("✓ Hardware monitoring started")
        log.info("Try rotating encoders and pressing buttons (Ctrl+C to exit)...")
        
        # Monitor for 30 seconds
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            log.info("Test interrupted by user")
        
        # Stop monitoring
        hw.stop()
        log.info("✓ Hardware monitoring stopped")
        
        return True
        
    except ImportError as e:
        log.error(f"✗ Hardware interface not available: {e}")
        log.info("This is normal when not running on Raspberry Pi")
        return False
    except Exception as e:
        log.error(f"✗ Hardware test failed: {e}")
        return False

def test_midi_interface():
    """Test MIDI interface detection."""
    log.info("Testing Zynthian MIDI interface...")
    
    try:
        from zynthian_hardware import ZynthianMidiInterface
        
        midi = ZynthianMidiInterface()
        log.info("✓ MIDI interface created")
        
        # Get available ports
        available = midi.get_available_ports()
        log.info(f"Available MIDI ports: {len(available)}")
        for port_id, description in available.items():
            log.info(f"  {port_id}: {description}")
        
        # Get recommendations
        recommended = midi.get_recommended_ports()
        log.info(f"Recommended input: {recommended.get('input', 'none')}")
        log.info(f"Recommended output: {recommended.get('output', 'none')}")
        
        return True
        
    except ImportError as e:
        log.error(f"✗ MIDI interface not available: {e}")
        return False
    except Exception as e:
        log.error(f"✗ MIDI test failed: {e}")
        return False

def test_integration_manager():
    """Test integration manager creation."""
    log.info("Testing Zynthian integration manager...")
    
    try:
        from zynthian_integration import create_zynthian_integration
        
        # Test configuration
        config = {
            "zynthian": {
                "enabled": True,
                "encoder_sensitivity": 1,
                "bpm_step": 5,
                "min_bpm": 60,
                "max_bpm": 200
            }
        }
        
        integration = create_zynthian_integration(config)
        
        if integration:
            log.info("✓ Integration manager created")
            
            # Test MIDI recommendations
            midi_config = integration.get_recommended_midi_config()
            log.info(f"MIDI recommendations: {midi_config}")
            
            return True
        else:
            log.warning("Integration manager creation returned None (disabled?)")
            return False
            
    except ImportError as e:
        log.error(f"✗ Integration manager not available: {e}")
        return False
    except Exception as e:
        log.error(f"✗ Integration test failed: {e}")
        return False

def main():
    """Run all Zynthian hardware tests."""
    log.info("=== Zynthian v4 Hardware Test ===")
    
    tests = [
        ("Hardware Interface", test_hardware_interface),
        ("MIDI Interface", test_midi_interface),
        ("Integration Manager", test_integration_manager)
    ]
    
    results = []
    for test_name, test_func in tests:
        log.info(f"\n--- {test_name} Test ---")
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    log.info("\n=== Test Summary ===")
    passed = 0
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        log.info(f"{test_name}: {status}")
        if success:
            passed += 1
    
    log.info(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        log.info("🎉 All tests passed! Zynthian integration is ready.")
        return 0
    else:
        log.warning("⚠ Some tests failed. Check hardware setup.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
