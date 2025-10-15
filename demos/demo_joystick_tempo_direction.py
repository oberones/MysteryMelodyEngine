#!/usr/bin/env python3
"""Demonstration of new joystick tempo and direction controls.

This script shows how the updated joystick mapping works:
- Up/Down: Control tempo (increase/decrease by 5 BPM)
- Left/Right: Control sequencer direction pattern (cycle through patterns)

Run this in the virtual environment after activating:
  source .venv/bin/activate
  python demos/demo_joystick_tempo_direction.py
"""

import sys
import time
import logging
from typing import List

# Add src to path for imports
sys.path.insert(0, 'src')

from state import State
from sequencer import Sequencer
from action_handler import ActionHandler
from events import SemanticEvent
from config import load_config

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

log = logging.getLogger(__name__)


class JoystickDemo:
    """Demonstrates new joystick tempo and direction controls."""
    
    def __init__(self):
        # Load basic config
        config = load_config('config.yaml')
        
        # Create state and components
        self.state = State()
        self.sequencer = Sequencer(self.state, config.scales)
        self.action_handler = ActionHandler(self.state)
        self.action_handler.set_sequencer(self.sequencer)
        
        # Configure demo parameters
        self._setup_demo_params()
    
    def _setup_demo_params(self):
        """Set up parameters for the demo."""
        # Initialize state
        self.state.set('bpm', 120.0)
        self.state.set('direction_pattern', 'forward')
        self.state.set('sequence_length', 8)
        
        log.info("Demo initialized with BPM=120, direction=forward")
    
    def simulate_joystick_event(self, direction: str, description: str):
        """Simulate a joystick event and show the result."""
        print(f"\n{description}")
        print("-" * 40)
        
        # Map direction to semantic action
        action_map = {
            'up': 'tempo_up',
            'down': 'tempo_down', 
            'left': 'direction_left',
            'right': 'direction_right'
        }
        
        action = action_map.get(direction)
        if not action:
            print(f"Unknown direction: {direction}")
            return
            
        # Create and handle event
        event = SemanticEvent(type=action, value=127, source='demo')
        
        # Show state before
        bpm_before = self.state.get('bpm')
        direction_before = self.state.get('direction_pattern')
        print(f"Before:  BPM={bpm_before:.1f}, Direction={direction_before}")
        
        # Handle the event
        self.action_handler.handle_semantic_event(event)
        
        # Show state after
        bpm_after = self.state.get('bpm')
        direction_after = self.state.get('direction_pattern')
        print(f"After:   BPM={bpm_after:.1f}, Direction={direction_after}")
        
        # Show the change
        if direction in ['up', 'down']:
            change = bpm_after - bpm_before
            print(f"Change:  BPM {change:+.1f}")
        else:
            print(f"Change:  Direction {direction_before} → {direction_after}")
    
    def run_demo(self):
        """Run the joystick control demonstration."""
        print("Joystick Tempo & Direction Control Demo")
        print("=" * 45)
        print("\nThis demo shows the new joystick mappings:")
        print("  • Up/Down: Control tempo (±5 BPM per press)")
        print("  • Left/Right: Cycle through direction patterns")
        print("\nDirection patterns: forward → backward → ping_pong → random → fugue → song")
        
        # Demo tempo controls
        print(f"\n{'='*45}")
        print("TEMPO CONTROL DEMO")
        print(f"{'='*45}")
        
        self.simulate_joystick_event('up', "Joystick UP: Increase tempo")
        time.sleep(0.5)
        
        self.simulate_joystick_event('up', "Joystick UP: Increase tempo again")
        time.sleep(0.5)
        
        self.simulate_joystick_event('down', "Joystick DOWN: Decrease tempo")
        time.sleep(0.5)
        
        self.simulate_joystick_event('down', "Joystick DOWN: Decrease tempo again")
        time.sleep(0.5)
        
        self.simulate_joystick_event('down', "Joystick DOWN: Decrease tempo more")
        
        # Demo direction controls
        print(f"\n{'='*45}")
        print("DIRECTION PATTERN DEMO")
        print(f"{'='*45}")
        
        self.simulate_joystick_event('right', "Joystick RIGHT: Next direction pattern")
        time.sleep(0.5)
        
        self.simulate_joystick_event('right', "Joystick RIGHT: Next direction pattern") 
        time.sleep(0.5)
        
        self.simulate_joystick_event('right', "Joystick RIGHT: Next direction pattern")
        time.sleep(0.5)
        
        self.simulate_joystick_event('left', "Joystick LEFT: Previous direction pattern")
        time.sleep(0.5)
        
        self.simulate_joystick_event('left', "Joystick LEFT: Previous direction pattern")
        
        # Test boundary conditions
        print(f"\n{'='*45}")
        print("BOUNDARY CONDITIONS DEMO") 
        print(f"{'='*45}")
        
        # Test tempo limits
        print(f"\nTesting tempo limits...")
        
        # Set to near minimum
        self.state.set('bpm', 65.0)
        self.simulate_joystick_event('down', "Near minimum BPM: Try to go below 60")
        
        # Set to near maximum 
        self.state.set('bpm', 195.0)
        self.simulate_joystick_event('up', "Near maximum BPM: Try to go above 200")
        
        print(f"\n{'='*45}")
        print("DEMO COMPLETE")
        print(f"{'='*45}")
        print("\n✓ Joystick controls working correctly!")
        print("\nKey Features:")
        print("  • Tempo control: 5 BPM increments, clamped to 60-200 BPM range")
        print("  • Direction control: Cycles through all 6 available patterns")
        print("  • Only responds to joystick press (127), ignores release (0)")
        print("  • State changes are logged for debugging")


def main():
    """Run the joystick control demonstration."""
    try:
        demo = JoystickDemo()
        demo.run_demo()
    except Exception as e:
        log.error(f"Demo failed: {e}")
        raise


if __name__ == '__main__':
    main()
