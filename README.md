# Mystery Music Engine (Phase 6 + HID Refactor)

Phase 6 implements idle mode detection and management with automatic ambient profile switching. **NEW**: Hybrid input system supporting both HID arcade controls and MIDI from Teensy (see root `SPEC.md` + `docs/ROADMAP.md`).

## Implemented

### Phase 1 (MIDI & Routing)
- Auto / explicit MIDI port selection (prefers name containing 'teensy').
- Config-driven mapping (note ranges + CC) -> action strings.
- Emission + logging of `SemanticEvent` objects.
- Structured key=value logging formatter.
- Unit tests for config load, routing, channel filtering, ignoring unmapped inputs, invalid range handling, MIDI auto-select edge cases.

### Phase 2 (State & Sequencer)
- Observable state container with parameter validation and change listeners.
- High-resolution clock with drift correction and swing support.
- Basic sequencer with step management and configurable sequence length.
- Action handler translating semantic events to state changes and sequencer operations.
- Manual step triggering via button presses with immediate note generation.
- Real-time parameter updates (tempo, swing, density, sequence length, etc.).
- Comprehensive test suite for all Phase 2 components.
- **Complete configuration logging** - All settings logged at startup for transparency.

### Phase 3 (Scale Mapping & Probability)
- Scale mapping with real-time scale changes and quantized transitions.
- Probability density gating for step events.
- Basic note probability per step.

### Phase 4 (Integration & Polish)
- Full integration of scale mapping with sequencer.
- Enhanced probability gating with density control.
- Quantized parameter changes on bar boundaries.

### Phase 5 (Mutation Engine)
- Automated parameter mutations with configurable schedules.
- BPM drift envelopes for organic tempo variation.
- Mutation logging and state tracking.

### Phase 5.5 (Enhanced Probability & Rhythm Patterns) ✨
- **Per-step probability arrays** - Individual probability control for each step.
- **Configurable step patterns** - Flexible rhythm patterns beyond hardcoded sequences.
- **Direction patterns** - Multiple sequencer playback directions (forward, backward, ping-pong, random).
- **Velocity variation** - Dynamic velocity based on probability values with randomness.
- **Pattern & probability presets** - Ready-to-use rhythm and probability templates.
- **Backward compatibility** - All existing configurations continue to work unchanged.

### Phase 6 (Idle Mode) 🌙 **NEW**
- **Automatic idle detection** - Tracks user interactions and enters idle mode after configurable timeout.
- **Ambient profiles** - Pre-defined ambient sound profiles for idle mode (slow_fade, minimal, meditative).
- **State preservation** - Saves active state when entering idle mode and restores it when exiting.
- **Mutation integration** - Mutations only occur during idle periods, disabled during active use.
- **Configurable behavior** - Timeout, profiles, and fade timing all configurable via YAML.
- **Real-time monitoring** - Status tracking and callback system for integration with other components.

### HID Refactor (Phase 6+) 🎮 **NEW**
- **Hybrid Input System** - Supports both HID arcade controls and MIDI from Teensy simultaneously.
- **HID Arcade Buttons** - 10 arcade buttons via USB gamepad/joystick (maps to MIDI Notes 60-69).
- **HID Joystick** - 4-direction joystick control via USB gamepad (maps to MIDI CCs 50-53).
- **MIDI from Teensy** - Potentiometers and switches continue to work via existing MIDI input.
- **Seamless Integration** - Both input sources generate the same semantic events and work together.
- **Configurable Mapping** - HID button and joystick mappings configurable via YAML.
- **Backward Compatible** - Existing MIDI-only configurations continue to work unchanged.

## Run

**IMPORTANT**: All Python operations must be performed within the virtual environment.

```bash
# Activate virtual environment (from engine directory)
source .venv/bin/activate

# Install dependencies (including new pygame for HID support)
pip install -r requirements.txt

# Run tests
pytest tests -q

# Run specific phase tests
pytest tests/test_idle.py -v          # Phase 6: Idle mode tests
pytest tests/test_hid_input.py -v     # HID refactor: Hybrid input tests
pytest tests/test_mutation.py -v      # Phase 5: Mutation engine tests  
pytest tests/test_sequencer.py -v     # Phase 5.5: Enhanced sequencer tests

# Run engine
python src/main.py --config config.yaml --log-level INFO

# Run Phase 5.5 demo (shows new features)
python demo_phase5_5.py

# Run direction patterns demo (detailed direction pattern showcase)
python demo_direction_patterns.py

# Run idle mode demo (Phase 6 - shows idle detection and ambient profiles)
python demo_idle_mode.py

# Run hybrid input demo (HID + MIDI input system) 🎮 NEW
python demo_hybrid_input.py

# Run mutation demo (shows mutation engine)
python demo_mutation.py
```

