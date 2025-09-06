# Project Specification (SPEC.md)

Title: Mystery Music Station (Interactive Generative Music Console)
Version: 0.1.0 (Spec)
Status: Living document (update alongside roadmap changes)
License: Apache-2.0

---
## 1. Purpose & Vision
Create a durable, low-latency, arcade-style generative music installation where physical interaction (buttons, knobs, joystick, switches) influences evolving musical structures and visual portal feedback. The Teensy firmware provides deterministic, reliable hardware → MIDI translation + RGB LED infinity portal animation; the Raspberry Pi engine provides generative logic, MIDI routing to external synths, mutation, and portal animation cues.

Primary Goals:
- Immediate tactile response (<10 ms perceptual latency for button notes)
- Long-running stability (≥8 hr daily operation)
- Modular generative layer (swap/extend rules without reflashing firmware)
- Clear separation of responsibilities (hardware vs. composition logic)
- Configurable external synth support with CC profile system

Non-Goals (v1):
- Streaming LED frame control from Pi
- Remote dynamic firmware reconfiguration (beyond compile-time constants)
- Complex visual UI

---
## 2. Hardware Summary (v1)
| Element | Count | Notes |
|---------|-------|-------|
| Arcade Buttons | 10 (B1–B10) | Digital, INPUT_PULLUP, MIDI Notes 60–69 |
| Pots | 6 (K1–K6) | Analog A0–A5 → CC 20–25 |
| Joystick | 4 directions | D22–D25 → CC 50–53 (edge pulse 127) |
| Toggles | 3 (S1–S3) | D26–D28 → CC 60–62 (latching 0/127) |
| RGB LED Infinity Portal | ~60 pixels | Data D14 (WS2812B/SK6812), pre-existing portal with animation programs |

Spare Pins Freed: D12, D13 (reserved future features)

---
## 3. MIDI Mapping (Canonical)
| Control | MIDI Type | Range / Value Semantics |
|---------|-----------|-------------------------|
| Buttons B1–B10 | NoteOn/NoteOff | Notes 60–69, fixed velocity 100, proper NoteOff (velocity 0) |
| Pots K1–K6 | ControlChange | CC 20–25, 0–127 after smoothing & deadband (≥2) |
| Joystick U/D/L/R | ControlChange | CC 50–53, single 127 pulse per actuation (no trailing 0) |
| Switches S1–S3 | ControlChange | CC 60–62, 127 on ON, 0 on OFF |
| Panic (future) | ControlChange or SysEx | TBD (deferred) |

Channel: 1 (Channel 2 reserved for future alternate semantic layer).

---
## 4. Latency & Performance Targets
| Path | Target |
|------|--------|
| Button press → MIDI dispatch | ≤5 ms typical, ≤10 ms worst |
| Pot move → CC emitted (above deadband) | ≤20 ms |
| Sequencer tick jitter (Pi) | <2 ms |
| MIDI → External Synth onset (Pi) | <10 ms typical |
| MCU main loop time | <1000 µs worst at 1 kHz |
| Portal animation frame update | 60–100 Hz |

---
## 5. Teensy Firmware Responsibilities
1. Scan inputs at 1 kHz.
2. Debounce digital inputs (5–8 ms window typical).
3. Smooth analog (EMA α≈0.25) + deadband (±2) + rate limiting (≥15 ms unless large delta).
4. Emit only state changes (no redundant CC / Note spam).
5. Provide RGB LED infinity portal animations using pre-existing portal code:
   - Animation Programs: spiral, pulse, wave, chaos, ambient, idle
   - Program switching via cues from Pi
   - BPM synchronization via rate control from Pi
   - Button/interaction visual feedback
   - Idle mode ambient animations (≤15% brightness cap after 30s inactivity)
   - Startup self-test (chase + color sweep + success blink)
6. Receive portal animation cues from Pi (program changes, rate sync, idle mode).
7. Maintain deterministic timing (avoid dynamic allocation in loop).
8. Offer minimal diagnostics (serial if DEBUG=1).

Out of Scope (v1): Config protocol, dynamic palette streaming, velocity sensing, SysEx control.

---
## 6. Raspberry Pi Engine Responsibilities
1. Receive and interpret MIDI events (mido + python-rtmidi).
2. Translate raw events → semantic actions (tempo, density, mode, scale change requests, etc.).
3. Sequencer core (steps, probability, density, swing, drift, bar-aligned scale changes).
4. Advanced pattern modes including:
   - Standard patterns: forward, backward, ping-pong, random sequences
   - Fugue mode: contrapuntal polyphonic composition with Bach-like principles
   - Song mode: structured compositions using common song forms (verse-chorus, AABA, 12-bar blues, etc.)
