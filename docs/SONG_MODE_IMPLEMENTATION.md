# Song Mode Implementation Guide

## Overview

The Mystery Melody Machine now supports a **song mode** that generates complete structured compositions using common song patterns found in popular music. This mode creates multi-section compositions with varying dynamics, density, and musical character that follow traditional songwriting forms.

## What is Song Mode?

Song mode is a compositional pattern that generates complete musical pieces with defined sections like intro, verse, chorus, bridge, and outro. Unlike other sequencer modes that generate continuous patterns, song mode:

- **Creates structured compositions** with distinct sections (intro, verse, chorus, bridge, outro)
- **Manages timing automatically** with sections lasting specific numbers of bars
- **Varies musical parameters** like density, tempo, and dynamics between sections
- **Supports multiple song patterns** including verse-chorus, AABA, 12-bar blues, and more
- **Includes between-song pauses** with automatic new song generation after 5 seconds
- **Uses polyphonic voices** for harmonic richness (configurable 1-4 voices)

---

## Configuration

### Basic Setup

Set the direction pattern to "song" in your `config.yaml`:

```yaml
sequencer:
  direction_pattern: song  # Enable song mode
  bpm: 120                 # Base tempo for compositions
  density: 0.8             # Base density (sections will modify this)
  root_note: 60            # Key center for song generation
  voices: 3                # Number of voices (1-4)
```

### Available Patterns

The `direction_pattern` can be set to:
- `forward` - Standard forward sequence
- `backward` - Reverse sequence  
- `ping_pong` - Bouncing back and forth
- `random` - Random step selection
- `fugue` - Contrapuntal fugue generation
- `song` - **NEW** - Structured song composition

---

## How Song Mode Works

### Song Pattern Selection

When song mode starts, it randomly selects from several predefined song patterns:

1. **Verse-Chorus** - Classic popular music form
2. **AABA (32-Bar Form)** - Traditional jazz and Tin Pan Alley format
3. **Verse-Chorus-Bridge** - Extended pop form with bridge section
4. **12-Bar Blues** - Traditional blues structure with solos
5. **Pop Standard** - Modern pop format with repeated choruses
6. **Minimalist** - Sparse, ambient composition with gradual development

### Section Types and Characteristics

Each song pattern consists of sections with specific musical characteristics:

#### Intro
- **Purpose**: Set the mood and establish key/tempo
- **Typical density**: 0.5-0.6 (moderate activity)
- **Velocity**: Slightly reduced for atmospheric entry
- **Duration**: 4-8 bars

#### Verse
- **Purpose**: Present main melodic content and narrative
- **Typical density**: 0.7-0.8 (moderate-high activity)
- **Characteristics**: Establishes harmonic foundation
- **Duration**: 8-16 bars

#### Chorus
- **Purpose**: Climactic, memorable section with highest energy
- **Typical density**: 0.9-1.0 (high activity)
- **Velocity**: Increased for emphasis and power
- **Duration**: 12-16 bars

#### Bridge
- **Purpose**: Contrasting section with different character
- **Typical density**: 0.8-0.9 (high activity)
- **Octave shift**: Often raised for contrast
- **Tempo**: Sometimes modified for dramatic effect
- **Duration**: 8-12 bars

#### Instrumental
- **Purpose**: Solo or featured instrumental section
- **Typical density**: 0.9 (high activity for virtuosic display)
- **Characteristics**: Showcases melodic development
- **Duration**: 12-16 bars

#### Outro
- **Purpose**: Graceful conclusion and resolution
- **Typical density**: 0.4-0.5 (reduced activity)
- **Velocity**: Reduced for fade-out effect
- **Duration**: 4-8 bars

### Voice Management

Song mode supports 1-4 voices for harmonic richness:

- **Voice 1**: Primary melody line (loudest)
- **Voice 2**: Harmonic support (slightly quieter)
- **Voice 3**: Bass or counter-melody (higher octave)
- **Voice 4**: Additional harmony (lower octave)

Each voice follows different scale degree patterns to create harmonic interest while maintaining musical coherence.

### Timing and Structure

- **Bar-based timing**: All sections are measured in musical bars (4 beats each)
- **Automatic progression**: Sections advance automatically based on timing
- **Tempo variations**: Sections can modify the base tempo (e.g., slower bridge)
- **Dynamic changes**: Density and velocity vary by section type
- **5-second pause**: Between complete songs for breathing space

---

## Musical Features

### Structured Composition

Song mode creates complete musical works with:
- **Clear formal structure** following established songwriting patterns
- **Dynamic contrast** between sections (quiet verses, loud choruses)
- **Harmonic progression** using multiple voices
- **Rhythmic variety** through density and pattern changes

### Voice Leading and Harmony

- **Smooth voice leading** with preference for stepwise motion
- **Harmonic intervals** created by different voice patterns
- **Octave distribution** spreads voices across frequency spectrum
- **Chord progressions** implied through scale degree patterns