Example log lines:
```
ts=2025-08-20T12:00:00 level=INFO logger=engine msg=semantic type=trigger_step source=button value=100 note=60 ch=1
ts=2025-08-20T12:00:00 level=INFO logger=engine msg=note_event note=60 velocity=100 step=0
ts=2025-08-20T12:00:01 level=DEBUG logger=sequencer msg=step_advance step=1 length=8
ts=2025-08-20T12:00:01 level=INFO logger=sequencer msg=step_probabilities_set length=8 values=[1.0, 0.8, 0.6, 0.4, 0.2, 0.6, 0.8, 1.0]
ts=2025-08-20T12:00:01 level=INFO logger=sequencer msg=step_pattern_set length=8 pattern=[True, False, True, True, False, False, True, False]
ts=2025-08-20T12:00:01 level=DEBUG logger=sequencer msg=note_generated step=0 note=60 velocity=95 step_prob=1.00
ts=2025-08-20T12:00:30 level=INFO logger=idle msg=idle_mode_enter
ts=2025-08-20T12:00:30 level=INFO logger=idle msg=idle_profile_applied profile=slow_fade params=[density, bpm, scale_index, reverb_mix, filter_cutoff, master_volume]
ts=2025-08-20T12:00:45 level=INFO logger=idle msg=idle_mode_exit
ts=2025-08-20T12:00:45 level=INFO logger=idle msg=idle_state_restored params=[density, bpm, scale_index, reverb_mix, filter_cutoff, master_volume]
```

Set `ENGINE_DEBUG_TIMING=1` for extra timing debug categories (future phases).

## Architecture (Phase 6 + HID Refactor)

```
HID Input (Arcade) ──┐
                     ├─→ Hybrid Input ──→ Action Handler → State Container
MIDI Input (Teensy) ──┘      │                   ↓              ↓
                              ├─→ Semantic Events        State Changes
                              └─→ Router                      ↓
                                     ↓                   Sequencer Clock
                              Audio Backend                   ↓
                                                    Step Events → Pattern Gate
                                                             ↓
                                    Probability Gate (Per-Step)
                                                             ↓
                                    Scale Mapper → Note Generation
                                                             ↓
                                    Velocity Variation → Audio Output
                                         
Idle Manager ←──────────── Interaction Tracking
     ↓
Ambient Profiles → State Preservation/Restoration
     ↓
Mutation Engine (Idle-Aware) → Parameter Changes
```

## Key Components

- **State**: Observable parameter store with validation and change notifications
- **Sequencer**: High-resolution clock with step management and enhanced note generation
- **ActionHandler**: Bridges semantic events to state changes and sequencer operations
- **HighResClock**: Precise timing with swing support and drift correction
- **Pattern System**: Configurable step activation patterns with presets ✨
- **Probability Engine**: Per-step probability control with preset templates ✨
- **Direction Engine**: Multiple sequencer playback directions (forward, backward, ping-pong, random) ✨
- **Velocity Engine**: Dynamic velocity variation based on probability values ✨
- **Idle Manager**: Automatic idle detection with ambient profile switching 🌙
- **Mutation Engine**: Idle-aware parameter mutations for evolving soundscapes
- **Hybrid Input System**: Unified input from both HID arcade controls and MIDI Teensy 🎮
- **HID Input**: USB gamepad/joystick support for arcade buttons and joystick 🎮
- **MIDI Input**: Existing Teensy support for potentiometers and switches 🎛️

## Current Capabilities

- Real-time tempo changes (60-200 BPM)
- Swing adjustment (0-50%)
- Sequence length control (1-32 steps)
- Manual step triggering via button presses
- Automatic step advancement with configurable timing
- Parameter validation and clamping
- Structured logging of all events
- Scale mapping with multiple scales and real-time switching
- Probability density gating for overall sparseness control
- Per-step probability arrays for fine-grained control
- Configurable step patterns for flexible rhythm creation
- Dynamic velocity variation based on probability values
- Automated parameter mutations for evolving soundscapes
- Automatic idle mode with ambient profiles and state preservation
- Idle-aware mutations (only occur during idle periods)