5. Mutation engine: scheduled mild parameter perturbations every 2–4 minutes.
6. Scale mapping: major/minor/pentatonic (extensible) – changes quantized to bar boundary.
7. External synth support via MIDI output with configurable CC profiles:
7. External synth support via MIDI output with configurable CC profiles:
   - Korg NTS1 MK2 (flagship synth with complete parameter mapping)
   - Generic Analog (standard subtractive synthesis parameters)
   - FM Synth (operator-based synthesis parameters)
   - Custom user-defined CC mappings via YAML configuration
8. Multi-synth MIDI output routing and latency optimization.
9. Idle mode detection (30s inactivity) → ambient parameter profile.
10. Portal animation control via cues sent back to Teensy:
10. Portal animation control via cues sent back to Teensy:
   - Program switching (spiral, pulse, wave, chaos, ambient, idle)
   - Rate synchronization with sequencer BPM
   - Idle/ambient mode visual transitions
   - Activity-based intensity control
11. Structured logging + (future) metrics endpoint.

Note: SuperCollider synthesis backend removed in favor of external hardware synths.

---
## 7. Portal Animation Programs & Cue System
The Teensy firmware integrates pre-existing infinity portal code with the following programs:

| Program | Description | Sync Behavior |
|---------|-------------|---------------|
| `spiral` | Rotating spiral patterns | BPM-synced rotation speed |
| `pulse` | Rhythmic pulsing | Beat-synchronized pulses |
| `wave` | Flowing wave patterns | Rate follows sequencer activity |
| `chaos` | Random/chaotic patterns | Intensity follows mutation events |
| `ambient` | Slow, peaceful patterns | Low intensity, slow rate |
| `idle` | Minimal ambient mode | Very low intensity (≤15% brightness) |

**Pi → Teensy Portal Cues:**
- Program change commands (switch between animation types)
- Rate synchronization (sync animation speed to sequencer BPM)
- Intensity control (based on sequencer density and activity)
- Idle mode transitions (automatic switch to ambient/idle programs)

**Portal Integration Points:**
- Button presses trigger visual feedback in current program
- Pot movements create brief intensity/color shifts
- Scale changes may trigger program transitions
- Mutation events can cause chaos program activation

---
## 8. Code Style & Conventions
### C++ (Teensy)
- Use `constexpr` arrays for pin & mapping definitions in `pins.h`.
- No dynamic allocation inside `loop()`.
- Prefix internal (file-static) helpers with `_` or place in anonymous namespace.
- Avoid floating point in hot paths; precompute scales / use integer math where feasible.
- Naming: `CamelCase` for types, `snake_case` for functions/variables, ALL_CAPS for tunable compile-time constants.
- Keep ISR usage minimal (prefer polling at 1 kHz unless a true interrupt is necessary—none planned v1).

### Python (Pi)
- **Virtual Environment**: All Python development and execution must be done within the `.venv` virtual environment in the `rpi/engine/` directory.
- **Dependency Management**: Use `pip install -r requirements.txt` within the activated virtual environment (from `rpi/engine/` directory).
- Use type hints (PEP484) & `pydantic` for config validation.
- Module naming: `snake_case.py`; classes `PascalCase`; constants `UPPER_SNAKE`.
- Prefer composition over inheritance; inject dependencies through constructors.
- Logging: `logging.getLogger(__name__)`; structured messages `key=value` style.
- Avoid blocking calls in timing loop—use non-blocking I/O / scheduling.

---
## 9. Configuration
Primary runtime config: `rpi/engine/config.yaml` (validated by `config.py`). Editable fields include sequencer parameters, mutation intervals, idle timings, external synth CC profiles, MIDI routing, portal animation settings, and logging level.

Firmware compile-time configuration: `config.h` (to be created) with constants specified in roadmap (e.g., `SCAN_HZ`, `DEBOUNCE_MS`).

---
## 10. Error Handling Policies
| Layer | Condition | Policy |
|-------|----------|--------|
| Teensy | Stuck button (held >5s) | Force NoteOff + log (DEBUG) |
| Teensy | Rapid pot jitter | Increase smoothing temporarily |
| Teensy | Portal animation overrun | Reduce frame rate / simplify current program |
| Pi | MIDI port disconnect | Retry with exponential backoff |
| Pi | External synth disconnect | Continue sequencing; attempt reconnection |
| Pi | Clock drift | Adjust next tick via accumulated error |
| Pi | Portal cue transmission failure | Log warning; continue without visual sync |

---
## 11. Testing Strategy Summary
Firmware:
- Manual serial diagnostics + logic analyzer spot checks
- Soak test 4 hr bench (simulate button & pot activity)

Pi Engine:
- **Environment**: All testing must be performed within the activated `.venv` virtual environment in `rpi/engine/`
- **Test Execution**: `cd rpi/engine && source .venv/bin/activate && pytest tests/`
- Unit tests (mapping, scale mapper, mutation bounds)
- Integration: simulated MIDI feed → expected synth event count / ordering
- Performance: tick jitter histogram logging
- Soak test 6–10 hr (target memory stability)

