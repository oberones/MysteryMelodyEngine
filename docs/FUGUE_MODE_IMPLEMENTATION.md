# Fugue Mode Implementation Guide

## Overview

The Mystery Melody Machine now supports a **fugue pattern** mode that generates mini-fugues according to classical contrapuntal principles. This mode creates complex polyphonic textures with subject and answer entries, episodes, and optional stretto sections.

## What is a Fugue?

A fugue is a compositional technique where a main theme (called the "subject") is introduced by one voice and then systematically imitated by other voices at different pitch levels. The fugue mode in the Mystery Melody Machine implements:

- **Subject**: A melodically interesting theme generated based on the current scale and key
- **Answer**: The subject transposed to the dominant (perfect 5th), with optional tonal adjustments
- **Exposition**: Initial round where each voice enters with subject or answer
- **Episodes**: Developmental passages using fragments of the subject
- **Multiple Voices**: Up to 4 polyphonic voices playing simultaneously

## Configuration

### Basic Setup

Set the direction pattern to "fugue" in your `config.yaml`:

```yaml
sequencer:
  direction_pattern: fugue  # Enable fugue mode
  bpm: 120                  # Affects fugue timing
  density: 0.7              # Controls stretto overlap (higher = more overlap)
                           # NOTE: In fugue mode, density does NOT gate note generation
                           # like it does in other modes - it only affects musical features
  root_note: 60             # Key center for fugue generation
  voices: 3                 # Number of voices (1-4, where 1 = monophonic)
```

### Available Patterns

The `direction_pattern` can be set to:
- `forward` - Standard forward sequence
- `backward` - Reverse sequence  
- `ping_pong` - Bouncing back and forth
- `random` - Random step selection
- `fugue` - **NEW** - Contrapuntal fugue generation

## How Fugue Mode Works

### Subject Generation

The fugue engine automatically generates subjects based on:
- Current scale setting (`scale_index` in state)
- Root note (`root_note` in state)
- Bach-like melodic principles:
  - Clear contour with mix of steps and leaps
  - Distinctive rhythmic patterns
  - Cadential closure
  - Strategic use of rests for phrasing and expression
  - Typical length of 4 beats (1 bar in 4/4 time)

### Voice Management

- **1-4 voices** supported (configured via `voices` setting in config.yaml)
- All voices output to the same MIDI channel (as per requirements)
- When `voices: 1` - Creates flowing monophonic melodies based on the subject
- When `voices: 2-4` - Generates polyphonic fugues with alternating subject/answer entries:
  - **Voice 1**: Subject in tonic
  - **Voice 2**: Answer in dominant
  - **Voice 3**: Subject in tonic
  - **Voice 4**: Answer in dominant

### Timing and Structure

- **Exposition**: Initial entries with configurable gaps between voices
- **Episodes**: Developmental sections using subject fragments
- **Maximum Duration**: 5 minutes per fugue
- **Rest Period**: 10 seconds between fugues
- **Synchronization**: Fully synchronized to main sequencer clock

### Parameter Influence

User controls affect fugue generation:

- **Density**: Higher values create more stretto (overlapping entries)
- **BPM**: Controls overall fugue tempo
- **Scale Changes**: Apply to new fugues (quantized to bar boundaries)  
- **Root Note**: Determines the tonic center for subject generation

### Probability Control Bypass

**Important**: Fugue mode completely ignores the normal sequencer probability controls:

- **Step Probabilities**: The `step_probabilities` array has no effect in fugue mode
- **Step Pattern**: The `step_pattern` array is bypassed entirely  
- **Note Probability**: The global `note_probability` setting is ignored
- **Density Gate**: The `density` parameter does NOT gate note generation in fugue mode (it only affects fugue-specific features like stretto overlap)

This design ensures that:
- Fugue musical logic has complete control over note timing
- Classical contrapuntal principles are preserved
- No random probability filtering interferes with voice leading
- The fugue engine can generate the exact notes needed for proper counterpoint

The `density` parameter in fugue mode serves a different purpose than in standard mode - it controls musical features like stretto overlap rather than acting as a note generation gate.

## Musical Features

### Enhanced Expression with Rests

The fugue mode now includes comprehensive rest support that enhances musical expression:
- **Strategic Silences**: Rests are placed for phrasing, breathing, and dramatic effect
- **Voice Separation**: Rests help distinguish between polyphonic voices
- **Authentic Patterns**: Rest placement follows Bach-like compositional principles
- **Textural Variety**: Dynamic changes in polyphonic density through strategic silence

