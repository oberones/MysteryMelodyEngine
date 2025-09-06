"""Custom mutation plugin for Korg NTS-1 mkII synthesizer.

This plugin provides comprehensive mutation rules for all NTS-1 mkII parameters
including oscillators, filters, envelopes, effects, and arpeggiator settings.
Based on the official MIDI implementation document.
"""

from __future__ import annotations
import logging
from typing import List, TYPE_CHECKING
from mutation import MutationRule

if TYPE_CHECKING:
    from mutation import MutationEngine

log = logging.getLogger(__name__)


def get_nts1_mutation_rules() -> List[MutationRule]:
    """Return comprehensive mutation rules for the Korg NTS-1 mkII.
    
    These rules are carefully weighted and scaled to provide musically
    meaningful mutations while maintaining sonic coherence.
    """
    return [
        # === OSCILLATOR SECTION ===
        
        # Oscillator Type (stepped parameter - rare mutations)
        MutationRule(
            parameter="osc_type",
            weight=0.3,
            delta_range=(-1, 1),
            delta_scale=1.0,
            description="OSC type change (saw, triangle, square, noise, etc.)"
        ),
        
        # Oscillator Shape Parameters (moderate mutations)
        MutationRule(
            parameter="osc_a",
            weight=1.8,
            delta_range=(-8.0, 8.0),
            delta_scale=1.0,
            description="OSC A parameter drift"
        ),
        MutationRule(
            parameter="osc_b", 
            weight=1.8,
            delta_range=(-8.0, 8.0),
            delta_scale=1.0,
            description="OSC B parameter drift"
        ),
        
        # Oscillator LFO (subtle to dramatic effects)
        MutationRule(
            parameter="osc_lfo_rate",
            weight=1.5,
            delta_range=(-5.0, 8.0),  # Favor increasing LFO rate
            delta_scale=1.0,
            description="OSC LFO rate variation"
        ),
        MutationRule(
            parameter="osc_lfo_depth",
            weight=2.0,
            delta_range=(-6.0, 6.0),
            delta_scale=1.0,
            description="OSC LFO depth modulation"
        ),
        
        # === FILTER SECTION ===
        
        # Filter Type (stepped parameter - occasional mutations)
        MutationRule(
            parameter="filter_type",
            weight=0.5,
            delta_range=(-1, 1),
            delta_scale=1.0,
            description="Filter type change (LPF, HPF, BPF, etc.)"
        ),
        
        # Filter Cutoff (high weight - very audible)
        MutationRule(
            parameter="filter_cutoff",
            weight=3.0,
            delta_range=(-12.0, 12.0),
            delta_scale=1.0,
            description="Filter cutoff sweep"
        ),
        
        # Filter Resonance (moderate mutations for character)
        MutationRule(
            parameter="filter_resonance",
            weight=2.0,
            delta_range=(-8.0, 10.0),  # Slight bias toward adding resonance
            delta_scale=1.0,
            description="Filter resonance adjustment"
        ),
        
        # Filter Sweep (modulation effects)
        MutationRule(
            parameter="filter_sweep_depth",
            weight=1.3,
            delta_range=(-5.0, 8.0),
            delta_scale=1.0,
            description="Filter sweep depth variation"
        ),
        MutationRule(
            parameter="filter_sweep_rate",
            weight=1.3,
            delta_range=(-4.0, 6.0),
            delta_scale=1.0,
            description="Filter sweep rate change"
        ),
        
        # === ENVELOPE SECTION ===
        
        # EG Type (stepped parameter - rare changes)
        MutationRule(
            parameter="eg_type",
            weight=0.4,
            delta_range=(-1, 1),
            delta_scale=1.0,
            description="EG type change (gate, env, open, etc.)"
        ),
        
        # EG Attack (subtle to dramatic shape changes)
        MutationRule(
            parameter="eg_attack",
            weight=1.8,
            delta_range=(-6.0, 8.0),
            delta_scale=1.0,
            description="EG attack time variation"
        ),
        
        # EG Release (important for note character)
        MutationRule(
            parameter="eg_release",
            weight=2.2,
            delta_range=(-8.0, 10.0),
            delta_scale=1.0,
            description="EG release time evolution"
        ),
        
        # === TREMOLO SECTION ===
        
        # Tremolo effects (moderate impact)
        MutationRule(
            parameter="tremolo_depth",
            weight=1.2,
            delta_range=(-4.0, 6.0),
            delta_scale=1.0,
            description="Tremolo depth adjustment"
        ),
        MutationRule(
            parameter="tremolo_rate",
            weight=1.2,
            delta_range=(-5.0, 5.0),
            delta_scale=1.0,
            description="Tremolo rate variation"
        ),
        
        # === MODULATION EFFECTS ===
        
        # Mod Type (stepped parameter - occasional changes)
        MutationRule(
            parameter="mod_type",
            weight=0.6,
            delta_range=(-1, 1),
            delta_scale=1.0,
            description="Modulation effect type change"
        ),
        
        # Mod Parameters (creative sound shaping)
        MutationRule(
            parameter="mod_a",
            weight=1.7,
            delta_range=(-7.0, 7.0),
            delta_scale=1.0,
            description="Modulation effect parameter A"
        ),
        MutationRule(
            parameter="mod_b",
            weight=1.7,
            delta_range=(-7.0, 7.0),
            delta_scale=1.0,
            description="Modulation effect parameter B"
        ),
        
        # === DELAY EFFECTS ===
        
        # Delay Type (stepped parameter - moderate changes)
        MutationRule(
            parameter="delay_type",
            weight=0.8,
            delta_range=(-1, 1),
            delta_scale=1.0,
            description="Delay effect type change"
        ),
        
        # Delay Parameters (spatial effects)
        MutationRule(
            parameter="delay_a",
            weight=1.5,
            delta_range=(-6.0, 8.0),
            delta_scale=1.0,
            description="Delay parameter A adjustment"
        ),
        MutationRule(
            parameter="delay_b",
            weight=1.5,
            delta_range=(-6.0, 8.0),
            delta_scale=1.0,
            description="Delay parameter B adjustment"
        ),
        
        # Delay Mix (important for send levels)
        MutationRule(
            parameter="delay_mix",
            weight=2.0,
            delta_range=(-5.0, 8.0),  # Bias toward adding delay
            delta_scale=1.0,
            description="Delay mix level variation"
        ),
        
        # === REVERB EFFECTS ===
        
        # Reverb Type (stepped parameter - moderate changes)
        MutationRule(
            parameter="reverb_type",
            weight=0.7,
            delta_range=(-1, 1),
            delta_scale=1.0,
            description="Reverb effect type change"
        ),
        
        # Reverb Parameters (ambience control)
        MutationRule(
            parameter="reverb_a",
            weight=1.4,
            delta_range=(-5.0, 7.0),
            delta_scale=1.0,
            description="Reverb parameter A adjustment"
        ),
        MutationRule(
            parameter="reverb_b",
            weight=1.4,
            delta_range=(-5.0, 7.0),
            delta_scale=1.0,
            description="Reverb parameter B adjustment"
        ),
        
        # Reverb Mix (atmospheric control)
        MutationRule(
            parameter="reverb_mix",
            weight=2.5,
            delta_range=(-4.0, 10.0),  # Strong bias toward adding reverb
            delta_scale=1.0,
            description="Reverb mix level evolution"
        ),
        
        # === ARPEGGIATOR SECTION ===
        
        # Arp Pattern (stepped parameter - rare but impactful)
        MutationRule(
            parameter="arp_pattern",
            weight=0.4,
            delta_range=(-1, 1),
            delta_scale=1.0,
            description="Arpeggiator pattern change"
        ),
        
        # Arp Intervals (stepped parameter - moderate impact)
        MutationRule(
            parameter="arp_intervals",
            weight=0.6,
            delta_range=(-1, 1),
            delta_scale=1.0,
            description="Arpeggiator interval change"
        ),
        
        # Arp Length (continuous parameter - moderate mutations)
        MutationRule(
            parameter="arp_length",
            weight=1.0,
            delta_range=(-8.0, 8.0),
            delta_scale=1.0,
            description="Arpeggiator length variation"
        ),
        
        # === MASTER CONTROLS ===
        
        # Master Volume (gentle variations to avoid jarring changes)
        MutationRule(
            parameter="master_volume",
            weight=1.0,
            delta_range=(-3.0, 3.0),  # Small changes for safety
            delta_scale=1.0,
            description="Master volume breathing"
        ),
    ]