---
## 12. Versioning
- Firmware tags: `teensy-vMAJOR.MINOR.PATCH`
- Engine tags: `engine-vMAJOR.MINOR.PATCH`
- Increment PATCH for fixes, MINOR for new non-breaking features, MAJOR for breaking mappings/protocols.
- Keep `CHANGELOG.md` per component.

---
## 13. Security & Safety Considerations
- Run engine under non-root user; restrict network exposure (loopback or LAN only initially).
- Validate all config inputs; reject unknown keys.
- Avoid unbounded logs (rotate or size limit planned future step).
- Electrically: follow power best practices (handled in mechanical plan; included here for completeness).

---
## 14. Future Extensibility (Reserved)
- Channel 2 secret mode
- SysEx configuration or small binary protocol
- Palette streaming & cross-fade scenes
- External clock sync (Ableton Link / MIDI clock)
- Multi-synth polyphonic voice management
- Advanced portal visual effects (cross-fade scenes, palette streaming)
- Additional sensors (freed pins D12,D13)
- Preset management and pattern recording
- Custom song patterns and compositional templates
- Advanced voice leading algorithms for song mode
- Song pattern learning from user input

---
## 15. AI Agent Collaboration Guidelines
This spec exists to make automated assistance consistent.

When extending firmware:
- Do NOT change pin allocations unless spec updated.
- Preserve public headers (`pins.h`, upcoming `config.h`) structure; append rather than reorder unless necessary.
- When adding portal animation programs, ensure they integrate with existing cue system.
- When adding constants, group by function (timing, portal, MIDI).
- Add tests or diagnostic notes for new behavior.

When extending Pi engine:
- **CRITICAL**: Always activate the virtual environment first: `cd rpi/engine && source .venv/bin/activate`
- **Dependencies**: Install/update requirements within venv: `pip install -r requirements.txt`
- **Testing**: Run tests within venv: `pytest tests/`
- **Execution**: Run engine within venv: `python src/main.py --config config.yaml`
- Keep config schema backward compatible (add new keys with defaults).
- Any new semantic action must map cleanly from existing MIDI ranges or use reserved CC after discussion (prefer Pi-side remapping before modifying firmware mapping).
- Maintain separation: mapping layer should not contain direct synthesis logic.
- When adding external synth profiles, follow the established CC profile system in config.yaml.
- Portal animation cues should remain lightweight and semantic (program/rate/intensity) rather than frame-level control.

General:
- Confirm impact footprint (lines touched, behavioral changes) in PR summary.
- Avoid introducing heavy dependencies; prefer standard library or listed allowed libs.
- Ensure latency targets still met (mention measurement if timing path changed).

Ask for Clarification If:
- New hardware peripherals proposed.
- MIDI mapping expansion collides with existing note/CC usage.
- Portal animation requirements exceed existing program capabilities.
- External synth profiles require non-standard MIDI implementation.

Assumptions Allowed Without Asking:
- Minor refactors improving readability (no behavior change).
- Adding lightweight inline helper functions.
- Expanding scale list (non-breaking) if triggered by existing scale_select mechanism.
- Adding new external synth CC profiles following established pattern.
- Adding new portal animation programs that integrate with existing cue system.

---
## 16. Commit & PR Conventions
- Conventional Commit style recommended: `feat(fw): add joystick pulse handling` / `fix(engine): clamp density`.
- Reference spec section for structural changes (e.g., "Spec §8 LED mapping updated").
- Include latency or CPU impact note if touching timing-critical code.

---
## 17. Glossary
| Term | Definition |
|------|------------|
| Density | Global probability scaler (0–1) applied to step triggers |
| Drift | Slow BPM modulation parameter |
| Ambient Mode | Reduced-intensity idle behavior after inactivity |
| Mutation Cycle | Scheduled batch of automatic parameter tweaks |
| Semantic Action | Logical intent derived from raw MIDI (e.g., set_tempo) |
| CC Profile | Synth-specific mapping of parameters to MIDI CC numbers |
| Portal Program | Pre-defined animation pattern for the infinity portal |
| Portal Cue | High-level command sent from Pi to Teensy for visual control |

---
## 18. Acceptance Checklist (Spec Compliance)
Firmware v1 must:
- Emit only defined MIDI set (Notes 60–69, CC 20–25, 50–53, 60–62)
- Integrate pre-existing infinity portal animation code
- Support portal program switching and BPM synchronization via Pi cues
- Obey latency & brightness caps
- Provide startup self-test

Engine v1 must:
- Honor bar-aligned scale changes
- Produce generative notes with probability & mutation
- Support external synth MIDI output with configurable CC profiles
- Send portal animation cues to Teensy for visual synchronization
- Enforce idle profile after 30s inactivity

---
## 19. Change Management
Update this file when:
- Hardware count changes (buttons, portal, controls) -> Section 2/7
- Mapping changes -> Sections 3/5/7
- Performance targets revised -> Section 4
- New external synth profiles or portal programs added -> Sections 6/7/14
- New protocols or backends added -> Sections 6/14

---
End of SPEC.md
