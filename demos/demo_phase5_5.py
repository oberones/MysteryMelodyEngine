#!/usr/bin/env python3
"""
Demo script for Phase 5.5: Enhanced Probability & Rhythm Patterns

This script demonstrates the new per-step probability arrays, configurable step patterns,
and velocity variation features added in Phase 5.5.
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from state import State
from sequencer import Sequencer, NoteEvent

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def demo_phase5_5():
    """Demonstrate Phase 5.5 features."""
    
    # Create state and sequencer
    state = State()
    sequencer = Sequencer(state, ['major', 'minor', 'pentatonic'])
    
    print("=== Phase 5.5 Demo: Enhanced Probability & Rhythm Patterns ===\n")
    
    # Collection to capture generated notes
    generated_notes = []
    
    def capture_note(note_event: NoteEvent):
        generated_notes.append(note_event)
        print(f"♪ Step {note_event.step}: Note {note_event.note} (vel {note_event.velocity})")
    
    sequencer.set_note_callback(capture_note)
    
    # Demo 1: Pattern presets
    print("1. Pattern Presets Demo")
    print("-" * 30)
    
    patterns_to_test = ['four_on_floor', 'offbeat', 'syncopated', 'dense']
    
    for pattern_name in patterns_to_test:
        print(f"\nPattern: {pattern_name}")
        pattern = sequencer.get_pattern_preset(pattern_name)
        print(f"Pattern: {pattern}")
        
        sequencer.set_step_pattern(pattern)
        state.set('density', 1.0)  # Ensure density doesn't gate
        state.set('note_probability', 1.0)  # Use old fallback for this demo
        
        generated_notes.clear()
        for step in range(8):
            sequencer._generate_step_note(step)
        
        active_steps = [note.step for note in generated_notes]
        print(f"Active steps: {active_steps}")
    
    # Demo 2: Probability presets
    print("\n\n2. Probability Presets Demo")
    print("-" * 35)
    
    prob_presets = ['uniform', 'crescendo', 'peaks', 'alternating']
    
    # Use all-on pattern for probability demo
    all_on_pattern = sequencer.get_pattern_preset('all_on')
    sequencer.set_step_pattern(all_on_pattern)
    
    for preset_name in prob_presets:
        print(f"\nProbability preset: {preset_name}")
        probs = sequencer.get_probability_preset(preset_name, length=8)
        print(f"Probabilities: {[f'{p:.2f}' for p in probs]}")
        
        sequencer.set_step_probabilities(probs)
        
        # Run multiple times to see probability effects
        step_hit_counts = [0] * 8
        trials = 100
        
        for trial in range(trials):
            for step in range(8):
                generated_notes.clear()
                sequencer._generate_step_note(step)
                if generated_notes:
                    step_hit_counts[step] += 1
        
        hit_rates = [count / trials for count in step_hit_counts]
        print(f"Actual rates:   {[f'{r:.2f}' for r in hit_rates]}")
    
    # Demo 3: Velocity variation
    print("\n\n3. Velocity Variation Demo")
    print("-" * 32)
    
    # Set up a pattern with varying probabilities
    varied_probs = [1.0, 0.8, 0.6, 0.4, 0.2, 0.6, 0.8, 1.0]
    sequencer.set_step_probabilities(varied_probs)
    sequencer.set_velocity_params(base_velocity=80, velocity_range=40)
    
    print("Probability pattern: ", [f'{p:.1f}' for p in varied_probs])
    print("Base velocity: 80, Range: ±40")
    print("\nGenerated notes with velocity variation:")
    
    generated_notes.clear()
    state.set('density', 1.0)
    
    for step in range(8):
        sequencer._generate_step_note(step)
    
    for note in generated_notes:
        step_prob = varied_probs[note.step]
        print(f"Step {note.step} (prob {step_prob:.1f}): velocity {note.velocity}")
    
    # Demo 4: Backward compatibility
    print("\n\n4. Backward Compatibility Demo")
    print("-" * 37)
    
    # Clear new-style parameters to test fallback
    state.set('step_probabilities', None)
    state.set('step_pattern', None)
    state.set('note_probability', 0.8)  # Old-style global probability
    
    print("Using legacy parameters (step_probabilities=None, step_pattern=None)")
    print("note_probability=0.8, should use even-step pattern")
    
    generated_notes.clear()
    
    # Test multiple times to see probability
    step_hit_counts = [0] * 8
    trials = 50
    
    for trial in range(trials):
        for step in range(8):
            generated_notes.clear()
            sequencer._generate_step_note(step)
            if generated_notes:
                step_hit_counts[step] += 1
    
    hit_rates = [count / trials for count in step_hit_counts]
    print("Hit rates by step:", [f'{r:.2f}' for r in hit_rates])
    print("Expected: High rates on even steps (0,2,4,6), zero on odd steps")
    
    # Demo 5: Direction patterns
    print("\n\n5. Direction Patterns Demo")
    print("-" * 30)
    
    direction_patterns = ['forward', 'backward', 'ping_pong', 'random']
    
    # Set up for direction demo
    state.set('sequence_length', 4)  # Short sequence for clearer demonstration
    sequencer.set_step_pattern([True] * 4)  # All steps active
    sequencer.set_step_probabilities([1.0] * 4)  # Always trigger
    
    for direction in direction_patterns:
        print(f"\nDirection: {direction}")
        sequencer.set_direction_pattern(direction)
        
        # Simulate step advancement to show pattern
        current_step = 0
        sequence_length = 4
        step_sequence = [current_step]
        
        for _ in range(8):  # Show 8 steps
            current_step = sequencer._get_next_step(current_step, sequence_length)
            step_sequence.append(current_step)
        
        print(f"Step sequence: {' → '.join(map(str, step_sequence))}")
    
    print("\n=== Demo Complete ===")
    print("\nPhase 5.5 Features Demonstrated:")
    print("✓ Pattern presets (four_on_floor, offbeat, syncopated, dense)")
    print("✓ Probability presets (uniform, crescendo, peaks, alternating)")
    print("✓ Velocity variation based on step probability")
    print("✓ Direction patterns (forward, backward, ping_pong, random)")
    print("✓ Backward compatibility with legacy parameters")

if __name__ == '__main__':
    demo_phase5_5()
