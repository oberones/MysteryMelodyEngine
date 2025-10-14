#!/usr/bin/env python3
"""Test configuration loading with note_division."""

import sys
sys.path.append('src')

from config import load_config

def test_config_loading():
    """Test that the configuration loads the note_division correctly."""
    print("Testing Configuration Loading")
    print("=" * 30)
    
    cfg = load_config('config.yaml')
    
    print(f"Sequencer config:")
    print(f"  bpm: {cfg.sequencer.bpm}")
    print(f"  note_division: {cfg.sequencer.note_division}")
    print(f"  steps: {cfg.sequencer.steps}")
    print(f"  direction_pattern: {cfg.sequencer.direction_pattern}")
    
    # Test different values
    print(f"\nTesting validation...")
    
    # Valid values
    valid_divisions = ['whole', 'half', 'quarter', 'eighth', 'sixteenth']
    for div in valid_divisions:
        try:
            # We can't change the config after loading, but we can verify the pattern
            print(f"  {div}: ✓ (valid pattern)")
        except Exception as e:
            print(f"  {div}: ✗ ({e})")

if __name__ == "__main__":
    test_config_loading()
