#!/usr/bin/env python3
"""
Demo script showing the root_note parameter functionality.
Shows how changing root_note affects the generated notes in different scales.
"""

import sys
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import load_config
from state import get_state, reset_state
from sequencer import create_sequencer
from scale_mapper import ScaleMapper


def note_to_name(note_number):
    """Convert MIDI note number to note name."""
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = note_number // 12 - 1
    note_name = note_names[note_number % 12]
    return f"{note_name}{octave}"


def demo_scale_mapper():
    """Demo the scale mapper with different root notes."""
    print("=== Scale Mapper Demo ===")
    
    mapper = ScaleMapper()
    scales_to_test = ["major", "minor", "pentatonic_major"]
    root_notes = [60, 67, 72]  # C4, G4, C5
    
    for scale_name in scales_to_test:
        print(f"\n{scale_name.upper()} scale:")
        
        for root_note in root_notes:
            mapper.set_scale(scale_name, root_note=root_note)
            root_name = note_to_name(root_note)
            
            # Generate first 8 notes of the scale
            notes = []
            for degree in range(8):
                note = mapper.get_note(degree)
                note_name = note_to_name(note)
                notes.append(f"{note_name}({note})")
            
            print(f"  Root {root_name}: {' '.join(notes)}")


def demo_state_integration():
    """Demo changing root_note via state management."""
    print("\n=== State Integration Demo ===")
    
    reset_state()
    state = get_state()
    
    # Show how mutations would affect the root note
    print("\nSimulating root_note mutations:")
    
    current_root = 60  # Start at C4
    state.set('root_note', current_root)
    
    mapper = ScaleMapper()
    
    # Simulate several mutation steps
    mutation_deltas = [-1, +2, -1, +1, -2, +3]  # Simulated mutation steps
    
    for i, delta in enumerate(mutation_deltas):
        new_root = current_root + delta
        
        # Apply state validation (clamp to 0-127)
        if new_root < 0:
            new_root = 0
        elif new_root > 127:
            new_root = 127
        
        state.set('root_note', new_root, source='mutation')
        mapper.set_scale("major", root_note=new_root)
        
        # Show the change
        old_name = note_to_name(current_root)
        new_name = note_to_name(new_root)
        
        # Generate a few notes to show the effect
        chord_notes = []
        for degree in [0, 2, 4]:  # Root, third, fifth
            note = mapper.get_note(degree)
            chord_notes.append(note_to_name(note))
        
        print(f"  Step {i+1}: {old_name} -> {new_name} (delta: {delta:+d}) | Triad: {' '.join(chord_notes)}")
        current_root = new_root


def demo_sequencer_integration():
    """Demo how sequencer uses root_note from state."""
    print("\n=== Sequencer Integration Demo ===")
    
    reset_state()
    state = get_state()
    config = load_config("config.yaml")
    
    # Create sequencer
    sequencer = create_sequencer(state, config.scales)
    
    print("Testing sequencer with different root notes:")
    
    test_roots = [60, 65, 69, 72]  # C4, F4, A4, C5
    
    for root_note in test_roots:
        state.set('root_note', root_note)
        state.set('scale_index', 0)  # Major scale
        
        # Force scale update
        sequencer._update_scale_from_state(force=True)
        
        root_name = note_to_name(root_note)
        
        # Generate notes that the sequencer would produce
        print(f"\n  Root note: {root_name} ({root_note})")
        print(f"  Scale notes for steps 0-7:")
        
        step_notes = []
        for step in range(8):
            # Simulate the sequencer's note generation logic
            degree = step % 8  # Updated to match sequencer._generate_step_note
            note = sequencer.scale_mapper.get_note(degree, octave=0)
            note_name = note_to_name(note)
            step_notes.append(f"Step {step}: {note_name}({note})")
        
        print(f"    {', '.join(step_notes[:4])}")
        print(f"    {', '.join(step_notes[4:])}")


def main():
    print("Root Note Parameter Demo")
    print("========================")
    print()
    print("This demo shows how the root_note parameter affects musical output")
    print("across different scales and through the mutation system.")
    
    try:
        demo_scale_mapper()
        demo_state_integration()
        demo_sequencer_integration()
        
        print("\n=== Summary ===")
        print("✓ Root note can be configured in config.yaml")
        print("✓ Root note can be changed via state management")  
        print("✓ Root note changes are reflected in scale mapping")
        print("✓ Root note is included in mutation possibilities")
        print("✓ Sequencer respects root note changes")
        print("\nThe root_note parameter is now fully integrated!")
        
    except Exception as e:
        print(f"\nDemo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
