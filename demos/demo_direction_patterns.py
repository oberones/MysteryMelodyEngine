#!/usr/bin/env python3
"""Demonstration of Phase 5.5 direction pattern capabilities.

This script shows how the new sequencer direction patterns work:
- Forward (default)
- Backward 
- Ping-pong (bouncing)
- Random

Run this in the virtual environment after activating:
  source .venv/bin/activate
  python demo_direction_patterns.py
"""

import sys
import time
import logging
from typing import List

# Add src to path for imports
sys.path.insert(0, 'src')

from state import State
from sequencer import Sequencer, NoteEvent
from config import load_config

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

class DirectionPatternDemo:
    """Demonstrates sequencer direction patterns."""
    
    def __init__(self):
        # Load basic config
        config = load_config('config.yaml')
        
        # Create state and sequencer
        self.state = State()
        self.sequencer = Sequencer(self.state, config.scales)
        
        # Track generated notes for demonstration
        self.generated_notes: List[tuple] = []
        self.sequencer.set_note_callback(self._note_callback)
        
        # Configure demo parameters
        self._setup_demo_params()
    
    def _setup_demo_params(self):
        """Set up parameters for the demo."""
        # Basic sequencer settings
        self.state.set('bpm', 120.0)
        self.state.set('sequence_length', 6)  # Shorter sequence for clearer patterns
        self.state.set('density', 1.0)  # Always trigger for clearer demonstration
        
        # Use a simple pattern with all steps active
        self.sequencer.set_step_pattern([True] * 6)
        
        # Use uniform high probability
        self.sequencer.set_step_probabilities([1.0] * 6)
        
        # Set velocity for consistent output
        self.sequencer.set_velocity_params(base_velocity=100, velocity_range=0)
    
    def _note_callback(self, note_event: NoteEvent):
        """Callback to track generated notes."""
        self.generated_notes.append((note_event.step, note_event.note, time.time()))
        print(f"  Step {note_event.step}: Note {note_event.note} (velocity {note_event.velocity})")
    
    def demonstrate_pattern(self, pattern_name: str, steps_to_show: int = 12):
        """Demonstrate a specific direction pattern."""
        print(f"\n{'='*50}")
        print(f"Direction Pattern: {pattern_name.upper()}")
        print(f"{'='*50}")
        
        # Clear previous notes
        self.generated_notes.clear()
        
        # Set the direction pattern
        self.sequencer.set_direction_pattern(pattern_name)
        
        # Start sequencer
        self.sequencer.start()
        
        print(f"Showing {steps_to_show} steps (sequence length: {self.state.get('sequence_length')})")
        print("Step sequence:")
        
        # Let it run for the specified number of steps
        start_time = time.time()
        step_count = 0
        
        while step_count < steps_to_show:
            time.sleep(0.1)  # Small sleep to prevent busy waiting
            if len(self.generated_notes) > step_count:
                step_count = len(self.generated_notes)
        
        # Stop sequencer
        self.sequencer.stop()
        
        # Show pattern summary
        if self.generated_notes:
            step_sequence = [note[0] for note in self.generated_notes[:steps_to_show]]
            print(f"\nStep sequence: {' → '.join(map(str, step_sequence))}")
            self._analyze_pattern(pattern_name, step_sequence)
        
        time.sleep(1)  # Brief pause between demonstrations
    
    def _analyze_pattern(self, pattern_name: str, step_sequence: List[int]):
        """Analyze and explain the pattern behavior."""
        print(f"\nPattern Analysis:")
        
        if pattern_name == 'forward':
            print("  - Steps advance in ascending order: 0→1→2→3...")
            print("  - Wraps around from end to beginning")
        
        elif pattern_name == 'backward':
            print("  - Steps advance in descending order: 3→2→1→0...")
            print("  - Wraps around from beginning to end")
        
        elif pattern_name == 'ping_pong':
            print("  - Steps bounce between boundaries")
            print("  - Direction reverses at sequence ends")
            # Check for direction changes
            direction_changes = 0
            for i in range(1, len(step_sequence) - 1):
                prev_diff = step_sequence[i] - step_sequence[i-1]
                next_diff = step_sequence[i+1] - step_sequence[i]
                if (prev_diff > 0 and next_diff < 0) or (prev_diff < 0 and next_diff > 0):
                    direction_changes += 1
            print(f"  - Direction changes detected: {direction_changes}")
        
        elif pattern_name == 'random':
            print("  - Steps chosen randomly (no pattern)")
            unique_steps = len(set(step_sequence))
            print(f"  - Unique steps visited: {unique_steps}")
            # Check for consecutiveness (should be low in random)
            consecutive = sum(1 for i in range(1, len(step_sequence)) 
                            if abs(step_sequence[i] - step_sequence[i-1]) <= 1)
            print(f"  - Consecutive step transitions: {consecutive}/{len(step_sequence)-1}")
    
    def run_all_demos(self):
        """Run demonstrations of all direction patterns."""
        print("Phase 5.5 Direction Pattern Demonstration")
        print("========================================")
        print("\nThis demo shows how sequencer direction patterns affect step progression.")
        print("Each pattern will play 12 steps to show the behavior clearly.")
        
        patterns = ['forward', 'backward', 'ping_pong', 'random']
        
        for pattern in patterns:
            self.demonstrate_pattern(pattern, steps_to_show=12)
        
        print(f"\n{'='*50}")
        print("DEMONSTRATION COMPLETE")
        print(f"{'='*50}")
        print("\nAll direction patterns demonstrated!")
        print("\nKey Features:")
        print("  • Forward: Traditional left-to-right progression (default)")
        print("  • Backward: Right-to-left progression")
        print("  • Ping-pong: Bouncing between sequence boundaries")
        print("  • Random: Unpredictable step selection")
        print("\nDirection patterns work with all other Phase 5.5 features:")
        print("  • Per-step probability arrays")
        print("  • Configurable step patterns")
        print("  • Velocity variation")
        print("  • All existing probability and mutation features")


def main():
    """Run the direction pattern demonstration."""
    try:
        demo = DirectionPatternDemo()
        demo.run_all_demos()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
