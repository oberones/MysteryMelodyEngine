# Raspberry Pi Generative Engine Software Roadmap

Target Platform: Raspberry Pi 4 (2–4 GB RAM)
Primary Role: Receive USB MIDI from Teensy, apply mapping + transformation + generative logic, synthesize / route audio, emit minimal LED cue messages to Teensy, expose logging.

Decided Tech Stack (per clarifications):
- Core Language: Python 3.11 (supervision, logic, routing)
- MIDI I/O: `mido` + `python-rtmidi`
- Audio Synthesis Backend: SuperCollider (`scsynth`) driven via OSC (`python-osc`)
- LED Control: Firmware (Teensy) owns animations; Pi sends only abstract cue events (note, param, mode, idle enter/exit)
- Optional future backends (PD/pyo) deferred

---
## 1. Goals & Non-Goals
### Core Goals
- Deterministic real-time mapping from incoming MIDI events to generative engine state changes.
- Layered generative architecture (input layer, state model, sequencer, probability & mutation, scale mapper, synthesis drivers, LED event bus).
- Hot-reload / rapid iteration of rules & mappings (editable config / YAML / JSON / Python plugin modules).
- Robust logging + introspection (metrics & state snapshot endpoints).
- Idle detection & adaptive behavior (ambient mode after 30 s inactivity).
- Modular audio backend abstraction (swap PD, SuperCollider, Python-native synthesis).
- **Initial version supports a single monophonic external hardware synth.**

### Non-Goals (Push to Firmware or Future)
- Physical input scanning (Teensy handles low-level hardware)
- Heavy GUI (maybe a lightweight status endpoint later)
- Persistent user content management (beyond simple presets / JSON state)
- High-bandwidth LED frame streaming (handled by Teensy animations)
- **Polyphony and multi-instrument support (future goals).**

---
## 2. High-Level Architecture
```
                +---------------------------+
USB MIDI  --->  |  MIDI In Adapter          |
                +------------+--------------+
                             |
                             v
                +---------------------------+
                |  Event Router / Mapper    |  (maps raw Notes/CC -> semantic intents)
                +------------+--------------+
                             |
                             v
                +---------------------------+
                |  State Model / Parameter  |  (tempo, scale, density, modes, flags)
                +------------+--------------+
                             | (queries)
                             v
                +---------------------------+
                | Sequencer Core (steps)    |  (probability, drift, mutation)
                +------------+--------------+
                             |
                  +----------+-----------+
                  |                      |
                  v                      v
        +----------------+      +-------------------+
        | Scale Mapper   |      | Mutation Engine   |
        +--------+-------+      +---------+---------+
                 |                        |
                 v                        |
        +----------------+                |
        | Note Stream    |<---------------+
        +--------+-------+
                 |
                 v
        +----------------+        +------------------+
        | Synth Adapter  |  --->  | Audio Backend(s) |
        +----------------+        +------------------+
                 |
                 v
        +----------------+
        | LED Event Bus  |  (emit abstract LED cues -> Teensy or local LEDs)
        +----------------+

        +----------------+
        | Monitoring API | (web / CLI / OSC / metrics)
        +----------------+
```

---

## 3. Module Breakdown
| Module | Responsibility | Key Concepts | Deliverables |
|--------|----------------|--------------|--------------|
| `midi_in` | Receive MIDI from Teensy | Port discovery, event queue | Python module |
| `midi_out` | Send MIDI to external synths | Multi-port routing, latency optimization | MIDI interface |
| `router` | Map raw Note/CC -> semantic actions | Config-driven rules | YAML/JSON loader |
| `state` | Central parameter store | Observable pattern, profile switching | State management |
| `sequencer` | Step timing, generative patterns | Clock, probability, mutations | Pattern engine |
| `scale_mapper` | Musical scale transformations | Scale definitions, quantization | Music theory |
| `cc_profiles` | **NEW** Synth-specific CC mappings | Profile definitions, parameter scaling | Synth abstraction |
| `portal_cues` | **NEW** Visual animation control | Cue generation, Teensy communication | Visual sync |
| `mutation` | Automated parameter evolution | Weighted scheduling, musical bounds | Generative logic |
| `idle_manager` | Detect inactivity & ambient mode | Event timestamps, profile switching | Adaptive behavior |
| `config` | Load + validate configuration | Schema validation (`pydantic`) | Config management |
| `logging/metrics` | Structured logs + counters | `logging`, `prometheus_client` | Exposed metrics endpoint |
| `api` | Optional web/OSC interface | FastAPI / aiohttp + OSC server | Control + introspection |
| `persistence` | Preset save/load (optional) | JSON snapshot | Save/restore functions |
| `cli` | Launch / manage processes | Argparse / Typer | `main.py` |
| `tests` | Unit/integration tests | Pytest | Test suite |

