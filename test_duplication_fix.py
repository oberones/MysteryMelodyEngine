#!/usr/bin/env python3
"""Test script to verify the duplication fix."""

import sys
sys.path.append('src')

from state import State
from sequencer import Sequencer
from note_utils import format_note_with_number

def test_duplication_fix():
    """Test that the duplication issue is fixed."""
    print("Testing duplication fix...")
    print("=" * 40)
    
    # Create state and sequencer
    state = State()
    sequencer = Sequencer(state, ['major'])
    
    # Set up all_on pattern (which was causing the duplication)
    pattern = sequencer.get_pattern_preset('all_on')
    sequencer.set_step_pattern(pattern)
    
    # Set density and probability to 1.0 for deterministic testing
    state.set('density', 1.0)
    state.set('note_probability', 1.0)
    
    # Collect generated notes
    generated_notes = []
    
    def capture_note(note_event):
        generated_notes.append(note_event)
    
    sequencer.set_note_callback(capture_note)
    
    # Generate notes for all 8 steps
    print("Generating notes for steps 0-7 with 'all_on' pattern:")
    for step in range(8):
        sequencer._generate_step_note(step)
    
    # Display results
    print(f"\nGenerated {len(generated_notes)} notes:")
    for note_event in generated_notes:
        note_info = format_note_with_number(note_event.note)
        print(f"  Step {note_event.step}: {note_info} (velocity={note_event.velocity})")
    
    # Check for duplicates
    notes_by_step = [(n.step, n.note) for n in generated_notes]
    unique_notes = set(n.note for n in generated_notes)
    
    print(f"\nAnalysis:")
    print(f"  Total notes generated: {len(generated_notes)}")
    print(f"  Unique note values: {len(unique_notes)}")
    print(f"  Expected (8 steps, 8 unique notes): 8")
    
    # Check if we have the expected pattern (no duplicates)
    if len(generated_notes) == 8 and len(unique_notes) == 8:
        print("  ✅ PASS: No duplicate notes found!")
    else:
        print("  ❌ FAIL: Duplicates still present")
        # Show which notes are duplicated
        from collections import Counter
        note_counts = Counter(n.note for n in generated_notes)
        duplicates = {note: count for note, count in note_counts.items() if count > 1}
        if duplicates:
            print(f"  Duplicate notes: {duplicates}")

if __name__ == "__main__":
    test_duplication_fix()
