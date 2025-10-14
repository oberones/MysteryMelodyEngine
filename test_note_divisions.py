#!/usr/bin/env python3
"""Test script to verify note division functionality."""

import sys
sys.path.append('src')

from state import State
from sequencer import Sequencer

def test_note_divisions():
    """Test different note divisions and their timing."""
    print("Testing Note Division Functionality")
    print("=" * 40)
    
    # Test different note divisions
    divisions = ['whole', 'half', 'quarter', 'eighth', 'sixteenth']
    bpm = 60  # Use 60 BPM for easy calculation
    
    for division in divisions:
        print(f"\nTesting {division} note division:")
        
        # Create fresh state and sequencer
        state = State()
        sequencer = Sequencer(state, ['major'])
        
        # Set BPM and note division
        state.set('bpm', bpm)
        state.set('note_division', division)
        
        # Get the calculated values
        steps_per_beat = sequencer._steps_per_beat
        beat_multiplier = sequencer._get_beat_multiplier_from_division(division)
        effective_bpm = bpm / beat_multiplier
        ticks_per_step = sequencer._ticks_per_step
        
        # Calculate expected timing
        beats_per_second = effective_bpm / 60.0
        steps_per_second = beats_per_second * steps_per_beat
        seconds_per_step = 1.0 / steps_per_second if steps_per_second > 0 else float('inf')
        
        print(f"  Steps per beat: {steps_per_beat}")
        print(f"  Beat multiplier: {beat_multiplier}")
        print(f"  Effective BPM: {effective_bpm:.1f}")
        print(f"  Ticks per step: {ticks_per_step}")
        print(f"  Seconds per step: {seconds_per_step:.2f}s")
        
        # Show what this means musically
        if division == 'whole':
            print(f"  → Each step = 1 whole note (4 beats)")
        elif division == 'half':
            print(f"  → Each step = 1 half note (2 beats)")
        elif division == 'quarter':
            print(f"  → Each step = 1 quarter note (1 beat)")
        elif division == 'eighth':
            print(f"  → Each step = 1 eighth note (0.5 beats)")
        elif division == 'sixteenth':
            print(f"  → Each step = 1 sixteenth note (0.25 beats)")

def test_timing_comparison():
    """Compare timing at different BPMs with quarter notes."""
    print("\n\nTiming Comparison (Quarter Notes)")
    print("=" * 40)
    
    test_bpms = [30, 60, 120]
    
    for bpm in test_bpms:
        state = State()
        sequencer = Sequencer(state, ['major'])
        
        state.set('bpm', bpm)
        state.set('note_division', 'quarter')
        
        # Calculate timing
        steps_per_beat = sequencer._steps_per_beat
        beat_multiplier = sequencer._get_beat_multiplier_from_division('quarter')
        effective_bpm = bpm / beat_multiplier
        beats_per_second = effective_bpm / 60.0
        steps_per_second = beats_per_second * steps_per_beat
        seconds_per_step = 1.0 / steps_per_second
        
        print(f"BPM {bpm}: {seconds_per_step:.2f}s per step ({steps_per_second:.1f} steps/sec)")

if __name__ == "__main__":
    test_note_divisions()
    test_timing_comparison()