---
## 4. Configuration Model (Draft)
`config.yaml` example snippet (updated for SuperCollider + bar-quantized scale changes):
```yaml
midi:
  input_port: auto
  output_port: auto  # Optional MIDI output port
  input_channel: 10   # Channel for incoming MIDI (1-16)
  output_channel: 1   # Channel for outgoing MIDI (1-16)

# Synth-specific CC parameter mappings
cc_profiles:
  korg_nts1_mk2:
    name: "Korg NTS1 MK2"
    parameters:
      filter_cutoff: {cc: 21, range: [0, 127], curve: "linear"}
      filter_resonance: {cc: 22, range: [0, 127], curve: "linear"}
      eg_attack: {cc: 23, range: [0, 127], curve: "exponential"}
      eg_decay: {cc: 24, range: [0, 127], curve: "exponential"}
      lfo_rate: {cc: 25, range: [0, 127], curve: "logarithmic"}
      osc_type: {cc: 20, range: [0, 127], curve: "stepped", steps: 8}
      
  generic_analog:
    name: "Generic Analog Synth"
    parameters:
      filter_cutoff: {cc: 74, range: [0, 127]}
      filter_resonance: {cc: 71, range: [0, 127]}
      envelope_attack: {cc: 73, range: [0, 127]}
      envelope_decay: {cc: 75, range: [0, 127]}

# Input mapping (from Teensy)
mapping:
  buttons:
    "60-69": trigger_step
  ccs:
    "20": active_profile_param_1  # Maps to filter_cutoff in active profile
    "21": active_profile_param_2  # Maps to filter_resonance in active profile
    "22": active_profile_param_3  # etc.
    "23": swing
    "24": density
    "25": master_volume
    "50": sequence_length
    "51": scale_select
    "52": cc_profile_select  # Switch between synth profiles
    "53": portal_program
    "60": mode
    "61": mutation_rate
    "62": drift

sequencer:
  steps: 8
  bpm: 110
  swing: 0.12
  density: 0.85
  gate_length: 0.8              # Note duration as fraction of step duration (0.1-1.0)
  quantize_scale_changes: bar   # enforce at bar boundary

scales: [major, minor, pentatonic]
mutation:
  interval_min_s: 120
  interval_max_s: 240
  max_changes_per_cycle: 2
idle:
  timeout_ms: 30000
  ambient_profile: slow_fade
  fade_in_ms: 4000
  fade_out_ms: 800
logging:
  level: INFO
api:
  enabled: true
  port: 8080
```

---
## 5. Data Flow (Event Lifecycle)
1. MIDI event arrives (Note/CC).
2. Router consults mapping config → emits semantic action (e.g., `ACTION_SET_TEMPO`, `ACTION_TRIGGER_GATE`).
3. State updates value (with validation + range clamp) OR sequencer receives trigger.
4. Sequencer generates note events on tick boundaries (honoring probability, density, drifted clock).
5. Scale mapper adjusts pitch set.
6. Synth adapter schedules audio backend calls.
7. LED bus receives summarised cues (e.g., `pot_move`, `mode_change`, `note_trigger`).
8. Metrics/logging record event latencies & counts.

---
## 6. Clock & Timing Strategy
- Master clock derived from BPM → tick interval = 60000 / (BPM * PPQ).
- Use high-resolution monotonic timer & drift correction (accumulate fractional remainder).
- Swing: alter timing of even/odd beats by ± swing factor.
- Drift parameter: Slowly modulate BPM within ±X% envelope.

---
## 7. Mutation Engine
- Scheduler picks random time in `[interval_min_s, interval_max_s]`.
- Select up to `max_changes_per_cycle` parameters based on weighted categories.
- Apply small bounded delta (e.g., density ±0.05) with clamp.
- Emit event log + LED cue.

---
## 8. Idle Mode
- Track last interaction timestamp (any incoming semantic action).
- If `now - last_interaction >= idle.timeout_ms`: switch to ambient profile (e.g., reduce density, shift scale to pentatonic airy pad, enable long reverb, LED slow fade).
- Exit idle on any new interaction; revert to saved active profile.

---
## 9. CC Profile System
### Profile Structure
```python
@dataclass
class CCParameter:
    cc: int
    range: tuple[int, int] = (0, 127)
    curve: str = "linear"  # linear, exponential, logarithmic, stepped
    steps: Optional[int] = None  # for stepped parameters

@dataclass 
class CCProfile:
    name: str
    parameters: dict[str, CCParameter]
    
    def map_parameter(self, param_name: str, value: float) -> tuple[int, int]:
        """Map 0.0-1.0 value to (CC_number, CC_value) for this synth"""
```

