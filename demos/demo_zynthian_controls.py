#!/usr/bin/env python3
"""
Demo script for the new Zynthian controls.

This demonstrates the new control scheme for Zynthian v4 hardware:
- Encoder 0: Sequencer steps (1-32) with apply via button
- Encoder 1: Scale selection with apply via button
- Encoder 2: Root note selection (C-B) with apply via button
- Encoder 3: Direction pattern selection with apply via button
- Buttons S1-S4: Direct CC profile selection

Run this script to see a demonstration of the control workflow.
"""

import sys
import os
import time

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def demo_zynthian_controls():
    """Demonstrate the new Zynthian control workflow"""
    
    print("🎹 Mystery Melody Machine - Zynthian v4 Controls Demo")
    print("=" * 60)
    print()
    
    print("NEW CONTROL SCHEME:")
    print()
    
    print("📟 ENCODERS (rotate to browse, press to apply):")
    print("  Encoder 0 (Layer):  Sequencer Steps (1-32)")
    print("  Encoder 1 (Back):   Scale Selection")
    print("  Encoder 2 (Select): Root Note (C-B)")
    print("  Encoder 3 (Learn):  Direction Pattern")
    print()
    
    print("🔘 BUTTONS (instant CC profile selection):")
    print("  S1: Korg NTS-1 MK2")
    print("  S2: Roland JX-08")
    print("  S3: Waldorf Streichfett")
    print("  S4: Generic Analog")
    print()
    
    print("🎵 WORKFLOW EXAMPLES:")
    print("-" * 40)
    
    # Example 1: Changing sequence length
    print()
    print("1️⃣  Changing Sequence Length:")
    print("   • Rotate Encoder 0 clockwise → Steps: 4 → 5 → 6 → 7 → 8")
    print("   • See current selection on display (future)")
    print("   • Press Encoder 0 button → Apply 8 steps to sequencer")
    print("   • Sequencer immediately switches to 8-step pattern")
    
    # Example 2: Switching scales
    print()
    print("2️⃣  Switching Musical Scales:")
    print("   • Rotate Encoder 1 → Scale: major → minor → pentatonic_major")
    print("   • Hear preview notes at current tempo (future)")
    print("   • Press Encoder 1 button → Apply pentatonic_major")
    print("   • All future notes use new scale, quantized to bar boundary")
    
    # Example 3: Changing root note
    print()
    print("3️⃣  Transposing Root Note:")
    print("   • Rotate Encoder 2 → Root: C → C# → D → D# → E")
    print("   • See note name on display")
    print("   • Press Encoder 2 button → Apply E as new root")
    print("   • Entire sequence transposes to E major/minor/etc.")
    
    # Example 4: Direction patterns
    print()
    print("4️⃣  Changing Sequence Direction:")
    print("   • Rotate Encoder 3 → Direction: forward → backward → ping_pong")
    print("   • Press Encoder 3 button → Apply ping_pong pattern")
    print("   • Sequence plays forward then backward repeatedly")
    
    # Example 5: CC Profile switching
    print()
    print("5️⃣  Switching Synthesizers:")
    print("   • Press S1 → Instantly switch to NTS-1 MK2 CC mappings")
    print("   • All knobs/joystick now control NTS-1 parameters")
    print("   • Press S2 → Switch to Roland JX-08 parameters")
    print("   • Press S3 → Switch to Streichfett parameters")
    print("   • Press S4 → Switch to generic analog parameters")
    
    print()
    print("✨ ADVANTAGES:")
    print("-" * 40)
    print("• 🎯 Direct hardware control without external MIDI controller")
    print("• 🔄 Browse-then-apply workflow prevents accidental changes")
    print("• ⚡ Instant CC profile switching for multi-synth setups")
    print("• 🎵 Musical parameters (scales, root notes) easily accessible")
    print("• 🔢 Sequence length adjustable in real-time (1-32 steps)")
    print("• 🎼 Direction patterns add rhythmic variety")
    print()
    
    print("🚀 PERFORMANCE USE:")
    print("-" * 40)
    print("• Rotate encoders to browse options while music plays")
    print("• Press encoder buttons to apply changes at musical moments")
    print("• Use S1-S4 buttons for instant synth switching")
    print("• All changes are tempo-synced and musically quantized")
    print()
    
    print("📝 CONFIGURATION:")
    print("-" * 40)
    print("• Copy examples/config.zynthian.example.yaml → config.yaml")
    print("• Set zynthian.enabled: true")
    print("• Connect Zynthian MIDI DIN to your synthesizers")
    print("• Run with: python src/main.py --config config.yaml")
    
    print()
    print("🎹 Ready to create evolving generative music with tactile control!")

if __name__ == "__main__":
    demo_zynthian_controls()