## Configuration Parameters

### Core Sequencer Parameters
| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `bpm` | float | 60.0-200.0 | 110.0 | Beats per minute |
| `swing` | float | 0.0-0.5 | 0.12 | Swing amount (0=straight, 0.5=max swing) |
| `density` | float | 0.0-1.0 | 0.85 | Overall probability gate for all steps |
| `sequence_length` | int | 1-32 | 8 | Number of steps in the sequence |

### Legacy Probability (Backward Compatibility)
| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `note_probability` | float | 0.0-1.0 | 0.9 | Global note probability (used when step_probabilities is None) |

### Phase 5.5: Enhanced Patterns & Probability ✨
| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `step_probabilities` | array | [0.0-1.0, ...] | None | Per-step probability values (overrides note_probability) |
| `step_pattern` | array | [bool, ...] | None | Per-step activation pattern (overrides hardcoded even-step pattern) |
| `direction_pattern` | string | See Direction Patterns | 'forward' | Sequencer playback direction |
| `base_velocity` | int | 1-127 | 80 | Base MIDI velocity for notes |
| `velocity_range` | int | 0-127 | 40 | Range for velocity variation (+/- from base) |

### Scale & Mapping
| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `scale_index` | int | 0-8 | 0 | Index into available scales list (see **Supported Scales** below) |
| `root_note` | int | 0-127 | 60 | Root note for scale (MIDI note number) |
| `quantize_scale_changes` | string | `bar`, `immediate` | `bar` | When to apply scale changes (bar boundary or immediately) |

### Phase 6: Idle Mode & Mutations 🌙
| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `idle.timeout_ms` | int | 1000+ | 30000 | Idle timeout in milliseconds (30s default) |
| `idle.ambient_profile` | string | See Profiles | 'slow_fade' | Ambient profile to use in idle mode |
| `idle.fade_in_ms` | int | 0+ | 4000 | Fade in duration for LED transitions |
| `idle.fade_out_ms` | int | 0+ | 800 | Fade out duration for LED transitions |
| `mutation.interval_min_s` | int | 1+ | 120 | Minimum mutation interval in seconds |
| `mutation.interval_max_s` | int | 1+ | 240 | Maximum mutation interval in seconds |
| `mutation.max_changes_per_cycle` | int | 0+ | 2 | Max parameter changes per mutation cycle |

### HID Refactor: Arcade Controls 🎮
| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `hid.device_name` | string | Device name | 'Generic USB Joystick' | Name of HID device to connect to |
| `hid.button_mapping` | dict | Button index → action | {0-9: 'trigger_step'} | Mapping of button indices to semantic actions |
| `hid.joystick_mapping` | dict | Direction → action | See below | Mapping of joystick directions to semantic actions |

**Default HID Joystick Mapping**:
```yaml
joystick_mapping:
  up: "osc_a"       # Maps to MIDI CC 50
  down: "osc_b"     # Maps to MIDI CC 51
  left: "mod_a"     # Maps to MIDI CC 52
  right: "mod_b"    # Maps to MIDI CC 53
```

**Default HID Button Mapping**:
```yaml
button_mapping:
  0: "trigger_step"  # Button 0 → MIDI Note 60
  1: "trigger_step"  # Button 1 → MIDI Note 61
  # ... (continues for buttons 2-9 → MIDI Notes 62-69)
```

## Pattern Presets 🎵

Use `sequencer.get_pattern_preset(preset_name)` to get predefined step patterns:

| Preset Name | Pattern | Description |
|-------------|---------|-------------|
| `four_on_floor` | `[T,F,F,F,T,F,F,F]` | Classic 4/4 kick pattern |
| `offbeat` | `[F,T,F,T,F,T,F,T]` | Emphasis on off-beats |
| `every_other` | `[T,F,T,F,T,F,T,F]` | Alternating on/off pattern |
| `syncopated` | `[T,F,T,T,F,T,F,F]` | Syncopated rhythm with emphasis shifts |
| `dense` | `[T,T,F,T,T,F,T,T]` | High-density pattern with occasional rests |
| `sparse` | `[T,F,F,F,F,F,T,F]` | Minimal pattern with long gaps |
| `all_on` | `[T,T,T,T,T,T,T,T]` | Every step active |
| `all_off` | `[F,F,F,F,F,F,F,F]` | Every step inactive |