### Supported Profiles
- **Korg NTS1 MK2:** Complete parameter mapping for oscillator, filter, envelope, LFO
- **Generic Analog:** Standard subtractive synthesis parameters
- **FM Synth:** Operator-based synthesis parameters
- **Custom:** User-defined mappings via YAML configuration

---
## 10. Portal Animation System
### Cue Types
```python
class PortalCue:
    program: str        # Animation program name
    intensity: float    # 0.0-1.0 animation intensity
    rate: float         # Animation speed multiplier
    color_hue: float    # 0.0-1.0 hue shift
    sync_bpm: bool      # Sync animations to sequencer BPM
```

### Communication Protocol
- **Serial/MIDI back to Teensy:** Lightweight binary messages
- **Programs:** `spiral`, `pulse`, `wave`, `chaos`, `ambient`, `idle`
- **Rate Sync:** Portal animations sync to sequencer BPM and activity level
- **Idle Mode:** Automatic switch to ambient portal program during idle

---
## 10. Logging & Metrics
- Structured logging: JSON lines (`timestamp`, `event`, `detail`).
- Metrics: Prometheus endpoint `/metrics` (event counts, queue sizes, tick latency histogram, mutation count, idle transitions).
- Performance budget: MIDI → synth call latency target < 10 ms typical.

---
## 11. Error Handling & Resilience
| Error | Detection | Handling |
|-------|-----------|----------|
| MIDI port disconnect | Exception on read | Attempt re-open (exponential backoff) |
| Backend crash (PD/SC process) | Process exit code | Supervisor restarts backend; if >N failures escalate |
| Clock overruns | Tick latency log > threshold | Adaptive degrade (reduce voice polyphony) |
| Config parse error | Validation fail | Abort with actionable message |
| High CPU > 85% sustained | Periodic system stats | Throttle mutation & LED events |

---
## 12. Testing Strategy
### Unit
- Mapping resolution from sample config
- Scale mapping correctness (expected pitch sets)
- Mutation rule boundaries

### Integration
- Simulated MIDI stream → verify resulting synth calls & state changes
- Idle transition & recovery
- Clock accuracy over 10 min (<0.1% drift)

### Performance
- Stress test CC spam (simulate rapid pot moves) → ensure bounded queue size
- Measure end-to-end latency (timestamp injection & audio callback scheduling)

### Soak
- 6 hr run with random event injection; ensure no memory leak (monitor RSS), stable CPU usage.

---
## 13. Development Phases & Milestones
### Phase 0: Scaffold
- [X] Create `rpi/engine/` structure, `pyproject.toml` or `requirements.txt`.
- [X] Implement config loader & logging skeleton.

### Phase 1: MIDI Input & Routing
- [X] Open port, map raw Note/CC to semantic events (print logs).

### Phase 2: State Model + Sequencer Skeleton
- [X] Core state container with change listeners.
- [X] Sequencer tick with static BPM & step playback (no probability yet).

### Phase 3: Optional MIDI Output
- [X] Optional MIDI output allows for messages to be sent to the attached MIDI device.

### Phase 4: Scale & Probability
- [X] Add probability per step, density gating.
- [X] Add scale mapping.
- [X] Add quantization for scale changes.

### Phase 5: Mutation Engine
- [X] Implement mutation engine to periodically change parameters.
- [X] Add BPM drift envelope + mutation scheduler.
- [X] Logging of each mutation.

### Phase 5.5: Enhanced Probability & Rhythm Patterns
- [X] Implement per-step probability arrays instead of global note_probability.
- [X] Add configurable step patterns instead of hardcoded even-step activation.
- [X] Add velocity variation based on probability values.
- [X] Add direction patterns for sequencer playback (forward, backward, ping-pong, random).
- [X] Add configurable note duration (gate_length) as fraction of step duration.

### Phase 6: Idle Mode
- [X] Implement idle mode detection and handling.
- [X] Mutations should be enabled when the system is idle and disabled when midi input is received

### Phase 7: External Hardware Integration
- [X] MIDI clock synchronization options
- [X] Support for multiple MIDI CC profiles (default support for NTS MKII parameters)
- [X] Simplified MIDI note scheduling (latency optimizer removed for stability)

### Phase 8: Portal Integration
- [ ] Portal cue generation system
- [ ] Serial communication with Teensy portal
- [ ] Visual-musical synchronization
- [ ] Portal program selection and control

