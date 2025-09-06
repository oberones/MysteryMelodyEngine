#!/usr/bin/env python3
"""Demo script for the NTS-1 mutation plugin.

This script demonstrates how to use the custom NTS-1 mutation plugin
with different styles (default, ambient, rhythmic) and shows the
comprehensive parameter coverage.
"""

import sys
import time
import logging
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import load_config, MutationConfig
from state import State
from mutation import MutationEngine
from nts1_mutation_plugin import setup_nts1_mutations, register_nts1_rules
from cc_profiles import get_profile

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)


def demo_nts1_cc_profile():
    """Demonstrate the corrected NTS-1 CC profile."""
    print("\n=== NTS-1 mkII CC Profile Demo ===")
    
    profile = get_profile("korg_nts1_mk2")
    if not profile:
        print("ERROR: NTS-1 profile not found!")
        return
    
    print(f"Profile: {profile.name}")
    print(f"Description: {profile.description}")
    print(f"Total parameters: {len(profile.parameters)}")
    print()
    
    # Show some key parameters and their CC mappings
    key_params = [
        "filter_cutoff", "filter_resonance", "filter_type",
        "eg_attack", "eg_release", "eg_type",
        "osc_a", "osc_b", "osc_type",
        "reverb_mix", "delay_mix",
        "mod_type", "delay_type", "reverb_type"
    ]
    
    print("Key Parameter Mappings:")
    print("Parameter Name          | CC | Range    | Curve      | Steps | Description")
    print("-" * 80)
    
    for param_name in key_params:
        if param_name in profile.parameters:
            param = profile.parameters[param_name]
            steps_str = f"{param.steps}" if param.steps else "N/A"
            print(f"{param_name:22} | {param.cc:2} | {param.range[0]:3}-{param.range[1]:3} | {param.curve.value:10} | {steps_str:5} | {param.name}")
    
    print()
    
    # Demonstrate parameter scaling
    print("Parameter Scaling Examples (input 0.0-1.0 -> CC value):")
    test_values = [0.0, 0.25, 0.5, 0.75, 1.0]
    
    for param_name in ["filter_cutoff", "eg_attack", "osc_type"]:
        if param_name in profile.parameters:
            param = profile.parameters[param_name]
            print(f"\n{param.name} (CC {param.cc}, {param.curve.value} curve):")
            
            for value in test_values:
                cc_value = param.scale_value(value)
                print(f"  {value:4.2f} -> {cc_value:3}")


def demo_mutation_rules(style: str = "default"):
    """Demonstrate NTS-1 mutation rules."""
    print(f"\n=== NTS-1 Mutation Rules Demo ({style}) ===")
    
    # Create minimal config for mutation engine
    config = MutationConfig(
        interval_min_s=5,
        interval_max_s=10,
        max_changes_per_cycle=3
    )
    
    # Create state and mutation engine
    state = State()
    mutation_engine = MutationEngine(config, state)
    
    # Set up NTS-1 mutations
    setup_nts1_mutations(mutation_engine, state, style)
    
    print(f"Initialized {len(mutation_engine._rules)} mutation rules")
    print(f"State has {len([k for k in state._params.keys() if not k.startswith('_')])} parameters")
    
    # Show rule breakdown by parameter category
    rule_categories = {
        "Oscillator": ["osc_", "tremolo_"],
        "Filter": ["filter_"],
        "Envelope": ["eg_"],
        "Modulation": ["mod_"],
        "Delay": ["delay_"],
        "Reverb": ["reverb_"],
        "Arpeggiator": ["arp_"],
        "Master": ["master_"]
    }
    
    print("\nRule breakdown by category:")
    for category, prefixes in rule_categories.items():
        count = sum(1 for rule in mutation_engine._rules 
                   if any(rule.parameter.startswith(prefix) for prefix in prefixes))
        print(f"  {category:12}: {count:2} rules")
    
    # Enable mutations (simulate idle state)
    mutation_engine._mutations_enabled = True
    
    # Demonstrate some mutations
    print(f"\nDemonstrating mutations...")
    
    for i in range(3):
        print(f"\n--- Mutation Cycle {i+1} ---")
        
        # Show some parameter values before mutation
        sample_params = ["filter_cutoff", "eg_attack", "reverb_mix", "osc_a"]
        print("Before mutation:")
        for param in sample_params:
            value = state.get(param)
            print(f"  {param}: {value}")
        
        # Force a mutation
        mutation_engine.force_mutation()
        
        # Show values after mutation
        print("After mutation:")
        for param in sample_params:
            value = state.get(param)
            print(f"  {param}: {value}")
        
        # Show what was mutated
        recent_mutations = mutation_engine.get_history(3)
        if recent_mutations:
            print("Applied mutations:")
            for mut in recent_mutations[-3:]:
                print(f"  {mut.parameter}: {mut.old_value:.1f} -> {mut.new_value:.1f} ({mut.rule_description})")
        
        time.sleep(1)


def demo_cc_output():
    """Demonstrate how mutations translate to CC messages."""
    print(f"\n=== CC Output Demo ===")
    
    profile = get_profile("korg_nts1_mk2")
    state = State()
    
    # Set up some NTS-1 parameters in state
    from nts1_mutation_plugin import register_nts1_state_parameters
    register_nts1_state_parameters(state)
    
    # Simulate some parameter changes and show resulting CC messages
    changes = [
        ("filter_cutoff", 0.3),   # Low-pass filter at 30%
        ("filter_cutoff", 0.8),   # Low-pass filter at 80%
        ("eg_attack", 0.1),       # Quick attack
        ("eg_attack", 0.9),       # Slow attack
        ("reverb_mix", 0.6),      # Moderate reverb
        ("osc_type", 0.5),        # Different oscillator type
    ]
    
    print("Parameter changes -> MIDI CC messages:")
    print("Parameter           | Value | CC# | CC Value | Description")
    print("-" * 65)
    
    for param_name, value in changes:
        if profile.has_parameter(param_name):
            cc_mapping = profile.map_parameter(param_name, value)
            if cc_mapping:
                cc_num, cc_value = cc_mapping
                param = profile.parameters[param_name]
                print(f"{param_name:18} | {value:5.2f} | {cc_num:3} | {cc_value:8} | {param.name}")


def main():
    """Run all demos."""
    print("NTS-1 mkII Mutation Plugin Demo")
    print("=" * 40)
    
    # Demo the corrected CC profile
    demo_nts1_cc_profile()
    
    # Demo different mutation styles
    for style in ["default", "ambient", "rhythmic"]:
        demo_mutation_rules(style)
        time.sleep(1)
    
    # Demo CC output
    demo_cc_output()
    
    print("\n=== Demo Complete ===")
    print("To use this plugin in your application:")
    print("1. Import: from nts1_mutation_plugin import setup_nts1_mutations")
    print("2. Call: setup_nts1_mutations(mutation_engine, state, 'ambient')")
    print("3. The plugin will register all parameters and mutation rules")
    print("4. Use cc_profile 'korg_nts1_mk2' for proper MIDI CC mapping")


if __name__ == "__main__":
    main()