def get_nts1_ambient_rules() -> List[MutationRule]:
    """Return NTS-1 mutation rules optimized for ambient/atmospheric music.
    
    These rules emphasize slow, evolving changes suitable for atmospheric
    compositions and idle modes.
    """
    return [
        # Gentle filter movements
        MutationRule(
            parameter="filter_cutoff",
            weight=3.5,
            delta_range=(-8.0, 8.0),
            delta_scale=0.7,  # Gentler scaling
            description="Gentle filter cutoff drift"
        ),
        
        # Subtle resonance changes
        MutationRule(
            parameter="filter_resonance",
            weight=1.5,
            delta_range=(-4.0, 6.0),
            delta_scale=0.8,
            description="Subtle resonance evolution"
        ),
        
        # Slow envelope changes
        MutationRule(
            parameter="eg_attack",
            weight=2.0,
            delta_range=(-3.0, 8.0),  # Favor longer attacks
            delta_scale=0.8,
            description="Gentle attack time evolution"
        ),
        MutationRule(
            parameter="eg_release",
            weight=2.0,
            delta_range=(-4.0, 10.0),  # Favor longer releases
            delta_scale=0.8,
            description="Gentle release time evolution"
        ),
        
        # Atmospheric effects emphasis
        MutationRule(
            parameter="reverb_mix",
            weight=4.0,
            delta_range=(0.0, 12.0),  # Only increases for ambient
            delta_scale=1.0,
            description="Reverb depth expansion"
        ),
        MutationRule(
            parameter="delay_mix",
            weight=3.0,
            delta_range=(-2.0, 10.0),  # Bias toward adding delay
            delta_scale=1.0,
            description="Delay depth expansion"
        ),
        
        # Slow LFO movements
        MutationRule(
            parameter="osc_lfo_rate",
            weight=1.5,
            delta_range=(-8.0, 2.0),  # Favor slower rates
            delta_scale=0.6,
            description="Slow LFO rate drift"
        ),
        MutationRule(
            parameter="osc_lfo_depth",
            weight=2.0,
            delta_range=(-3.0, 8.0),  # Bias toward more modulation
            delta_scale=0.8,
            description="Gentle LFO depth variation"
        ),
        
        # Tremolo for texture
        MutationRule(
            parameter="tremolo_depth",
            weight=1.8,
            delta_range=(-2.0, 6.0),
            delta_scale=0.7,
            description="Subtle tremolo depth"
        ),
        MutationRule(
            parameter="tremolo_rate",
            weight=1.5,
            delta_range=(-6.0, 3.0),  # Favor slower tremolo
            delta_scale=0.7,
            description="Slow tremolo rate"
        ),
    ]


