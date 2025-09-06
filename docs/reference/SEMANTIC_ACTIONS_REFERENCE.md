# Semantic Actions Reference

## Overview

This document provides a comprehensive list of semantic actions that can be mapped to physical hardware controls in the Mystery Melody Machine. Actions are categorized by the type of control they're best suited for: switch buttons (discrete/toggle actions) or potentiometers (continuous control).

---

## Actions for Switch Buttons (Discrete/Toggle Controls)

### Sequencer & Pattern Control

| Action | Description |
|--------|-------------|
| `chaos_lock` | Lock/unlock mutation system |
| `step_trigger` | Manual step advance/note trigger |
| `pattern_preset_toggle` | Cycle through step pattern presets (four_on_floor, offbeat, syncopated, etc.) |
| `direction_toggle` | Cycle through direction patterns (forward, backward, ping_pong, random) |
| `scale_lock` | Lock current scale (prevent mutations) |
| `quantize_mode_toggle` | Toggle between bar-quantized and immediate scale changes |
| `sequence_reset` | Reset to step 0 |
| `mute_toggle` | Mute/unmute sequencer output |

### Musical Scale & Mode

| Action | Description |
|--------|-------------|
| `scale_up` | Increment scale index (9 available: major, minor, pentatonic_major, pentatonic_minor, dorian, locrian, mixolydian, blues, chromatic) |
| `scale_down` | Decrement scale index |
| `root_note_up` | Transpose root note up (semitone or octave) |
| `root_note_down` | Transpose root note down |
| `octave_up` | Shift all notes up one octave |
| `octave_down` | Shift all notes down one octave |

### NTS-1 Synthesis Control (Discrete Parameters)

| Action | Description | NTS-1 CC Values |
|--------|-------------|-----------------|
| `osc_type_toggle` | Cycle through oscillator types | 7 types: 0,18,36,54,72,90,127 |
| `filter_type_toggle` | Cycle through filter types | 7 types: LPF, HPF, BPF, etc. |
| `mod_type_toggle` | Cycle through modulation effect types | 9 types: chorus, flanger, phaser, etc. |
| `delay_type_toggle` | Cycle through delay types | 13 types: stereo, mono, ping-pong, etc. |
| `reverb_type_toggle` | Cycle through reverb types | 11 types: hall, room, plate, etc. |
| `eg_type_toggle` | Cycle through envelope generator types | 5 types |

### System & Meta Control

| Action | Description |
|--------|-------------|
| `idle_mode_toggle` | Force enter/exit idle mode |
| `mutation_enable_toggle` | Enable/disable mutation system |
| `cc_profile_toggle` | Switch between external synth CC profiles (korg_nts1_mk2, generic_analog, fm_synth, waldorf_streichfett) |
| `portal_program_cycle` | Cycle through portal animation programs (spiral, pulse, wave, chaos, ambient, idle) |

### Arpeggiator Control (NTS-1 specific)

| Action | Description | NTS-1 CC |
|--------|-------------|----------|
| `arp_pattern_toggle` | Cycle through arpeggiator patterns | 10 patterns (CC 117) |
| `arp_intervals_toggle` | Cycle through arpeggiator interval settings | 6 settings (CC 118) |
| `sustain_pedal_toggle` | MIDI sustain pedal on/off | CC 64 |

---

## Actions for Potentiometers (Continuous Control)

### Timing & Rhythm Parameters

| Action | Description | Range | Curve |
|--------|-------------|-------|-------|
| `tempo` | BPM control | 60-200 BPM | Linear |
| `swing` | Swing amount | 0.0-0.5 | Logarithmic |
| `density` | Overall note probability gate | 0.0-1.0 | Linear |
| `note_probability` | Base probability for active steps | 0.0-1.0 | Linear |
| `gate_length` | Note duration factor | 0.1-1.0 | Linear |
| `drift` | BPM modulation envelope | -0.2 to +0.2 | Linear |

### Sequence Control

| Action | Description | Range | Curve |
|--------|-------------|-------|-------|
| `sequence_length` | Number of steps | 1-32 | Stepped |
| `base_velocity` | Base MIDI velocity | 1-127 | Linear |
| `velocity_range` | Velocity variation range | 0-127 | Linear |
| `step_probability_spread` | Adjust probability variation across steps | 0.0-1.0 | Linear |

### NTS-1 Synthesis Parameters (Continuous)

| Action | Description | NTS-1 CC | Curve |
|--------|-------------|----------|-------|
| `master_volume` | Master output level | CC 7 | Linear |
| `filter_cutoff` | Filter cutoff frequency | CC 43 | Exponential |
| `filter_resonance` | Filter resonance/Q | CC 44 | Linear |
| `filter_sweep_depth` | Filter LFO depth | CC 45 | Linear |
| `filter_sweep_rate` | Filter LFO rate | CC 46 | Logarithmic |
| `eg_attack` | Envelope attack time | CC 16 | Exponential |
| `eg_release` | Envelope release time | CC 19 | Exponential |
| `osc_a` | Oscillator parameter A | CC 54 | Linear |
| `osc_b` | Oscillator parameter B | CC 55 | Linear |
| `osc_lfo_rate` | Oscillator LFO rate | CC 24 | Logarithmic |
| `osc_lfo_depth` | Oscillator LFO depth | CC 26 | Linear |
| `tremolo_depth` | Tremolo effect depth | CC 20 | Linear |
| `tremolo_rate` | Tremolo effect rate | CC 21 | Logarithmic |

