"""Demonstration of song mode in the Mystery Melody Machine.

This script shows how to use the new song pattern style that generates
structured compositions using common song forms like verse-chorus patterns.
"""

import sys
import time
sys.path.append('src')

from state import State
from sequencer import Sequencer
from scale_mapper import ScaleMapper


def demo_song_mode():
    """Demonstrate song mode functionality."""
    print("=== Mystery Melody Machine - Song Mode Demo ===\n")
    
    # Initialize the sequencer
    state = State()
    scales = ['minor', 'major', 'pentatonic_minor', 'dorian', 'mixolydian', 'blues']
    sequencer = Sequencer(state, scales)
    
    # Set up note callback to display generated notes
    notes_generated = []
    def note_callback(note_event):
        notes_generated.append(note_event)
        print(f"♪ Note: MIDI {note_event.note:3d} | Vel {note_event.velocity:3d} | "
              f"Duration {note_event.duration:.3f}s | Step {note_event.step:2d}")
    
    sequencer.set_note_callback(note_callback)
    
    # Test different scales with song mode
    test_configurations = [
        ("C Minor Blues", 60, "blues", 1),
        ("D Dorian Pop", 62, "dorian", 2), 
        ("G Major Song", 67, "major", 3)
    ]
    
    for config_name, root_note, scale_mode, voices in test_configurations:
        print(f"\n--- Testing Song Mode: {config_name} ({voices} voice{'s' if voices != 1 else ''}) ---")
        
        # Set the scale and configuration
        state.set('root_note', root_note, source='demo')
        state.set('voices', voices, source='demo')
        state.set('bpm', 120, source='demo')
        
        scale_index = scales.index(scale_mode) if scale_mode in scales else 0
        state.set('scale_index', scale_index, source='demo')
        
        # Set song pattern
        sequencer.set_direction_pattern('song')
        
        # Generate some notes to demonstrate song structure
        print("Generating song composition...")
        notes_generated.clear()
        
        # Simulate several steps to show song progression
        for step in range(32):  # Generate 32 steps to show section changes
            sequencer._generate_step_note(step)
            
            # Check song info every 8 steps
            if step % 8 == 0 and sequencer._song_sequencer:
                song_info = sequencer._song_sequencer.get_current_song_info()
                if song_info['status'] == 'playing' and song_info['section']:
                    section = song_info['section']
                    print(f"  Step {step:2d}: {section['type'].upper()} "
                          f"(bar {section['bars_completed']}/{section['bars']}) "
                          f"density={section['density']:.2f}")
        
        print(f"Generated {len(notes_generated)} notes for {config_name}")
        
        # Show pitch range and velocity range
        if notes_generated:
            pitches = [note.note for note in notes_generated]
            velocities = [note.velocity for note in notes_generated]
            print(f"Pitch range: {min(pitches)} - {max(pitches)} "
                  f"(span: {max(pitches) - min(pitches)} semitones)")
            print(f"Velocity range: {min(velocities)} - {max(velocities)}")
        
        time.sleep(0.5)  # Brief pause between configurations
    
    # Test song pattern switching
    print(f"\n--- Testing Song Pattern Progression ---")
    
    # Set a longer test to show multiple song patterns
    state.set('root_note', 60, source='demo')  # C
    state.set('scale_index', 0, source='demo')  # Minor
    state.set('voices', 2, source='demo')
    sequencer.set_direction_pattern('song')
    
    print("Demonstrating automatic song pattern selection and progression...")
    notes_generated.clear()
    
    if sequencer._song_sequencer:
        # Force start a new song to demonstrate
        sequencer._song_sequencer.force_new_song()
        
        # Show song info
        song_info = sequencer._song_sequencer.get_current_song_info()
        if song_info['status'] == 'playing':
            print(f"Current song: {song_info['pattern']}")
            print(f"Estimated duration: {song_info['estimated_duration']/60:.1f} minutes")
            print(f"Total sections: {song_info['total_sections']}")
        
        # Generate through several sections
        for step in range(64):
            sequencer._generate_step_note(step)
            
            # Show section transitions
            if step % 4 == 0:
                song_info = sequencer._song_sequencer.get_current_song_info()
                if song_info['status'] == 'playing' and song_info['section']:
                    section = song_info['section']
                    section_progress = f"{song_info['section_index']+1}/{song_info['total_sections']}"
                    print(f"  Step {step:2d}: {section['type'].upper()} {section_progress} "
                          f"| bars {section['bars_completed']}/{section['bars']} "
                          f"| density={section['density']:.1f} tempo×{section['tempo_factor']:.1f}")
                elif song_info['status'] == 'between_songs':
                    time_left = song_info.get('time_until_next_song', 0)
                    print(f"  Step {step:2d}: BETWEEN SONGS (next in {time_left:.1f}s)")
    
    print(f"Generated {len(notes_generated)} notes total")
    
    # Test pattern switching back to other modes
    print(f"\n--- Testing Pattern Switching ---")
    patterns = ['forward', 'backward', 'ping_pong', 'random', 'fugue', 'song']
    
    for pattern in patterns:
        print(f"\nSwitching to {pattern} pattern...")
        sequencer.set_direction_pattern(pattern)
        current = state.get('direction_pattern')
        print(f"Current pattern: {current}")
        
        if pattern == 'song':
            print("Song sequencer active:", sequencer._song_sequencer is not None)
        elif pattern == 'fugue':
            print("Fugue sequencer active:", sequencer._fugue_sequencer is not None)
    
    print(f"\n=== Demo Complete ===")
    print(f"Song mode is now available as a direction_pattern option!")
    print(f"Set 'direction_pattern: song' in your config.yaml to use it.")
    print(f"\nSong patterns available:")
    from song import SONG_PATTERNS
    for pattern_name, pattern in SONG_PATTERNS.items():
        print(f"  - {pattern.name} ({pattern.estimated_duration_minutes:.1f} min, {len(pattern.sections)} sections)")


if __name__ == "__main__":
    demo_song_mode()
