# NTS-1 Plugin Default Integration - Implementation Summary

## What Was Implemented

The NTS-1 mutation plugin is now **automatically loaded by default** when the system detects that the KORG NTS-1 mkII CC profile is active.

## Changes Made

### 1. Main Application Integration (`src/main.py`)
- Added automatic detection of `korg_nts1_mk2` CC profile
- Auto-loads NTS-1 plugin when detected
- Replaces default mutation rules with NTS-1-specific rules
- Loads configuration options from `config.yaml`

### 2. Default Configuration (`config.yaml`)
- **CC Profile**: Changed from `waldorf_streichfett` to `korg_nts1_mk2`
- **Hardware Mapping**: Updated to map knobs/controls to NTS-1 parameters:
  - K1-K6: filter_cutoff, filter_resonance, eg_attack, eg_release, reverb_mix, delay_mix
  - Joystick: osc_a, osc_b, mod_a, mod_b
  - Switches: osc_type, filter_type, mod_type
- **Plugin Config**: Added `nts1_plugin` section with default settings

### 3. CC Profile Loading
- Added `load_custom_profiles()` call to ensure all profiles are available
- NTS-1 profile with 31 parameters is loaded and ready

## How It Works

1. **Automatic Detection**: When `main.py` starts, it checks the active CC profile
2. **Conditional Loading**: If profile is `korg_nts1_mk2`, the NTS-1 plugin is automatically imported and loaded
3. **Rule Replacement**: Default mutation rules are cleared and replaced with 30 NTS-1-specific rules
4. **Parameter Initialization**: All NTS-1 parameters are registered in the state system with appropriate defaults

## Configuration Options

```yaml
midi:
  cc_profile:
    active_profile: "korg_nts1_mk2"  # Triggers auto-loading

mutation:
  nts1_plugin:
    style: "default"              # Options: "default", "ambient", "rhythmic"  
    replace_default_rules: true   # Replace built-in rules with NTS-1 ones
```

## Hardware Mapping (Default)

| Control | Parameter | NTS-1 CC | Description |
|---------|-----------|----------|-------------|
| K1 | filter_cutoff | 43 | Filter Cutoff |
| K2 | filter_resonance | 44 | Filter Resonance |
| K3 | eg_attack | 16 | EG Attack |
| K4 | eg_release | 19 | EG Release |
| K5 | reverb_mix | 36 | Reverb Mix |
| K6 | delay_mix | 33 | Delay Mix |
| Joy Up | osc_a | 54 | OSC A |
| Joy Down | osc_b | 55 | OSC B |
| Joy Left | mod_a | 28 | MOD A |
| Joy Right | mod_b | 29 | MOD B |
| S1 | osc_type | 53 | OSC Type |
| S2 | filter_type | 42 | Filter Type |
| S3 | mod_type | 88 | MOD Type |

## Testing Verification

✅ **Integration Test Passed**
- NTS-1 CC profile loaded (31 parameters)
- Default rules cleared (9 → 0)
- NTS-1 rules loaded (30 rules)
- System starts successfully with MIDI I/O

✅ **Startup Log Verification**
```
cc_profile_active=korg_nts1_mk2
Cleared default mutation rules for NTS-1 plugin
nts1_state_parameters_initialized count=30
nts1_mutation_plugin_loaded style=default rules_count=30
NTS-1 mutation plugin auto-loaded (style=default, replace_default=True)
```

## For Users

**No manual setup required!** The NTS-1 plugin now works out of the box:

1. Start the application: `python src/main.py`
2. The system automatically detects the NTS-1 profile
3. 30 comprehensive mutation rules are loaded for all NTS-1 parameters
4. Hardware controls are mapped to key NTS-1 synthesis parameters
5. Intelligent mutations begin affecting filter, envelope, effects, etc.

## Switching Styles

To use different mutation styles, edit `config.yaml`:

```yaml
mutation:
  nts1_plugin:
    style: "ambient"    # For gentle, atmospheric mutations
    # or
    style: "rhythmic"   # For dynamic, beat-oriented mutations
```

The plugin provides the richest, most comprehensive mutation experience for the NTS-1 mkII synthesizer available in the Mystery Music Station ecosystem.
