#!/usr/bin/env python3
"""Debug script to trace BPM initialization issue."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import load_config
from state import get_state, reset_state
from sequencer import create_sequencer

def main():
    # Reset state to ensure clean start
    reset_state()
    
    # Load config
    cfg = load_config('config.yaml')
    print(f"Config BPM: {cfg.sequencer.bpm}")
    
    # Get state and check initial BPM
    state = get_state()
    print(f"State BPM before config: {state.get('bpm')}")
    
    # Update state from config
    state.update_multiple({
        'bpm': cfg.sequencer.bpm,
        'swing': cfg.sequencer.swing,
        'density': cfg.sequencer.density,
        'sequence_length': cfg.sequencer.steps,
        'root_note': cfg.sequencer.root_note,
        'gate_length': cfg.sequencer.gate_length,
    }, source='config')
    
    print(f"State BPM after config: {state.get('bpm')}")
    
    # Create sequencer
    sequencer = create_sequencer(state, cfg.scales)
    
    # Check clock BPM
    print(f"Clock BPM after sequencer creation: {sequencer.clock.bpm}")
    
    # Manually call update_clock_from_state to see what happens
    print("Calling _update_clock_from_state()...")
    sequencer._update_clock_from_state()
    print(f"Clock BPM after manual update: {sequencer.clock.bpm}")

if __name__ == "__main__":
    main()
