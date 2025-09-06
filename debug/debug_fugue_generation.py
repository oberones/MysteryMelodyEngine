#!/usr/bin/env python3
"""Debug fugue generation to understand why it's producing so few notes."""

import sys
import time
sys.path.append('src')
from state import State
from scale_mapper import ScaleMapper
from fugue import FugueSequencer, FugueParams, FugueEngine

def debug_fugue_generation():
    """Debug the fugue generation process step by step."""
    
    print("=== Debugging Fugue Generation ===\n")
    
    # Set up basic components
    state = State()
    state.set('bpm', 120.0)
    state.set('sequence_length', 8)
    state.set('density', 0.7)
    state.set('root_note', 60)
    state.set('scale_index', 0)  # C minor
    
    scale_mapper = ScaleMapper()
    scale_mapper.set_scale('minor', root_note=60)
    
    # Create fugue sequencer
    fugue_sequencer = FugueSequencer(state, scale_mapper)
    
    print("--- Step 1: Testing FugueEngine directly ---")
    
    # Test the fugue engine directly
    fugue_engine = FugueEngine(scale_mapper)
    
    params = FugueParams(
        n_voices=3,
        key_root=60,
        mode="minor",
        entry_gap_beats=2.0,
        stretto_overlap=0.5,
        use_tonal_answer=True,
    )
    
    # Generate subject
    print("Generating subject...")
    subject = fugue_engine.generate_subject(params, bars=1)
    print(f"Subject length: {len(subject)} notes")
    print(f"Subject total duration: {sum(n['dur'] for n in subject):.2f} quarter notes")
    for i, note in enumerate(subject):
        print(f"  Note {i}: pitch={note['pitch']}, dur={note['dur']:.2f}, vel={note['vel']}")
    
    # Generate complete fugue
    print("\nGenerating complete fugue...")
    fugue_score = fugue_engine.render_fugue(subject, params)
    print(f"Number of voices: {len(fugue_score)}")
    for voice_idx, voice in enumerate(fugue_score):
        voice_duration = sum(n['dur'] for n in voice)
        print(f"  Voice {voice_idx}: {len(voice)} notes, total duration: {voice_duration:.2f} quarter notes")
        for i, note in enumerate(voice):
            print(f"    Note {i}: pitch={note['pitch']}, dur={note['dur']:.2f}, vel={note['vel']}")
    
    print("\n--- Step 2: Testing FugueSequencer behavior ---")
    
    # Debug the parameters calculation
    n_voices_calc = min(4, max(2, state.get('sequence_length', 8) // 4))
    print(f"Calculated n_voices: {n_voices_calc} (sequence_length={state.get('sequence_length', 8)})")
    
    # Start a new fugue in the sequencer
    fugue_sequencer.start_new_fugue()
    
    # Debug the voice setup
    print(f"Active fugue voices: {len(fugue_sequencer._active_fugue) if fugue_sequencer._active_fugue else 0}")
    print(f"Voice positions length: {len(fugue_sequencer._voice_positions)}")
    print(f"Voice next times length: {len(fugue_sequencer._voice_next_times)}")
    print(f"Voice next times: {fugue_sequencer._voice_next_times}")
    
    if fugue_sequencer._active_fugue:
        for i, voice in enumerate(fugue_sequencer._active_fugue):
            print(f"  Voice {i}: {len(voice)} notes")
    
    # Simulate step calls like the main sequencer would do
    print("\nSimulating sequencer steps...")
    for step in range(20):  # Test 20 steps
        note_result = fugue_sequencer.get_next_step_note(step)
        if note_result:
            note, velocity, duration = note_result
            print(f"Step {step:2d}: Note {note:3d}, Vel {velocity:3d}, Dur {duration:.3f}s")
        else:
            print(f"Step {step:2d}: No note")
        
        # Show timing state every few steps
        if step % 5 == 0:
            print(f"    Musical time: {fugue_sequencer._fugue_musical_time:.2f}, "
                  f"Voice positions: {fugue_sequencer._voice_positions}, "
                  f"Voice next times: {fugue_sequencer._voice_next_times}")
        
        # Small delay to simulate real timing
        time.sleep(0.01)
    
    print("\n--- Step 3: Testing musical timing calculations ---")
    
    # Test the musical timing calculations
    bpm = 120.0
    quarter_note_duration = 60.0 / bpm  # 0.5 seconds at 120 BPM
    print(f"Quarter note duration at {bpm} BPM: {quarter_note_duration:.3f} seconds")
    
    # Check if fugue is still active
    active_fugue = fugue_sequencer._active_fugue
    print(f"Active fugue exists: {active_fugue is not None}")
    if active_fugue:
        print(f"Voice positions: {fugue_sequencer._voice_positions}")
        print(f"Voice next times: {fugue_sequencer._voice_next_times}")
        print(f"Fugue musical time: {fugue_sequencer._fugue_musical_time:.2f}")
    
    print("\n=== Debug Complete ===")

if __name__ == "__main__":
    debug_fugue_generation()