### Phase 8: API & Metrics
- [ ] HTTP/JSON endpoint for current state & mutation history.
- [ ] Prometheus metrics endpoint.

### Phase 9: Hardening & Soak
- [ ] Reconnect logic, CPU/memory monitors.
- [ ] Long-run soak test with performance tuning.
- [ ] Create/run performance and stress tests to ensure reliability.

### Phase 10: Polish
- [ ] Preset save/load.
- [ ] Config hot-reload (SIGHUP or file watcher).
- [ ] CLI flags for overrides.
- [ ] Enable logging to file (/var/log/rpi-engine.log)

---
## 14. Directory Structure (Proposed)
```
rpi-engine/
  src/
    main.py
    config.py
    midi_in.py
    router.py
    state.py
    sequencer.py
    scale_mapper.py
    mutation.py
    synth_adapter.py
    backend_pyo.py
    backend_pd.py
    backend_sc.py
    led_bus.py
    idle.py
    logging_setup.py
    metrics.py
    api.py
    util/time.py
  tests/
    test_mapping.py
    test_scale.py
    test_mutation.py
    test_sequencer.py
  config.yaml (sample)
requirements.txt or pyproject.toml
```

---
## 15. Portal Integration Details
### Teensy Communication
```python
class PortalInterface:
    def send_cue(self, program: str, intensity: float, rate: float):
        """Send animation cue to Teensy portal"""
        
    def set_bpm_sync(self, bpm: float):
        """Sync portal animation rate to sequencer BPM"""
        
    def enter_idle_mode(self):
        """Switch portal to ambient/idle animation"""
```

### Animation Synchronization
- **Beat Sync:** Portal pulses and flashes sync to sequencer beats
- **Parameter Coupling:** Portal color and intensity reflect filter cutoff, resonance
- **Activity Response:** Animation intensity follows sequencer density and mutation activity
- **Idle Transition:** Smooth fade to ambient patterns during idle mode

---
## 16. External Synth Optimization
### MIDI Performance
- **Direct Hardware MIDI:** Minimize USB-MIDI latency where possible
- **CC Throttling:** Intelligent parameter smoothing to avoid MIDI flooding
- **Note Priority:** Ensure note events take priority over CC updates
- **Multi-Port:** Support multiple external synths simultaneously

### Synth-Specific Features
- **NTS1 MK2 Presets:** Automatically recall and modify onboard presets
- **Parameter Scaling:** Optimal CC curves for each synth's parameter response
- **Voice Management:** Intelligent note allocation for polyphonic external synths

---
## 17. Performance Targets
| Metric | Target |
|--------|--------|
| MIDI event handling latency | < 5 ms avg |
| Sequencer jitter | < 2 ms |
| CPU usage (normal) | < 30% |
| Memory footprint (RSS) | < 300 MB (Python + SC bridge) |
| Continuous uptime stability | ≥ 10 hr soak (>= 8 hr requirement + margin) |

---
## 18. Security / Safety Considerations
- Run engine as non-root.
- Validate config input (schema) before applying.
- Rate-limit external API mutation endpoints.
- Avoid blocking calls in audio scheduling path.

---
## 19. Deployment & Operation
- Systemd service file (`mystery_engine.service`) to auto-start.
- Log rotation with `logrotate` or built-in max-size rotation.
- Optional watchdog (systemd Restart=on-failure).

---
## 20. Versioning & Release
- Semantic versioning (engine separate from firmware).
- Tag: `engine-v0.1.0` once Phase 5 complete & stable.
- CHANGELOG entries by feature area.

---
## 21. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Python GC pauses cause jitter | Audio glitches | Keep audio real-time work minimal; offload synthesis to external engine (PD/SC) |
| Excessive MIDI -> event backlog | Latency | Bounded queue + drop lowest priority param spam |
| Mutation produces unpleasant extremes | Bad UX | Clamp ranges + weighted selection |
| Scale changes mid-phrase sound harsh | Disjoint feel | Option: quantize scale changes at bar boundaries |
| Idle mode flaps | Visual/audio noise | Hysteresis (exit only after 1s active) |

---
## 22. Testing Strategy (Updated)
### Hardware Integration
- **Multi-Synth Testing:** Verify MIDI routing to multiple external devices
- **Portal Sync Testing:** Visual-musical synchronization accuracy
- **Latency Measurement:** End-to-end timing from Teensy input to synth output
- **Profile Switching:** Seamless transitions between different synth configurations

### Musical Testing
- **Scale Accuracy:** Verify musical intervals and quantization
- **Generative Quality:** Assess mutation and pattern generation musicality
- **Performance Stability:** Extended sessions with complex external setups
