#!/usr/bin/env python3
"""
Verification script to ensure all MIDI CC inputs are properly routed to semantic events.
Compares roadmap specification with current implementation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import yaml
from config import load_config
from action_handler import ActionHandler
from state import State

def main():
    print("🔍 Verifying MIDI CC Mapping Implementation")
    print("=" * 50)
    
    # Load current config
    config = load_config('config.yaml')
    cc_mappings = config.mapping.get('ccs', {})
    
    # Create action handler to check available handlers
    state = State()
    handler = ActionHandler(state)
    available_handlers = set(handler._action_handlers.keys())
    
    # Roadmap-specified CC mappings (from ROADMAP.md Section 4)
    roadmap_ccs = {
        "20": "tempo",
        "21": "filter_cutoff", 
        "22": "reverb_mix",
        "23": "swing",
        "24": "density",
        "25": "master_volume",
        "50": "sequence_length",
        "51": "scale_select", 
        "52": "chaos_lock",
        "53": "reserved",
        "60": "mode",
        "61": "palette",
        "62": "drift"
    }
    
    print("📋 Roadmap-specified CC mappings:")
    for cc, action in roadmap_ccs.items():
        print(f"  CC {cc:>2} -> {action}")
    
    print(f"\n📋 Current config CC mappings:")
    for cc, action in cc_mappings.items():
        print(f"  CC {cc:>2} -> {action}")
    
    print(f"\n🔧 Available action handlers:")
    for handler_name in sorted(available_handlers):
        print(f"  - {handler_name}")
    
    print(f"\n✅ Verification Results:")
    
    # Check if all roadmap CCs are in config
    missing_in_config = []
    for cc, action in roadmap_ccs.items():
        if cc not in cc_mappings:
            missing_in_config.append(f"CC {cc} -> {action}")
        elif cc_mappings[cc] != action:
            print(f"  ⚠️  CC {cc}: config has '{cc_mappings[cc]}', roadmap expects '{action}'")
    
    if missing_in_config:
        print(f"  ❌ Missing in config:")
        for item in missing_in_config:
            print(f"     {item}")
    else:
        print(f"  ✅ All roadmap CCs present in config")
    
    # Check if all config actions have handlers
    missing_handlers = []
    for cc, action in cc_mappings.items():
        if action not in available_handlers:
            missing_handlers.append(f"CC {cc} -> {action}")
    
    if missing_handlers:
        print(f"  ❌ Missing action handlers:")
        for item in missing_handlers:
            print(f"     {item}")
    else:
        print(f"  ✅ All config actions have handlers")
    
    # Check for extra handlers not used in config
    config_actions = set(cc_mappings.values())
    unused_handlers = available_handlers - config_actions - {'trigger_step'}  # trigger_step is for buttons
    
    if unused_handlers:
        print(f"  ℹ️  Unused action handlers:")
        for handler_name in sorted(unused_handlers):
            print(f"     {handler_name}")
    
    # Additional CC we added
    if "26" in cc_mappings and cc_mappings["26"] == "note_probability":
        print(f"  ✅ Added CC 26 -> note_probability (not in roadmap but handler exists)")
    
    print("\n🎯 Summary:")
    roadmap_match = all(cc in cc_mappings and cc_mappings[cc] == action 
                       for cc, action in roadmap_ccs.items())
    handlers_complete = all(action in available_handlers for action in cc_mappings.values())
    
    if roadmap_match and handlers_complete:
        print("  ✅ All MIDI CC inputs are correctly routed to semantic events!")
    else:
        print("  ❌ Some issues found in CC routing")
    
    return roadmap_match and handlers_complete

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
