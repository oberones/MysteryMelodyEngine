#!/usr/bin/env python3
"""Demo script to show the mutation engine in action.

This script demonstrates the mutation engine functionality by:
1. Creating a state and mutation engine
2. Forcing mutations and showing the results
3. Displaying mutation history and statistics
"""

import sys
import time
sys.path.append('src')

from config import MutationConfig
from state import State, get_state
from mutation import create_mutation_engine
from logging_utils import configure_logging

def main():
    # Configure logging to see mutation events
    configure_logging("INFO")
    
    print("=== Mutation Engine Demo ===\n")
    
    # Create configuration for faster mutations (for demo)
    config = MutationConfig(
        interval_min_s=5,  # Short interval for demo
        interval_max_s=10,
        max_changes_per_cycle=2
    )
    
    # Get global state and set some initial values
    state = get_state()
    initial_values = {
        'bpm': 120.0,
        'density': 0.8,
        'swing': 0.12,
        'note_probability': 0.9,
        'filter_cutoff': 64,
        'reverb_mix': 32,
        'sequence_length': 8,
        'drift': 0.0
    }
    
    print("Initial parameter values:")
    for param, value in initial_values.items():
        state.set(param, value, source="demo")
        print(f"  {param}: {value}")
    
    # Create mutation engine
    mutation_engine = create_mutation_engine(config, state)
    
    print(f"\nMutation engine created with {len(mutation_engine._rules)} rules")
    print(f"Mutation interval: {config.interval_min_s}-{config.interval_max_s}s")
    print(f"Max changes per cycle: {config.max_changes_per_cycle}")
    
    # Show mutation rules
    print("\nMutation rules:")
    for rule in mutation_engine._rules:
        print(f"  {rule.parameter}: weight={rule.weight}, delta_range={rule.delta_range}, desc='{rule.description}'")
    
    print("\n=== Forcing 3 mutation cycles ===\n")
    
    # Force some mutations and show results
    for i in range(3):
        print(f"--- Mutation cycle {i+1} ---")
        
        # Capture state before mutation
        before_state = state.get_all()
        
        # Force mutation
        mutation_engine.force_mutation()
        
        # Show what changed
        after_state = state.get_all()
        changes_found = False
        
        for param in before_state:
            if before_state[param] != after_state[param]:
                print(f"  {param}: {before_state[param]} → {after_state[param]}")
                changes_found = True
        
        if not changes_found:
            print("  No changes applied this cycle")
        
        time.sleep(0.5)  # Brief pause between cycles
    
    # Show mutation history
    print("\n=== Mutation History ===")
    history = mutation_engine.get_history()
    
    if history:
        print(f"Total mutations applied: {len(history)}")
        for i, event in enumerate(history):
            print(f"  {i+1}. {event.parameter}: {event.old_value} → {event.new_value} "
                  f"(δ={event.delta:.3f}) - {event.rule_description}")
    else:
        print("No mutations recorded yet")
    
    # Show statistics
    print("\n=== Engine Statistics ===")
    stats = mutation_engine.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n=== Final parameter values ===")
    final_state = state.get_all()
    for param in sorted(final_state.keys()):
        initial = initial_values.get(param, "N/A")
        final = final_state[param]
        changed = "✓" if initial != final else " "
        print(f"  {changed} {param}: {initial} → {final}")
    
    print("\nDemo complete!")


if __name__ == "__main__":
    main()