*T=True (step active), F=False (step inactive)*

**Usage**: 
```python
pattern = sequencer.get_pattern_preset('syncopated')
sequencer.set_step_pattern(pattern)
```

## Direction Patterns 🎯

Use `sequencer.set_direction_pattern(pattern_name)` to control sequencer playback direction:

| Pattern Name | Description | Behavior |
|-------------|-------------|-----------|
| `forward` | Standard left-to-right playback | Steps advance 0→1→2→3...→N→0 |
| `backward` | Right-to-left playback | Steps advance N→...→3→2→1→0→N |
| `ping_pong` | Bouncing back and forth | Steps advance 0→1→2→3→2→1→0→1... |
| `random` | Random step selection | Each step chooses randomly from all other steps |

**Default**: `forward` (maintains backward compatibility)

**Usage**: 
```python
sequencer.set_direction_pattern('ping_pong')
# Or validate first
direction = sequencer.get_direction_preset('backward')
sequencer.set_direction_pattern(direction)
```

## Probability Presets 🎲

Use `sequencer.get_probability_preset(preset_name, length)` to get predefined probability patterns:

| Preset Name | Description | Example (8 steps) |
|-------------|-------------|-------------------|
| `uniform` | Equal probability for all steps | `[0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]` |
| `crescendo` | Gradually increasing probability | `[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.9]` |
| `diminuendo` | Gradually decreasing probability | `[0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.3]` |
| `peaks` | High probability every 4th step | `[0.9, 0.4, 0.4, 0.4, 0.9, 0.4, 0.4, 0.4]` |
| `valleys` | Low probability every 4th step | `[0.3, 0.8, 0.8, 0.8, 0.3, 0.8, 0.8, 0.8]` |
| `alternating` | High/low alternating pattern | `[0.9, 0.3, 0.9, 0.3, 0.9, 0.3, 0.9, 0.3]` |
| `random_low` | Random values in low range | `[0.2-0.6 random values]` |
| `random_high` | Random values in high range | `[0.6-1.0 random values]` |

**Usage**: 
```python
probs = sequencer.get_probability_preset('crescendo', length=8)
sequencer.set_step_probabilities(probs)
```

## Idle Profiles 🌙

Available ambient profiles for idle mode (configured via `idle.ambient_profile`):

| Profile Name | Description | Characteristics |
|--------------|-------------|-----------------|
| `slow_fade` | Gentle ambient fade (default) | Reduced density (0.3), slower tempo (65 BPM), pentatonic scale, increased reverb, darker filter, quieter volume |
| `minimal` | Ultra-minimal ambient | Very low density (0.15), very slow tempo (50 BPM), full reverb, very quiet |
| `meditative` | Contemplative minor ambient | Medium density (0.4), minor scale, no swing, dark filter, moderate volume |

**Behavior**: 
- System automatically enters idle mode after configured timeout (default: 30 seconds)
- Any MIDI interaction immediately exits idle mode and restores previous settings
- Only parameters defined in the idle profile are changed/restored
- Mutations are only active during idle mode

## Supported Scales 🎼

The following scales are available in the system (use `scale_index` 0-8 to select):

| Index | Scale Name | Intervals (Semitones) | Description |
|-------|------------|----------------------|-------------|
| 0 | `major` | [0, 2, 4, 5, 7, 9, 11] | Standard major scale (Ionian mode) |
| 1 | `minor` | [0, 2, 3, 5, 7, 8, 10] | Natural minor scale (Aeolian mode) |
| 2 | `pentatonic_major` | [0, 2, 4, 7, 9] | Major pentatonic scale (5-note) |
| 3 | `pentatonic_minor` | [0, 3, 5, 7, 10] | Minor pentatonic scale (5-note) |
| 4 | `mixolydian` | [0, 2, 4, 5, 7, 9, 10] | Mixolydian mode (dominant 7th flavor) |
| 5 | `blues` | [0, 3, 5, 6, 7, 10] | Blues scale (6-note) |
| 6 | `dorian` | [0, 2, 3, 5, 7, 9, 10] | Dorian mode (minor with raised 6th) |
| 7 | `locrian` | [0, 1, 3, 5, 6, 8, 10] | Locrian mode (diminished flavor) |
| 8 | `chromatic` | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11] | All 12 semitones |

