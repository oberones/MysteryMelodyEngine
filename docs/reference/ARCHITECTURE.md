# Architecture Documentation

**Mystery Music Engine (Raspberry Pi Generative Engine)**  
Version: 0.7.0  
Current Status: Phase 7 (External Hardware Integration)  
Last Updated: August 24, 2025

## Overview

The Mystery Music Engine is a real-time generative music system designed to receive MIDI input from a Teensy-based hardware controller and produce evolving musical sequences on external hardware synthesizers. The system emphasizes low-latency responsiveness, musical coherence, and long-term autonomous operation.

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Raspberry Pi Engine                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐                │
│  │ MIDI Input  │───▶│    Router    │───▶│ActionHandler │                │
│  │             │    │              │    │              │                │
│  │ - Port mgmt │    │ - Map raw    │    │ - Semantic   │                │
│  │ - Event     │    │   MIDI to    │    │   event      │                │
│  │   dispatch  │    │   semantic   │    │   handling   │                │
│  └─────────────┘    │   actions    │    │ - State      │                │
│                     └──────────────┘    │   updates    │                │
│                                         └───────┬──────┘                │
│                                                 │                       │
│  ┌─────────────────────────────────────────────▼───────────────────────┐│
│  │                    State Container                                  ││
│  │                                                                     ││
│  │ - Observable parameter store                                        ││
│  │ - Validation & clamping                                             ││
│  │ - Change notification system                                        ││
│  │ - Thread-safe access                                                ││
│  └─────────────────────────┬───────────────────────────────────────────┘│
│                            │                                            │
│    ┌───────────────────────▼──────────┐    ┌──────────────────────────┐ │
│    │       Sequencer Core             │    │    Mutation Engine       │ │
│    │                                  │    │                          │ │
│    │ - High-res clock (drift corr.)   │    │ - Scheduled param        │ │
│    │ - Step management                │    │   mutations              │ │
│    │ - Pattern & probability engine   │    │ - Weighted selection     │ │
│    │ - Direction patterns             │    │ - Idle-aware operation   │ │
│    │ - Scale mapping integration      │    │ - Musical bounds         │ │
│    └───────────────┬──────────────────┘    └──────────────────────────┘ │
│                    │                                                    │
│    ┌───────────────▼──────────────────┐    ┌──────────────────────────┐ │
│    │       Scale Mapper               │    │     Idle Manager         │ │
│    │                                  │    │                          │ │
│    │ - Musical scale definitions      │    │ - Interaction tracking   │ │
│    │ - Note quantization              │    │ - Ambient mode switching │ │
│    │ - Root note transposition        │    │ - Smooth transitions     │ │
│    └───────────────┬──────────────────┘    └──────────────────────────┘ │
│                    │                                                    │
│    ┌───────────────▼──────────────────┐                                 │
│    │       Note Generation            │                                 │
│    │                                  │                                 │
│    │ - Velocity variation             │                                 │
│    │ - Gate length calculation        │                                 │
│    │ - Note event creation            │                                 │
│    └───────────────┬──────────────────┘                                 │
│                    │                                                    │
└────────────────────┼────────────────────────────────────────────────────┘
                     │
    ┌────────────────▼────────────────┐
    │        MIDI Output              │
    │                                 │
    │ - External synth routing        │
    │ - Note scheduling               │
    │ - CC profile management         │
    │ - Latency optimization          │
    └─────────────────────────────────┘
                     │
                     ▼
    ┌─────────────────────────────────┐
    │      External Hardware          │
    │                                 │
    │ - Korg NTS1 MK2                 │
    │ - Waldorf Streichfett           │
    │ - Generic analog synths         │
    │ - Custom CC profiles            │
    └─────────────────────────────────┘
