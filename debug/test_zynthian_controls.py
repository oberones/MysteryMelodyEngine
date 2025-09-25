#!/usr/bin/env python3
"""
Test script for the new Zynthian control mappings.

This script simulates the new Zynthian hardware controls to verify
the integration works correctly before deploying to actual hardware.
"""

import sys
import os
import logging

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zynthian_integration import ZynthianIntegrationManager, ZynthianConfig
from state import State
from scale_mapper import ScaleMapper, SCALES

# Mock classes for testing without hardware
class MockSequencer:
    def __init__(self):
        self.available_scales = list(SCALES.keys())
    
    def set_direction_pattern(self, pattern: str):
        print(f"MockSequencer: Setting direction pattern to {pattern}")

class MockExternalHardware:
    def __init__(self):
        self.active_profile = "korg_nts1_mk2"
    
    def set_active_profile(self, profile: str):
        self.active_profile = profile
        print(f"MockExternalHardware: Setting CC profile to {profile}")
    
    def get_active_profile_id(self):
        return self.active_profile

def test_zynthian_controls():
    """Test the new Zynthian control mappings"""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    
    # Create components
    state = State()
    config = ZynthianConfig(enabled=True)
    integration = ZynthianIntegrationManager(config)
    
    # Create mock components
    sequencer = MockSequencer()
    external_hardware = MockExternalHardware()
    
    # Inject components
    integration.set_components(
        state=state,
        sequencer=sequencer,
        external_hardware=external_hardware
    )
    
    # Initialize current selections
    integration._initialize_current_selections()
    
    print("=== Testing Zynthian Control Mappings ===\n")
    
    # Test Encoder 0: Steps selection
    print("1. Testing Encoder 0 (Steps 1-32):")
    print(f"   Initial steps: {integration.current_steps_selection}")
    integration._adjust_steps_selection(3)  # Increase by 3
    print(f"   After +3: {integration.current_steps_selection}")
    integration._adjust_steps_selection(-1)  # Decrease by 1
    print(f"   After -1: {integration.current_steps_selection}")
    integration._apply_steps_selection()  # Apply the value
    print(f"   Applied steps to state: {state.get('steps')}")
    print()
    
    # Test Encoder 1: Scale selection
    print("2. Testing Encoder 1 (Scale Selection):")
    print(f"   Available scales: {integration.available_scales}")
    print(f"   Initial scale index: {integration.current_scale_selection}")
    integration._adjust_scale_selection(2)  # Move forward 2 scales
    print(f"   After +2: {integration.current_scale_selection} ({integration.available_scales[integration.current_scale_selection]})")
    integration._apply_scale_selection()  # Apply the scale
    print(f"   Applied scale to state: {state.get('scale')}")
    print()
    
    # Test Encoder 2: Root note selection
    print("3. Testing Encoder 2 (Root Note C-B):")
    print(f"   Initial root: {integration.root_notes[integration.current_root_selection]}")
    integration._adjust_root_selection(5)  # Move up 5 semitones
    print(f"   After +5: {integration.root_notes[integration.current_root_selection]}")
    integration._apply_root_selection()  # Apply the root note
    print(f"   Applied root note to state: {state.get('root_note')}")
    print()
    
    # Test Encoder 3: Direction pattern selection
    print("4. Testing Encoder 3 (Direction Pattern):")
    print(f"   Available patterns: {integration.direction_patterns}")
    print(f"   Initial pattern: {integration.direction_patterns[integration.current_direction_selection]}")
    integration._adjust_direction_selection(2)  # Move forward 2 patterns
    print(f"   After +2: {integration.direction_patterns[integration.current_direction_selection]}")
    integration._apply_direction_selection()  # Apply the pattern
    print()
    
    # Test Button S1-S4: CC Profile selection
    print("5. Testing Buttons S1-S4 (CC Profile Selection):")
    print(f"   Available profiles: {integration.cc_profiles}")
    print(f"   Initial profile: {external_hardware.get_active_profile_id()}")
    
    print("   Pressing S1 (NTS-1):")
    integration._select_cc_profile("korg_nts1_mk2")
    
    print("   Pressing S2 (JX-08):")
    integration._select_cc_profile("roland_jx08")
    
    print("   Pressing S3 (Streichfett):")
    integration._select_cc_profile("waldorf_streichfett")
    
    print("   Pressing S4 (Generic):")
    integration._select_cc_profile("generic_analog")
    print()
    
    # Test boundary conditions
    print("6. Testing Boundary Conditions:")
    
    # Test steps boundaries
    integration.current_steps_selection = 1
    integration._adjust_steps_selection(-5)  # Should clamp to 1
    print(f"   Steps below minimum: {integration.current_steps_selection}")
    
    integration.current_steps_selection = 32
    integration._adjust_steps_selection(5)  # Should clamp to 32
    print(f"   Steps above maximum: {integration.current_steps_selection}")
    
    # Test scale wraparound
    integration.current_scale_selection = len(integration.available_scales) - 1
    integration._adjust_scale_selection(1)  # Should wrap to 0
    print(f"   Scale wraparound: {integration.current_scale_selection} ({integration.available_scales[integration.current_scale_selection]})")
    
    # Test root note wraparound
    integration.current_root_selection = len(integration.root_notes) - 1
    integration._adjust_root_selection(1)  # Should wrap to 0
    print(f"   Root note wraparound: {integration.root_notes[integration.current_root_selection]}")
    print()
    
    # Show final state
    print("7. Final State Summary:")
    integration._log_current_state()

if __name__ == "__main__":
    test_zynthian_controls()