## Supported CC Profiles 🎛️

The following CC profiles are available for external synthesizers (configured via `midi.cc_profile.active_profile`):

### Built-in Profiles
| Profile ID | Name | Description | Parameter Count |
|------------|------|-------------|-----------------|
| `korg_nts1_mk2` | Korg NTS-1 MK2 | Complete parameter mapping for Korg NTS-1 MK2 digital synthesizer | 15+ parameters |
| `generic_analog` | Generic Analog Synth | Standard analog subtractive synthesis parameters | 10+ parameters |
| `fm_synth` | FM Synthesizer | Operator-based FM synthesis with 2 operators | 8+ parameters |
| `waldorf_streichfett` | Waldorf Streichfett | Dual engine string synthesizer with string, solo, and effects sections | 15+ parameters |

### Custom Profiles
You can also define custom CC profiles in `config.yaml` under the `cc_profiles` section with your own parameter mappings.

### CC Parameter Curve Types
| Curve Type | Description | Best For |
|------------|-------------|----------|
| `linear` | Direct 0-1 to CC value mapping | Most parameters |
| `exponential` | Smoother control at low values | Filters, envelopes |
| `logarithmic` | More precision at high values | Frequencies |
| `stepped` | Discrete values | Waveform selection, modes |

## Configuration Example (config.yaml)

```yaml
# HID Input Configuration (arcade buttons + joystick) 🎮 NEW
hid:
  device_name: "Generic USB Joystick"
  button_mapping:
    0: "trigger_step"    # Button 0 → Note 60
    1: "trigger_step"    # Button 1 → Note 61
    # ... continues for buttons 2-9
  joystick_mapping:
    up: "osc_a"         # Joystick Up → CC 50
    down: "osc_b"       # Joystick Down → CC 51
    left: "mod_a"       # Joystick Left → CC 52
    right: "mod_b"      # Joystick Right → CC 53

# MIDI Input Configuration (Teensy potentiometers + switches)
midi:
  input_port: "auto"
  output_port: "RK006 OUT_ALL"
  input_channel: 1
  output_channel: 12

# Note: Button and joystick mappings moved to HID section
# MIDI mapping now only contains Teensy potentiometers and switches
mapping:
  buttons: {}  # Empty - buttons handled by HID
  ccs:
    "21": filter_cutoff      # K1 potentiometer
    "22": filter_resonance   # K2 potentiometer
    "60": osc_type          # S1 switch
    "61": filter_type       # S2 switch
    # No joystick CCs - handled by HID

idle:
  timeout_ms: 30000          # 30 second timeout
  ambient_profile: slow_fade # Choose: slow_fade, minimal, meditative  
  fade_in_ms: 4000          # 4 second LED fade in
  fade_out_ms: 800          # 0.8 second LED fade out

mutation:
  interval_min_s: 120       # 2 minute minimum between mutations
  interval_max_s: 240       # 4 minute maximum between mutations  
  max_changes_per_cycle: 2  # Max 2 parameters changed per mutation
```

## Usage Examples

### Setting Custom Step Probabilities
```python
# Set individual probabilities for each step
sequencer.set_step_probabilities([1.0, 0.8, 0.6, 0.4, 0.2, 0.6, 0.8, 1.0])

# Or use a preset
probs = sequencer.get_probability_preset('crescendo', length=8)
sequencer.set_step_probabilities(probs)
```

### Setting Custom Step Patterns
```python
# Set a custom pattern
sequencer.set_step_pattern([True, False, True, True, False, False, True, False])

# Or use a preset
pattern = sequencer.get_pattern_preset('syncopated')
sequencer.set_step_pattern(pattern)
```

### Setting Direction Patterns
```python
# Set direction pattern
sequencer.set_direction_pattern('ping_pong')

# Or use a preset (validates the name)
direction = sequencer.get_direction_preset('backward')
sequencer.set_direction_pattern(direction)
```

### Configuring Velocity Variation
```python
# Set base velocity and variation range
sequencer.set_velocity_params(base_velocity=100, velocity_range=30)
# Results in velocities ranging roughly from 70-130 based on step probability
```

### Backward Compatibility
```python
# Old-style configuration still works
state.set('note_probability', 0.7)  # Applied to all steps when step_probabilities is None
# Hardcoded even-step pattern used when step_pattern is None
```