```

## Core Components

### 1. Main Engine (`main.py`)

**Purpose**: Application entry point and component orchestration

**Key Responsibilities**:
- Configuration loading and validation
- Component initialization and lifecycle management
- MIDI I/O setup and connection management
- Note scheduling and timing coordination
- Graceful shutdown handling

**Key Methods**:
- `main(argv)`: Primary entry point with argument parsing
- `NoteScheduler`: Handles proper MIDI note off timing
- `handle_note_event()`: Routes note events to MIDI output
- `handle_semantic()`: Routes semantic events to action handler

**Architecture Integration**:
- Creates and connects all major system components
- Establishes callback chains for event flow
- Manages the main event loop and periodic operations

### 2. MIDI Input Layer (`midi_in.py`)

**Purpose**: Hardware interface for receiving MIDI from Teensy controller

**Key Responsibilities**:
- MIDI port discovery and auto-selection (prefers "teensy" ports)
- Real-time MIDI message reception and dispatch
- Connection error handling and recovery
- Background thread management for MIDI callbacks

**Key Methods**:
- `MidiInput.create(desired, callback)`: Factory method with auto-selection
- `auto_select()`: Intelligent port selection logic
- `_on_msg(msg)`: Background thread MIDI message handler

**Data Flow**:
```
Hardware MIDI → Port → Background Thread → Callback → Router
```

### 3. Router Layer (`router.py`)

**Purpose**: Translates raw MIDI messages to semantic actions

**Key Responsibilities**:
- Configuration-driven MIDI mapping (buttons: note ranges, CCs: individual)
- Channel filtering based on configuration
- Note-off filtering (ignores releases in current implementation)
- Semantic event generation

**Key Methods**:
- `_build_maps()`: Constructs note and CC mapping tables from config
- `route(msg)`: Main message routing logic
- Range parsing for button mappings (e.g., "60-69")

**Data Structures**:
```python
class SemanticEvent:
    type: str        # Action type (e.g., 'trigger_step', 'tempo')
    source: str      # Input source ('button', 'cc')
    value: int       # MIDI value (velocity, CC value)
    raw_note: int    # Original note number (if applicable)
    raw_cc: int      # Original CC number (if applicable)
    channel: int     # MIDI channel (1-based)
```

### 4. State Management (`state.py`)

**Purpose**: Central parameter store with validation and change notification

**Key Responsibilities**:
- Thread-safe parameter storage with RLock protection
- Parameter validation and automatic clamping
- Observable pattern implementation with change listeners
- Source tracking for parameter changes

**Key Methods**:
- `set(param, value, source)`: Validated parameter updates
- `update_multiple(updates, source)`: Atomic multi-parameter updates
- `add_listener(callback)`: Change notification subscription
- `_validate_param(param, value)`: Parameter-specific validation logic

**State Change Flow**:
```
Parameter Update → Validation → Clamping → Change Detection → 
Listener Notification → Component Updates
```

**Key Parameters**:
- Musical: `bpm`, `swing`, `density`, `scale_index`, `root_note`
- Sequencer: `sequence_length`, `step_position`, `step_pattern`
- Audio: `filter_cutoff`, `reverb_mix`, `master_volume`, `gate_length`
- System: `idle_mode`, `chaos_lock`, `drift`

### 5. Action Handler (`action_handler.py`)

**Purpose**: Bridges semantic events to state changes and sequencer operations

**Key Responsibilities**:
- Semantic event interpretation and routing
- Parameter value scaling and conversion (MIDI 0-127 to parameter ranges)
- Manual step triggering for immediate note generation
- Idle manager interaction tracking
- Integration with external hardware management

**Key Methods**:
- `handle_semantic_event(event)`: Main event dispatch logic
- `_handle_trigger_step(event)`: Manual sequencer advancement
- `_handle_tempo(event)`: BPM parameter conversion and setting
- Various parameter-specific handlers for different CC mappings

**Parameter Mapping Examples**:
```python
# MIDI CC 0-127 → BPM 60-200
bpm = 60.0 + (event.value / 127.0) * 140.0

# MIDI CC 0-127 → Density 0.0-1.0  
density = event.value / 127.0