def get_nts1_rhythmic_rules() -> List[MutationRule]:
    """Return NTS-1 mutation rules optimized for rhythmic/percussive music.
    
    These rules emphasize quick changes and rhythmic elements suitable
    for dance, techno, and beat-oriented compositions.
    """
    return [
        # Quick filter sweeps
        MutationRule(
            parameter="filter_cutoff",
            weight=4.0,
            delta_range=(-15.0, 15.0),  # Larger changes for drama
            delta_scale=1.2,
            description="Dramatic filter cutoff sweeps"
        ),
        
        # Punchy envelopes
        MutationRule(
            parameter="eg_attack",
            weight=2.0,
            delta_range=(-8.0, 4.0),  # Favor quick attacks
            delta_scale=1.0,
            description="Punchy attack variations"
        ),
        MutationRule(
            parameter="eg_release",
            weight=2.5,
            delta_range=(-10.0, 5.0),  # Favor quick releases
            delta_scale=1.0,
            description="Rhythmic release variations"
        ),
        
        # Resonance emphasis
        MutationRule(
            parameter="filter_resonance",
            weight=3.0,
            delta_range=(-5.0, 15.0),  # Strong bias toward more resonance
            delta_scale=1.1,
            description="Resonance boost for character"
        ),
        
        # Fast LFO for movement
        MutationRule(
            parameter="osc_lfo_rate",
            weight=2.5,
            delta_range=(-2.0, 12.0),  # Favor faster rates
            delta_scale=1.0,
            description="Fast LFO rate for movement"
        ),
        
        # Distortion via oscillator
        MutationRule(
            parameter="osc_a",
            weight=2.0,
            delta_range=(-10.0, 10.0),
            delta_scale=1.2,
            description="OSC A drive for character"
        ),
        MutationRule(
            parameter="osc_b",
            weight=2.0,
            delta_range=(-10.0, 10.0),
            delta_scale=1.2,
            description="OSC B drive for character"
        ),
        
        # Moderate effects for space
        MutationRule(
            parameter="delay_mix",
            weight=1.5,
            delta_range=(-3.0, 6.0),
            delta_scale=1.0,
            description="Rhythmic delay variations"
        ),
        MutationRule(
            parameter="reverb_mix",
            weight=1.0,
            delta_range=(-4.0, 6.0),
            delta_scale=1.0,
            description="Controlled reverb for space"
        ),
    ]