### Parameter Automation

Song mode automatically manages:
- **Tempo changes** for dramatic effect (bridges, outros)
- **Density variations** to create section contrast
- **Velocity dynamics** for musical expression
- **Octave shifts** for textural variety

---

## Technical Implementation

### Architecture

```
SongSequencer
├── Pattern Management (verse-chorus, AABA, etc.)
├── Section Timing (bar-based progression)
├── Voice Coordination (polyphonic patterns)
└── Parameter Automation (tempo, density, dynamics)

Sequencer Integration
├── Pattern Selection (song mode activation)
├── State Management (section parameters)
├── Note Generation (multi-voice coordination)
└── Clock Synchronization (bar-based timing)
```

### Song Pattern Definitions

Song patterns are defined in `src/song.py` with the following structure:

```python
SongPattern(
    name="Pattern Name",
    sections=[
        SongSection(
            section_type=SectionType.INTRO,
            bars=8,
            density=0.6,
            tempo_factor=1.0,
            octave_shift=0,
            velocity_factor=0.8
        ),
        # ... more sections
    ],
    estimated_duration_minutes=3.0
)
```

### Files Added

- `src/song.py` - Core song pattern engine and sequencer
- `tests/test_song_mode.py` - Comprehensive test suite
- `demos/demo_song_mode.py` - Interactive demonstration
- `docs/SONG_MODE_IMPLEMENTATION.md` - This documentation

---

## Usage Examples

### Setting Song Pattern Programmatically

```python
from sequencer import Sequencer
from state import State

state = State()
sequencer = Sequencer(state, scales=['minor', 'major'])

# Enable song mode
sequencer.set_direction_pattern('song')

# Set parameters
state.set('voices', 3)     # 3-voice harmony
state.set('root_note', 60) # C major/minor
state.set('bpm', 120)      # Moderate tempo
```

### MIDI Control Integration

Song mode can be controlled via existing MIDI mappings:
- Scale selection knobs choose song key
- Tempo knobs adjust base song speed  
- Voice count affects harmonic complexity
- Density knobs set base activity level

## Performance Characteristics

- **CPU Usage**: Moderate - song generation uses batch processing
- **Memory**: Low - patterns stored as simple parameter lists
- **Latency**: <10ms note generation (meets spec requirements)
- **Duration**: 1-4 minutes per song with automatic progression

## Available Song Patterns

### Verse-Chorus (2.5 minutes)
Classic pop structure: Intro → Verse → Chorus → Verse → Chorus → Outro

### AABA (1.8 minutes) 
Traditional 32-bar form: Intro → A → A → B → A → Outro

### Verse-Chorus-Bridge (3.2 minutes)
Extended pop form: Intro → Verse → Chorus → Verse → Chorus → Bridge → Chorus → Outro

### 12-Bar Blues (2.1 minutes)
Blues structure: Intro → Blues → Blues → Solo → Blues → Outro

### Pop Standard (3.5 minutes)
Modern pop: Intro → Verse → Chorus → Verse → Chorus → Bridge → Chorus → Chorus → Outro

### Minimalist (4.0 minutes)
Ambient structure: Intro → Verse → Bridge → Verse → Outro (with sparse textures)

---

## Troubleshooting

### No Notes Generated
- Check that MIDI output is enabled
- Verify scale mapper is properly initialized
- Ensure BPM is reasonable (60-200 range)
- Song may be in between-songs pause (wait 5 seconds)

### Song Sections Not Changing
- Check that sufficient time has passed (sections are bar-based)
- Verify BPM is set correctly for timing calculations
- Song progression is automatic and cannot be rushed

### Probability Controls Not Working
- **This is expected behavior in song mode**
- Song mode manages its own density and timing
- Density controls work normally in other direction patterns
- To use probability controls, switch to a non-song direction pattern

### Switching Patterns
- All patterns can be switched without restart
- Pattern changes take effect immediately
- Song state is preserved when switching away and back
- New songs start automatically when returning to song mode

---

## Configuration Examples

### Jazz-Style Configuration
```yaml
sequencer:
  direction_pattern: song
  bpm: 140
  root_note: 60
  voices: 4
  
scales:
  - dorian
  - mixolydian
  - major
```

### Blues Configuration
```yaml
sequencer:
  direction_pattern: song
  bpm: 90
  root_note: 60
  voices: 2
  
scales:
  - blues
  - minor
```

### Pop Configuration
```yaml
sequencer:
  direction_pattern: song
  bpm: 120
  root_note: 62
  voices: 3
  
scales:
  - major
  - minor
  - pentatonic_major
```

---

## Future Extensions

- **Custom song patterns** via configuration
- **Song pattern learning** from MIDI input
- **Chord progression templates** 
- **Lyrical rhythm patterns**
- **Genre-specific variations** (rock, jazz, electronic)
- **Song form analysis** and automatic structure detection
- **Dynamic song length** based on activity level

---

**End of Song Mode Implementation Guide**
