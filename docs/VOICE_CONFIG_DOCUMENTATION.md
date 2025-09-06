# Voice Configuration for Fugue Mode

## Overview

The fugue mode now supports configurable voice count, allowing users to choose between monophonic melody generation and polyphonic fugue generation. This addresses the need for both simple single-voice melodies and complex multi-voice counterpoint.

## Configuration

### Config File Setting

Add the `voices` parameter to your `config.yaml`:

```yaml
sequencer:
  direction_pattern: fugue
  voices: 3              # Number of voices for fugue mode (1-4)
```

### Valid Voice Counts

- **`voices: 1`** - Monophonic melody mode
  - Generates single-voice melodic lines
  - Perfect for bass lines, lead melodies, or simple melodic content
  - Never produces polyphonic output

- **`voices: 2`** - Two-voice polyphony
  - Simple counterpoint between two voices
  - Good for duets or call-and-response patterns
  - Moderate computational complexity

- **`voices: 3`** - Three-voice polyphony (default)
  - Traditional fugue texture
  - Rich harmonic content with manageable complexity
  - Recommended for most polyphonic applications

- **`voices: 4`** - Four-voice polyphony
  - Complex Baroque-style fugues
  - Maximum polyphonic richness
  - Higher computational complexity

## Musical Behavior

### Single Voice Mode (`voices: 1`)

When set to single voice mode, the fugue engine creates:
- A flowing monophonic melody based on the generated subject
- Variations and transpositions of the subject material
- Connecting passages between melodic phrases
- A natural cadential conclusion
- Strategic rests for musical phrasing

**Example use cases:**
- Bass lines for other instruments
- Lead melody lines
- Simple melodic content when polyphony isn't desired
- Testing melodic material before adding harmony

### Multi-Voice Mode (`voices: 2-4`)

When set to multi-voice mode, the fugue engine creates:
- Proper fugue exposition with staggered voice entries
- Subject and answer alternation between voices
- Polyphonic episodes with canonic imitation
- Stretto sections with overlapping entries
- Complex contrapuntal development

**Example use cases:**
- Traditional fugue generation
- Rich harmonic textures
- Sophisticated musical AI demonstrations
- Polyphonic backing tracks

## Implementation Details

### Polyphony Handling

The sequencer now properly handles multiple simultaneous notes:
- `get_next_step_notes()` returns a list of notes (instead of a single note)
- Each note in the list is processed through the callback system
- Multiple MIDI notes can be triggered simultaneously
- Voice timing is independently tracked per voice

### Configuration Validation

The voice count is automatically clamped to valid ranges:
- Minimum: 1 voice (monophonic)
- Maximum: 4 voices (practical limit for fugue complexity)
- Invalid values are corrected automatically

### Backward Compatibility

- Existing configurations without the `voices` parameter default to 3 voices
- All other sequencer modes (forward, backward, ping_pong, random) are unaffected
- The change is purely additive and doesn't break existing functionality

## Testing

The voice configuration system has been thoroughly tested:

```bash
# Test voice configuration functionality
python test_voice_config.py

# Test single voice mode specifically  
python test_single_voice_config.py

# Comprehensive demonstration
python test_voice_comprehensive.py

# Original polyphony test still works
python test_fugue_polyphony.py
```

## Usage Examples

### For Simple Melodies
```yaml
sequencer:
  direction_pattern: fugue
  voices: 1
  bpm: 110
```

### For Traditional Fugues
```yaml
sequencer:
  direction_pattern: fugue
  voices: 3
  bpm: 120
```

### For Complex Polyphony
```yaml
sequencer:
  direction_pattern: fugue
  voices: 4
  bpm: 100
  density: 0.7  # Slightly lower density for complex textures
```

## Benefits

1. **Flexibility**: Choose appropriate complexity for your musical context
2. **Performance**: Single voice mode uses fewer resources
3. **Musical Appropriateness**: Match voice count to musical style
4. **Easy Configuration**: Simple YAML parameter change
5. **Polyphonic Accuracy**: Proper simultaneous note handling

This enhancement makes the fugue mode suitable for a much wider range of musical applications, from simple melodic generation to complex polyphonic composition.