def register_nts1_rules(mutation_engine: MutationEngine, style: str = "default") -> None:
    """Register NTS-1 mutation rules with the engine.
    
    Args:
        mutation_engine: The mutation engine to register rules with
        style: Rule style - 'default', 'ambient', or 'rhythmic'
    """
    if style == "ambient":
        rules = get_nts1_ambient_rules()
        log.info("Registering NTS-1 ambient mutation rules")
    elif style == "rhythmic":
        rules = get_nts1_rhythmic_rules()
        log.info("Registering NTS-1 rhythmic mutation rules")
    else:
        rules = get_nts1_mutation_rules()
        log.info("Registering NTS-1 default mutation rules")
    
    for rule in rules:
        mutation_engine.add_rule(rule)
    
    log.info(f"nts1_mutation_plugin_loaded style={style} rules_count={len(rules)}")


def register_nts1_state_parameters(state) -> None:
    """Register all NTS-1 parameters with the state system with default values.
    
    This ensures all parameters exist in the state before mutations are applied.
    """
    # Set default values for all NTS-1 parameters
    nts1_defaults = {
        # Master
        "master_volume": 100,
        
        # Oscillator
        "osc_type": 0,        # Saw wave
        "osc_a": 64,          # Center position
        "osc_b": 64,          # Center position
        "osc_lfo_rate": 32,   # Moderate rate
        "osc_lfo_depth": 16,  # Light modulation
        
        # Filter
        "filter_type": 0,        # Low-pass filter
        "filter_cutoff": 96,     # Fairly open
        "filter_resonance": 32,  # Moderate resonance
        "filter_sweep_depth": 0, # No sweep initially
        "filter_sweep_rate": 64, # Medium rate
        
        # Envelope
        "eg_type": 0,         # Gate mode
        "eg_attack": 16,      # Quick attack
        "eg_release": 64,     # Medium release
        
        # Tremolo
        "tremolo_depth": 0,   # No tremolo initially
        "tremolo_rate": 64,   # Medium rate
        
        # Modulation Effects
        "mod_type": 0,        # First mod type
        "mod_a": 64,          # Center position
        "mod_b": 64,          # Center position
        
        # Delay Effects
        "delay_type": 0,      # First delay type
        "delay_a": 64,        # Center position
        "delay_b": 64,        # Center position
        "delay_mix": 16,      # Light delay
        
        # Reverb Effects
        "reverb_type": 0,     # First reverb type
        "reverb_a": 64,       # Center position
        "reverb_b": 64,       # Center position
        "reverb_mix": 32,     # Moderate reverb
        
        # Arpeggiator
        "arp_pattern": 0,     # First pattern
        "arp_intervals": 0,   # First interval setting
        "arp_length": 64,     # Medium length
    }
    
    for param, value in nts1_defaults.items():
        # Only set if parameter doesn't already exist
        if state.get(param) is None:
            state.set(param, value, source="nts1_plugin_init")
    
    log.info(f"nts1_state_parameters_initialized count={len(nts1_defaults)}")


# Convenience function for quick setup
def setup_nts1_mutations(mutation_engine: MutationEngine, state, style: str = "default") -> None:
    """Complete setup of NTS-1 mutations including state parameters and rules.
    
    Args:
        mutation_engine: The mutation engine to configure
        state: The state system to initialize parameters in
        style: Rule style - 'default', 'ambient', or 'rhythmic'
    """
    register_nts1_state_parameters(state)
    register_nts1_rules(mutation_engine, style)
    log.info(f"nts1_mutation_setup_complete style={style}")