# MIDI CC 0-127 → Scale Index (clamped to available scales)
scale_index = min(event.value // 16, len(available_scales) - 1)
```

### 6. Sequencer Core (`sequencer.py`)

**Purpose**: High-precision timing engine and pattern generation

**Architecture Overview**:
```
┌─────────────────┐    ┌──────────────────┐    ┌────────────────┐
│  HighResClock   │───▶│ Sequencer Logic  │───▶│ Note Generation│
│                 │    │                  │    │                │
│ - Drift correct │    │ - Step patterns  │    │ - Scale mapping│
│ - Swing timing  │    │ - Probability    │    │ - Velocity var │
│ - PPQ precision │    │ - Direction      │    │ - Gate length  │
└─────────────────┘    └──────────────────┘    └────────────────┘
```

#### 6.1 HighResClock Class

**Key Responsibilities**:
- Monotonic high-resolution timing with drift correction
- Swing timing for musical feel
- Configurable PPQ (Pulses Per Quarter) support
- Background thread execution

**Timing Algorithm**:
```python
tick_interval = 60.0 / (self.bpm * self.ppq)
target_time = start_time + (tick_count * tick_interval)

# Swing adjustment for odd 16th notes
if is_swing_tick:
    target_time += swing * tick_interval

# Drift correction
current_time = time.perf_counter()
sleep_time = target_time - current_time
```

#### 6.2 Sequencer Pattern Engine

**Features**:
- **Step Patterns**: Configurable activation patterns (all_on, syncopated, four_on_the_floor)
- **Direction Patterns**: forward, backward, ping-pong, random
- **Per-Step Probability**: Individual probability values for each step
- **Velocity Variation**: Dynamic velocity based on step probability
- **Gate Length**: Configurable note duration as fraction of step time

**Pattern Presets**:
```python
PATTERN_PRESETS = {
    'all_on': [True] * 16,
    'four_on_the_floor': [True, False, False, False] * 4,
    'syncopated': [True, False, True, True, False, False, True, False] * 2,
    'minimal': [True] + [False] * 7
}
```

**Key Methods**:
- `_on_tick(tick_event)`: Main sequencer tick handler
- `_advance_step()`: Step position advancement with direction patterns
- `_generate_step_note(step)`: Note generation with probability and scale mapping
- `set_bpm_immediate(bpm)` / `start_bpm_transition(...)`: BPM control

### 7. Scale Mapping (`scale_mapper.py`)

**Purpose**: Musical scale definitions and note quantization

**Scale Definitions**:
```python
SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "blues": [0, 3, 5, 6, 7, 10],
    "chromatic": list(range(12))
}
```

**Key Methods**:
- `set_scale(scale_name, root_note)`: Scale and root configuration
- `get_note(degree, octave)`: Scale degree to MIDI note conversion
- `get_notes(num_notes, start_degree, octave)`: Multiple note generation

**Note Calculation**:
```python
def get_note(self, degree: int, octave: int = 0) -> int:
    scale_len = len(self.current_scale_intervals)
    octave_offset = (degree // scale_len) * 12
    interval = self.current_scale_intervals[degree % scale_len]
    return self.root_note + interval + (octave * 12) + octave_offset
```

### 8. MIDI Output Layer (`midi_out.py`)

**Purpose**: External hardware synthesis communication

**Key Responsibilities**:
- Multi-port MIDI output with auto-selection
- Connection management and recovery
- Note on/off timing coordination
- Control change message transmission
- Latency optimization

**Key Classes**:
- `MidiOutput`: Full MIDI output implementation
- `NullMidiOutput`: Disabled output placeholder

**Connection Management**:
```python
def _ensure_connected(self) -> bool:
    if self._is_connected and self.port:
        return True
    if self.port_name:
        return self._connect()
    return False
```

### 9. Mutation Engine (`mutation.py`)

**Purpose**: Autonomous parameter evolution during idle periods

**Architecture**:
```
┌─────────────────┐    ┌────────────────┐    ┌─────────────────┐
│  Mutation Rules │───▶│ Rule Selection │───▶│ Parameter Delta │
│                 │    │                │    │                 │
│ - Weight system │    │ - Random pick  │    │ - Bounded change│
│ - Delta ranges  │    │ - Max changes  │    │ - State update  │
│ - Parameter map │    │   per cycle    │    │ - History log   │
└─────────────────┘    └────────────────┘    └─────────────────┘
```

**Key Features**:
- **Weighted Selection**: Higher weight = higher selection probability
- **Bounded Deltas**: Musical parameter boundaries prevent extreme values
- **Idle-Aware**: Only operates when system is in idle mode
- **Configurable Timing**: Random intervals between mutation cycles
- **History Tracking**: Maintains log of applied mutations

**Example Mutation Rules**:
```python
MutationRule(
    parameter="bpm",
    weight=2.0,
    delta_range=(-5.0, 5.0),
    description="Tempo drift"
),
MutationRule(
    parameter="density", 
    weight=1.5,
    delta_range=(-0.1, 0.1),
    description="Density variation"
)
```

### 10. Idle Management (`idle.py`)

**Purpose**: Automatic ambient mode switching during inactivity

**Idle Detection Flow**:
```
User Interaction → Touch() → Reset Timer → Monitor Thread →
Timeout Check → Ambient Profile → Smooth Transition
```

**Key Features**:
- **Interaction Tracking**: Monitors all user inputs with timestamps
- **Smooth Transitions**: Gradual parameter changes to ambient values
- **Profile System**: Predefined ambient configurations
- **Immediate Exit**: Instant return to normal mode on interaction
- **Mutation Integration**: Enables mutation engine during idle periods

**Idle Profiles**:
```python
"slow_fade": {
    'density': 0.3,          # Reduce note density
    'bpm': 65.0,             # Slower tempo  
    'scale_index': 2,        # Pentatonic scale
    'reverb_mix': 90,        # More reverb
    'filter_cutoff': 40,     # Darker filter
    'master_volume': 60      # Quieter
}
```

## Data Flow Architecture

### Primary Event Flow

```
1. MIDI Hardware Input
   ↓
2. MidiInput (background thread)
   ↓  
3. Router (semantic event generation)
   ↓
4. ActionHandler (parameter interpretation)
   ↓
5. State (validated parameter updates)
   ↓
6. Component Notifications (change listeners)
   ↓
7. Sequencer/Mutation/Idle responses
```

### Note Generation Flow

```
1. Sequencer Clock Tick
   ↓
2. Step Pattern Gate (active step check)
   ↓  
3. Probability Gate (per-step probability)
   ↓
4. Scale Mapper (degree → MIDI note)
   ↓
5. Velocity/Gate Length Calculation
   ↓
6. Note Event Generation
   ↓
7. MIDI Output (with scheduling)
   ↓
8. External Hardware Synthesis
```

### Configuration Flow

```
1. YAML Config Loading (config.py)
   ↓
2. Pydantic Validation (structured config classes)
   ↓
3. Component Initialization (main.py)
   ↓
4. Runtime Parameter Distribution
   ↓
5. State Container Population
   ↓
6. Component Configuration Application
```

## Threading Model

### Thread Architecture

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Main Thread   │  │ MIDI Input      │  │ Sequencer Clock │
│                 │  │ (mido callback) │  │ (HighResClock)  │
│ - Initialization│  │                 │  │                 │
│ - Event loop    │  │ - Msg reception │  │ - Tick generation│
│ - Shutdown      │  │ - Router calls  │  │ - Swing timing  │
└─────────────────┘  └─────────────────┘  └─────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Mutation Engine │  │  Idle Manager   │  │ Note Scheduler  │
│                 │  │                 │  │                 │
│ - Periodic      │  │ - Timeout check │  │ - Note off      │
│   mutations     │  │ - Profile mgmt  │  │   scheduling    │
│ - Idle aware    │  │ - Transition    │  │ - MIDI timing   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Thread Safety

**State Management**:
- `threading.RLock()` for parameter updates
- Atomic operations for critical sections
- Change listener notifications protected

**Sequencer Timing**:
- Monotonic clock for precision
- Lock-free tick generation where possible
- Callback isolation for note events

**MIDI Operations**:
- Background thread for input
- Foreground thread for output  
- Connection state management with locks

## Performance Characteristics

### Latency Targets

| Operation | Target | Implementation |
|-----------|--------|----------------|
| MIDI Input → Semantic Event | < 5ms | Background thread + direct callback |
| Semantic Event → State Update | < 2ms | Direct function calls, no queuing |
| State Update → Component Response | < 1ms | Change listener callbacks |
| Sequencer Tick Jitter | < 2ms | High-resolution monotonic clock |
| Note Generation → MIDI Output | < 10ms | Direct MIDI port writing |

### Memory Management

**Fixed Allocations**:
- Configuration structures (loaded once)
- Scale definitions (static arrays)
- Pattern presets (compile-time constants)

**Dynamic Allocations**:
- State change events (short-lived)
- Note events (immediate processing)
- Mutation history (bounded circular buffer)

**Resource Limits**:
- Mutation history: 100 events maximum
- Note scheduler: Active note tracking with cleanup
- State parameters: Fixed parameter set, no dynamic expansion

## Configuration Architecture

### Configuration Schema

```yaml
# High-level configuration structure
logging: { level: INFO }
midi: { input_port, output_port, channels, clock_config, cc_profiles }
mapping: { buttons: {}, ccs: {} }
sequencer: { steps, bpm, swing, patterns, directions }
scales: [ scale_names... ]
mutation: { intervals, max_changes, rules }
idle: { timeout, profiles, transitions }
```

### Configuration Classes (Pydantic)

```python
class RootConfig:
    logging: LoggingConfig
    midi: MidiConfig  
    mapping: Dict[str, Any]
    sequencer: SequencerConfig
    scales: List[str]
    mutation: MutationConfig
    idle: IdleConfig
```

### Runtime Parameter Flow

```
YAML → Pydantic Validation → Component Init → State Population → 
Runtime Updates → Parameter Changes → Component Responses
```

## External Dependencies

### Core Libraries

| Library | Purpose | Usage |
|---------|---------|-------|
| `mido` | MIDI I/O | Real-time MIDI message handling |
| `python-rtmidi` | MIDI backend | Low-level MIDI port access |
| `pydantic` | Configuration | Schema validation and parsing |
| `PyYAML` | Configuration | YAML file parsing |

### Threading Dependencies

| Component | Library | Purpose |
|-----------|---------|---------|
| Clock timing | `time.perf_counter()` | High-resolution monotonic time |
| Thread safety | `threading.RLock()` | Reentrant locking |
| Background tasks | `threading.Thread` | Concurrent execution |

## Error Handling Strategy

### Error Categories

**Configuration Errors**:
- Invalid YAML syntax → Application exit with clear message
- Missing required parameters → Pydantic validation error
- Invalid parameter ranges → Clamped to valid ranges with warning

**MIDI Errors**:
- Port connection failure → Exponential backoff retry
- Port disconnection → Attempt reconnection, continue operation
- Invalid MIDI messages → Log and ignore

**Runtime Errors**:
- State parameter validation failure → Clamp and warn
- Scale mapping errors → Fallback to chromatic scale
- Mutation boundary violations → Skip mutation, log warning

### Recovery Mechanisms

**Graceful Degradation**:
- MIDI output failure → Continue with NullMidiOutput
- Sequencer timing issues → Reduce complexity, maintain basic operation
- Mutation engine errors → Disable mutations, preserve core functionality

**Automatic Recovery**:
- MIDI port reconnection with exponential backoff
- Clock drift correction through accumulated error tracking
- State validation with automatic parameter clamping

## Testing Architecture

### Test Categories

**Unit Tests** (`tests/test_*.py`):
- Individual component functionality
- Parameter validation and clamping
- Scale mapping correctness
- Configuration parsing

**Integration Tests**:
- Full system with mock MIDI
- State change propagation
- Sequencer timing accuracy
- Idle mode transitions

**Performance Tests**:
- Latency measurement
- Memory leak detection
- Long-running stability (soak tests)
- CPU usage under load

### Test Infrastructure

```python
# Test environment setup
@pytest.fixture
def mock_config():
    return load_config("tests/test.yaml")

@pytest.fixture  
def test_state():
    reset_state()
    return get_state()

# Integration test pattern
def test_full_pipeline(mock_config, test_state):
    # Setup components
    sequencer = create_sequencer(test_state, mock_config.scales)
    action_handler = ActionHandler(test_state, sequencer)
    
    # Simulate MIDI input
    event = SemanticEvent(type="tempo", source="cc", value=64)
    action_handler.handle_semantic_event(event)
    
    # Verify state changes
    assert test_state.get("bpm") == expected_bpm
```

## Future Architecture Considerations

### Phase 8: Portal Integration
- Visual animation cue system
- Teensy communication protocol  
- Animation-music synchronization

### Phase 9: API & Metrics
- REST API for state inspection
- Prometheus metrics endpoint
- Real-time monitoring dashboard

### Phase 10: Advanced Features
- Preset save/load system
- Configuration hot-reload
- Advanced synthesis backend integration
- Multi-synth polyphonic voice management

### Scalability Considerations
- Plugin architecture for custom scales and patterns
- Distributed processing for complex generative algorithms
- External clock synchronization (Ableton Link)
- Network-based multi-device coordination

---

## Version History

- **v0.1-0.3**: Phases 1-2 (MIDI + Basic Sequencer)
- **v0.4**: Phase 3-4 (Scale Mapping + Probability)  
- **v0.5**: Phase 5 (Mutation Engine)
- **v0.6**: Phase 6 (Idle Mode)
- **v0.7**: Phase 7 (External Hardware Integration)
- **v0.8**: Phase 8 (Portal Integration) - *In Development*

For detailed implementation history, see `docs/PHASE*_IMPLEMENTATION.md` and `docs/ROADMAP.md`.
