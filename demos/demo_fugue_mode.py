"""Demonstration of fugue mode in the Mystery Melody Machine.

This script shows how to use the new fugue pattern style that generates
mini-fugues according to classical contrapuntal principles.
"""

import sys
import time
sys.path.append('src')

from state import State
from sequencer import Sequencer
from scale_mapper import ScaleMapper


def demo_fugue_mode():
    """Demonstrate fugue mode functionality."""
    print("=== Mystery Melody Machine - Fugue Mode Demo ===\n")
    
    # Initialize the sequencer
    state = State()
    scales = ['minor', 'major', 'pentatonic_minor', 'dorian', 'mixolydian']
    sequencer = Sequencer(state, scales)
    
    # Set up note callback to display generated notes
    notes_generated = []
    def note_callback(note_event):
        notes_generated.append(note_event)
        print(f"♪ Note: MIDI {note_event.note:3d} | Vel {note_event.velocity:3d} | "
              f"Duration {note_event.duration:.3f}s | Step {note_event.step:2d}")
    
    sequencer.set_note_callback(note_callback)
    
    # Test different scales with fugue mode
    test_scales = [
        ("C Minor", 60, "minor"),
        ("D Dorian", 62, "dorian"), 
        ("G Major", 67, "major")
    ]
    
    for scale_name, root_note, scale_mode in test_scales:
        print(f"\n--- Testing Fugue in {scale_name} ---")
        
        # Set the scale
        state.set('root_note', root_note, source='demo')
        scale_index = scales.index(scale_mode) if scale_mode in scales else 0
        state.set('scale_index', scale_index, source='demo')
        
        # Set fugue pattern
        sequencer.set_direction_pattern('fugue')
        
        # Generate some notes
        print("Generating fugue exposition...")
        notes_generated.clear()
        
        for step in range(12):  # Generate 12 steps
            sequencer._generate_step_note(step)
        
        print(f"Generated {len(notes_generated)} notes for {scale_name}")
        
        # Show pitch range
        if notes_generated:
            pitches = [note.note for note in notes_generated]
            print(f"Pitch range: {min(pitches)} - {max(pitches)} "
                  f"(span: {max(pitches) - min(pitches)} semitones)")
        
        time.sleep(0.5)  # Brief pause between scales
    
    # Test parameter variations
    print(f"\n--- Testing Parameter Variations ---")
    
    # Higher density for more stretto-like effect
    print("\nHigh density (more stretto):")
    state.set('density', 0.9, source='demo')
    sequencer.set_direction_pattern('fugue')
    
    notes_generated.clear()
    for step in range(8):
        sequencer._generate_step_note(step)
    print(f"Generated {len(notes_generated)} notes with high density")
    
    # Lower density for sparser texture
    print("\nLow density (sparser texture):")
    state.set('density', 0.3, source='demo')
    sequencer.set_direction_pattern('fugue')
    
    notes_generated.clear()
    for step in range(8):
        sequencer._generate_step_note(step)
    print(f"Generated {len(notes_generated)} notes with low density")
    
    # Test pattern switching
    print(f"\n--- Testing Pattern Switching ---")
    patterns = ['forward', 'backward', 'ping_pong', 'random', 'fugue']
    
    for pattern in patterns:
        print(f"\nSwitching to {pattern} pattern...")
        sequencer.set_direction_pattern(pattern)
        current = state.get('direction_pattern')
        print(f"Current pattern: {current}")
        
        if pattern == 'fugue':
            print("Fugue sequencer active:", sequencer._fugue_sequencer is not None)
    
    print(f"\n=== Demo Complete ===")
    print(f"Fugue mode is now available as a direction_pattern option!")
    print(f"Set 'direction_pattern: fugue' in your config.yaml to use it.")


if __name__ == "__main__":
    demo_fugue_mode()