## Dynamic Configuration API 🌐 **NEW**

The engine now includes a REST API for real-time configuration changes without requiring a restart.

### Features
- **Real-time updates**: Modify any configuration parameter while the engine runs
- **Validation**: All changes are validated before application
- **System state**: Monitor internal state and trigger events
- **Auto-documentation**: Interactive API docs at `/docs`

### Quick Start
```bash
# Start the engine (API enabled by default on port 8080)
python src/main.py --config config.yaml

# In another terminal - update BPM
curl -X POST http://localhost:8080/config \
  -H "Content-Type: application/json" \
  -d '{"path": "sequencer.bpm", "value": 120.0}'

# Change sequencer direction
curl -X POST "http://localhost:8080/actions/semantic?action=set_direction_pattern&value=ping_pong"

# Get current state
curl http://localhost:8080/state
```

### Python Client Example
```python
from examples.api_demo import APIClient

client = APIClient("http://localhost:8080")

# Update configuration
client.update_config("sequencer.density", 0.8)
client.update_config("mutation.interval_min_s", 45)

# Trigger events
client.trigger_semantic_event("set_direction_pattern", "random")

# Monitor state
state = client.get_state()
print(f"Current BPM: {state['bpm']}")
```

### API Configuration
```yaml
api:
  enabled: true
  port: 8080
  host: "0.0.0.0"    # Set to "127.0.0.1" for localhost-only
  log_level: "info"
```

For complete API documentation, see [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md).

### Idle Mode Control (Phase 6) 🌙
```python
# Manual idle mode control (for testing/debugging)
idle_manager.force_idle()    # Enter idle mode immediately
idle_manager.force_active()  # Exit idle mode immediately

# Monitor idle status
status = idle_manager.get_status()
print(f"Idle: {status['is_idle']}")
print(f"Time to idle: {status['time_to_idle']:.1f}s")

# Register for idle state change notifications
def on_idle_change(is_idle):
    print(f"Idle mode: {'ON' if is_idle else 'OFF'}")

idle_manager.add_idle_state_callback(on_idle_change)
```

### Mutation Engine Control
```python
# Check if mutations are enabled (only when idle)
enabled = mutation_engine.are_mutations_enabled()

# Force a mutation (for testing - only works when enabled)
mutation_engine.force_mutation()

# Get mutation statistics
stats = mutation_engine.get_stats()
print(f"Total mutations: {stats['total_mutations']}")
print(f"Next mutation in: {stats['time_to_next_mutation_s']:.1f}s")

# Get mutation history
history = mutation_engine.get_history(5)  # Last 5 mutations
for event in history:
    print(f"{event.parameter}: {event.old_value} → {event.new_value}")
```

## Next (Phase 7)
- LED event emission for interaction feedback and idle state visualization.
- Enhanced integration with Teensy firmware for visual feedback.
- Additional ambient profiles and customization options.

## Configuration Reference 📖

### Complete Configuration Value Lists

For easy reference, here are all supported values for key configuration options:

**Scales** (`scale_index` 0-8):
- `major`, `minor`, `pentatonic_major`, `pentatonic_minor`, `mixolydian`, `blues`, `dorian`, `locrian`, `chromatic`

**Ambient Profiles** (`idle.ambient_profile`):
- `slow_fade`, `minimal`, `meditative`

**Direction Patterns** (`direction_pattern`):
- `forward`, `backward`, `ping_pong`, `random`

**Step Pattern Presets** (use `sequencer.get_pattern_preset(name)`):
- `four_on_floor`, `offbeat`, `every_other`, `syncopated`, `dense`, `sparse`, `all_on`, `all_off`

**Probability Presets** (use `sequencer.get_probability_preset(name, length)`):
- `uniform`, `crescendo`, `diminuendo`, `peaks`, `valleys`, `alternating`, `random_low`, `random_high`

**Quantize Scale Changes** (`quantize_scale_changes`):
- `bar` (apply at bar boundaries), `immediate` (apply immediately)

**CC Profiles** (`midi.cc_profile.active_profile`):
- `korg_nts1_mk2`, `generic_analog`, `fm_synth`, `waldorf_streichfett`, plus any custom profiles defined in config

**CC Curve Types** (for custom profiles):
- `linear`, `exponential`, `logarithmic`, `stepped`

**Logging Levels** (`logging.level`):
- `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

License: Apache-2.0