### Effects Parameters (NTS-1)

| Action | Description | NTS-1 CC | Curve |
|--------|-------------|----------|-------|
| `mod_a` | Modulation effect parameter A | CC 28 | Linear |
| `mod_b` | Modulation effect parameter B | CC 29 | Linear |
| `delay_a` | Delay effect parameter A | CC 30 | Linear |
| `delay_b` | Delay effect parameter B | CC 31 | Linear |
| `delay_mix` | Delay effect mix level | CC 33 | Linear |
| `reverb_a` | Reverb effect parameter A | CC 34 | Linear |
| `reverb_b` | Reverb effect parameter B | CC 35 | Linear |
| `reverb_mix` | Reverb effect mix level | CC 36 | Linear |
| `arp_length` | Arpeggiator length | CC 119 | Linear |

### Mutation System Parameters

| Action | Description | Range | Curve |
|--------|-------------|-------|-------|
| `mutation_rate_factor` | Scale mutation interval timing | 0.5-2.0x base rate | Linear |
| `mutation_intensity` | Scale mutation delta ranges | 0.1-2.0x base deltas | Linear |

### Portal Animation Control

| Action | Description | Range | Curve |
|--------|-------------|-------|-------|
| `portal_intensity` | Visual intensity/brightness | 0.0-1.0 | Linear |
| `portal_rate` | Animation speed multiplier | 0.1-3.0 | Logarithmic |
| `portal_color_shift` | Hue rotation for color effects | 0-360° | Linear |

### Alternative Synth Profile Parameters

These parameters map to different CCs based on the active CC profile:

#### Generic Analog Synth Profile

| Action | Description | CC | Curve |
|--------|-------------|----|----|
| `analog_filter_cutoff` | Analog filter cutoff | CC 74 | Exponential |
| `analog_filter_resonance` | Analog filter resonance | CC 71 | Linear |
| `analog_envelope_attack` | Analog envelope attack | CC 73 | Exponential |
| `analog_envelope_decay` | Analog envelope decay | CC 75 | Exponential |
| `analog_envelope_sustain` | Analog envelope sustain | CC 70 | Linear |
| `analog_envelope_release` | Analog envelope release | CC 72 | Exponential |
| `analog_lfo_rate` | Analog LFO rate | CC 76 | Logarithmic |
| `analog_lfo_amount` | Analog LFO amount | CC 77 | Linear |
| `analog_osc_detune` | Analog oscillator detune | CC 78 | Linear |
| `analog_pulse_width` | Analog pulse width | CC 79 | Linear |

#### FM Synth Profile

| Action | Description | CC | Curve |
|--------|-------------|----|----|
| `fm_op1_ratio` | FM operator 1 ratio | CC 20 | Stepped (32 steps) |
| `fm_op1_level` | FM operator 1 level | CC 21 | Linear |
| `fm_op1_attack` | FM operator 1 attack | CC 22 | Exponential |
| `fm_op1_decay` | FM operator 1 decay | CC 23 | Exponential |
| `fm_op2_ratio` | FM operator 2 ratio | CC 24 | Stepped (32 steps) |
| `fm_op2_level` | FM operator 2 level | CC 25 | Linear |
| `fm_op2_attack` | FM operator 2 attack | CC 26 | Exponential |
| `fm_op2_decay` | FM operator 2 decay | CC 27 | Exponential |
| `fm_mod_index` | FM modulation index | CC 28 | Exponential |
| `fm_feedback` | FM feedback | CC 29 | Linear |

#### Waldorf Streichfett Profile

| Action | Description | CC | Curve |
|--------|-------------|----|----|
| `string_octaves` | String section octaves | CC 71 | Linear |
| `string_release` | String section release | CC 72 | Exponential |
| `string_crescendo` | String section crescendo | CC 73 | Linear |
| `string_ensemble` | String ensemble effect | CC 74 | Linear |
| `solo_tone` | Solo section tone | CC 76 | Linear |
| `solo_tremolo` | Solo section tremolo | CC 77 | Linear |
| `solo_attack` | Solo section attack | CC 80 | Exponential |
| `solo_decay` | Solo section decay | CC 81 | Exponential |
| `balance` | String/Solo balance | CC 82 | Linear |
| `fx_animate_amount` | Animate effect amount | CC 92 | Linear |
| `fx_phaser_amount` | Phaser effect amount | CC 93 | Linear |
| `fx_reverb_amount` | Reverb effect amount | CC 94 | Linear |

---

## Summary

- **Switch-appropriate actions**: 20+ discrete controls for pattern selection, scale changes, effect type cycling, and system toggles
- **Potentiometer-appropriate actions**: 40+ continuous controls for synthesis parameters, timing, effects, and system modulation

The system supports multiple CC profiles allowing the same physical controls to map to different synthesizer parameters based on the connected external hardware. All parameters include appropriate scaling curves (linear, exponential, logarithmic, stepped) optimized for musical control.

---

*Generated from codebase analysis on August 31, 2025*