### Tonal vs Real Answers

By default, the system uses **tonal answers** which adjust the first tonic→dominant motion to prevent early modulation, following Bach's practice in the Well-Tempered Clavier.

### Contrapuntal Rules

The implementation includes basic counterpoint constraints:
- Avoids parallel fifths and octaves on strong beats
- Maintains reasonable voice ranges
- Prefers stepwise motion with occasional leaps
- Handles voice crossing gracefully

### Episode Generation

Episodes are created by:
- Extracting 2-beat fragments from the subject
- Sequencing through related keys (circle of fifths)
- Distributing across voices with canonic imitation
- Including strategic rests for phrasing and breathing

## Integration with Existing Systems

### MIDI Control

The fugue pattern integrates seamlessly with existing MIDI controls:
- Button presses and knob movements affect fugue parameters
- Scale selection applies to new fugues
- Pattern switching via MIDI works normally

**Note**: When switching to fugue mode, all standard probability controls are automatically bypassed. When switching back to other patterns (forward, backward, ping_pong, random), the normal probability controls resume their function.

### Mutation System

The mutation system can modify fugue parameters:
- Density changes affect stretto characteristics
- BPM changes affect fugue tempo
- Scale mutations apply to subsequent fugues

### Idle Mode

Fugue mode respects idle mode transitions:
- Switches to ambient parameters after inactivity timeout
- Supports smooth BPM transitions during idle entry/exit

## Technical Implementation

### Architecture

```
FugueEngine
├── Subject Generation (Bach-like principles)
├── Answer Generation (tonal/real)
├── Entry Planning (exposition structure)
├── Episode Creation (fragment development)
└── Counterpoint Rules (voice leading)

FugueSequencer
├── Fugue Lifecycle Management
├── Timing and Synchronization
├── Note Distribution
└── Rest Period Handling

Sequencer Integration
├── Pattern Selection
├── State Management
├── MIDI Output
└── Clock Synchronization
```

### Files Added

- `src/fugue.py` - Core fugue generation engine
- `tests/test_fugue.py` - Comprehensive test suite
- `demos/demo_fugue_mode.py` - Interactive demonstration

## Usage Examples

### Setting Fugue Pattern Programmatically

```python
from sequencer import Sequencer
from state import State

state = State()
sequencer = Sequencer(state, scales=['minor', 'major'])

# Enable fugue mode
sequencer.set_direction_pattern('fugue')

# Set parameters
state.set('density', 0.8)  # Higher stretto
state.set('root_note', 60)  # C major/minor
state.set('bpm', 120)      # Moderate tempo
```

### MIDI Control Integration

The fugue mode can be controlled via existing MIDI mappings:
- Scale selection knobs choose fugue key
- Density knobs control stretto overlap
- Tempo knobs adjust fugue speed

## Performance Characteristics

- **CPU Usage**: Moderate - fugue generation is done in batches
- **Memory**: Low - voices stored as simple note lists
- **Latency**: <10ms note generation (meets spec requirements)
- **Determinism**: Reproducible fugues via seeded random generation

## Future Enhancements

Potential extensions (not implemented yet):
- **Multi-subject fugues** (double/triple fugues)
- **Invertible counterpoint** tables
- **Style conditioning** (Bach vs. Baroque-lite)
- **User-supplied subjects** via MIDI recording
- **Advanced counterpoint** constraints via optimization

## Troubleshooting

### No Notes Generated
- Check that MIDI output is enabled
- Verify scale mapper is properly initialized
- Ensure BPM is reasonable (60-200 range)

### Fugue Too Sparse/Dense
- Adjust `density` parameter (0.3-0.9 recommended)
- Check `sequence_length` (affects voice count)

### Probability Controls Not Working
- **This is expected behavior in fugue mode**
- Fugue mode intentionally ignores step probabilities, step patterns, and note probability settings
- These controls work normally in other direction patterns (forward, backward, ping_pong, random)
- To use probability controls, switch to a non-fugue direction pattern

### Switching Patterns
- All patterns can be switched without restart
- Pattern changes take effect immediately
- Fugue state is preserved when switching away and back

## Related Documentation

- [Fugue Mode Specification](docs/reference/fugue_mode_spec.md) - Detailed technical spec
- [SPEC.md](docs/reference/SPEC.md) - Overall system architecture
- [MUTATION_IMPLEMENTATION.md](docs/MUTATION_IMPLEMENTATION.md) - Parameter mutation system
