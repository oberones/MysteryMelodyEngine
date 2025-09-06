# NTS-1 mkII Mutation Plugin

A comprehensive custom mutation plugin for the Korg NTS-1 mkII digital synthesizer, providing intelligent parameter evolution across all synthesis sections.

## Overview

This plugin creates mutation rules specifically tailored for the NTS-1 mkII's parameter set, based on the official MIDI implementation document. It includes all oscillator, filter, envelope, effects, and arpeggiator parameters with carefully weighted rules for musically meaningful evolution.

## Features

### Complete Parameter Coverage
- **Oscillator Section**: Type, shape parameters A/B, LFO rate/depth
- **Filter Section**: Type, cutoff, resonance, sweep depth/rate
- **Envelope Generator**: Type, attack, release 
- **Tremolo**: Depth and rate controls
- **Modulation Effects**: Type selection and parameters A/B
- **Delay Effects**: Type selection, parameters A/B, mix level
- **Reverb Effects**: Type selection, parameters A/B, mix level
- **Arpeggiator**: Pattern, intervals, length
- **Master Controls**: Volume and sustain pedal

### Corrected CC Profile
The plugin includes a corrected CC profile for the NTS-1 mkII based on the official MIDI implementation:

| Parameter | CC# | Range | Curve | Steps | Description |
|-----------|-----|-------|-------|-------|-------------|
| Master Volume | 7 | 0-127 | Linear | - | Master Volume |
| EG Attack | 16 | 0-127 | Exponential | - | EG Attack |
| EG Release | 19 | 0-127 | Exponential | - | EG Release |
| Filter Cutoff | 43 | 0-127 | Exponential | - | Filter Cutoff |
| Filter Resonance | 44 | 0-127 | Linear | - | Filter Resonance |
| OSC A | 54 | 0-127 | Linear | - | OSC A |
| OSC B | 55 | 0-127 | Linear | - | OSC B |
| Reverb Mix | 36 | 0-127 | Linear | - | REVERB MIX |
| Delay Mix | 33 | 0-127 | Linear | - | DELAY MIX |

### Three Mutation Styles

**Default Style**: Balanced mutations across all parameters
- 30 mutation rules covering all synthesis sections
- Moderate weights and delta ranges for musical evolution
- Suitable for general-purpose generative music

**Ambient Style**: Gentle, atmospheric mutations
- 10 focused rules emphasizing slow evolution
- Reduced delta scales for subtle changes
- Bias toward reverb and delay increases
- Longer attack/release times preferred

**Rhythmic Style**: Dynamic, beat-oriented mutations  
- 9 rules emphasizing dramatic filter sweeps
- Higher weights on filter cutoff and resonance
- Quick attack/release preferences
- Moderate effects for space without muddiness

## Usage

### Basic Setup

```python
from nts1_mutation_plugin import setup_nts1_mutations

# Complete setup with default style
setup_nts1_mutations(mutation_engine, state, "default")
```

### Advanced Setup

```python
from nts1_mutation_plugin import (
    register_nts1_state_parameters,
    register_nts1_rules
)

# Manual setup with custom configuration
register_nts1_state_parameters(state)
register_nts1_rules(mutation_engine, "ambient")
```

### Configuration

Add to your `config.yaml`:

```yaml
midi:
  cc_profile:
    active_profile: "korg_nts1_mk2"  # Use corrected NTS-1 profile

mutation:
  interval_min_s: 45        # Longer intervals for musical coherence
  interval_max_s: 90
  max_changes_per_cycle: 4  # More changes for rich parameter set
  
  nts1_plugin:
    enabled: true
    style: "ambient"        # Options: "default", "ambient", "rhythmic"
    replace_default_rules: true
```

### Hardware Mapping

Map your hardware controls to NTS-1 parameters:

```yaml
mapping:
  ccs:
    # Hardware knobs -> NTS-1 parameters
    "21": filter_cutoff      # K1 -> Filter Cutoff (CC 43)
    "22": filter_resonance   # K2 -> Filter Resonance (CC 44)
    "23": eg_attack          # K3 -> EG Attack (CC 16)
    "24": eg_release         # K4 -> EG Release (CC 19)
    "25": reverb_mix         # K5 -> Reverb Mix (CC 36)
    "26": delay_mix          # K6 -> Delay Mix (CC 33)
    
    # Switches for stepped parameters
    "60": osc_type           # S1 -> OSC Type (CC 53)
    "61": filter_type        # S2 -> Filter Type (CC 42)
    "62": mod_type           # S3 -> MOD Type (CC 88)
```

## Files

- `src/nts1_mutation_plugin.py` - Main plugin implementation
- `src/nts1_integration.py` - Integration helpers for main application  
- `demos/demo_nts1_mutation.py` - Comprehensive demonstration script
- `tests/test_nts1_mutation_plugin.py` - Plugin test suite
- `config.nts1.example.yaml` - Example configuration file

## Integration with Main Application

For main application integration, see `src/nts1_integration.py`:

```python
from nts1_integration import (
    integrate_nts1_plugin,
    setup_nts1_idle_mode,
    validate_nts1_cc_profile
)

# In your main.py
if integrate_nts1_plugin(mutation_engine, state, config_data):
    log.info("NTS-1 plugin integration successful")

setup_nts1_idle_mode(idle_manager, state, config_data)
validate_nts1_cc_profile(config_data)
```

## Testing

Run the test suite:

```bash
cd /path/to/rpi-engine
source .venv/bin/activate
python -m pytest tests/test_nts1_mutation_plugin.py -v
```

Run the demo:

```bash
cd /path/to/rpi-engine  
source .venv/bin/activate
python demos/demo_nts1_mutation.py
```

## Musical Considerations

### Parameter Weighting
- **High Impact Parameters** (weight 3.0+): filter_cutoff, density, reverb_mix
- **Medium Impact Parameters** (weight 1.5-2.5): eg_attack, eg_release, osc_lfo_depth
- **Low Impact Parameters** (weight 0.3-1.0): type selectors, arp_pattern

### Delta Ranges
- **Large Deltas**: filter_cutoff (±12), reverb_mix (±10)
- **Medium Deltas**: osc_a/b (±8), eg_attack/release (±8)  
- **Small Deltas**: swing (±0.05), tremolo (±6)

### Stepped Parameters
Type selectors use stepped curves with appropriate step counts:
- OSC Type: 7 steps (saw, triangle, square, etc.)
- Filter Type: 7 steps (LPF, HPF, BPF, etc.) 
- Effect Types: 9-13 steps depending on effect

## Troubleshooting

**Plugin Not Loading**: Verify `nts1_plugin.enabled: true` in config

**Parameters Not Changing**: Check that mutations are enabled and idle mode is active

**Wrong CC Values**: Ensure `active_profile: "korg_nts1_mk2"` in config

**Harsh Sound Changes**: Use "ambient" style or reduce `max_changes_per_cycle`

## Advanced Customization

Create custom rule variants:

```python
from nts1_mutation_plugin import get_nts1_mutation_rules
from mutation import MutationRule

# Get base rules and modify
rules = get_nts1_mutation_rules()

# Add custom rule
custom_rule = MutationRule(
    parameter="filter_cutoff",
    weight=5.0,  # Very high priority
    delta_range=(-20.0, 20.0),  # Dramatic changes
    description="Extreme filter sweeps"
)

mutation_engine.add_rule(custom_rule)
```

## License

Part of the Mystery Music Station project. See main project LICENSE file.
