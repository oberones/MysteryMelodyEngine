from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Any
import yaml

class MidiClockConfig(BaseModel):
    """MIDI clock synchronization configuration."""
    enabled: bool = False
    send_start_stop: bool = True
    send_song_position: bool = True

class CCProfileConfig(BaseModel):
    """CC profile configuration for external synths."""
    active_profile: str = "korg_nts1_mk2"  # Default to NTS-1 MK2
    parameter_smoothing: bool = True
    cc_throttle_ms: int = 10  # Minimum time between CC messages

class MidiConfig(BaseModel):
    input_port: str = "auto"
    output_port: Optional[str] = None  # Optional MIDI output port
    input_channel: int = 1
    output_channel: int = 1
    clock: MidiClockConfig = MidiClockConfig()
    cc_profile: CCProfileConfig = CCProfileConfig()

class SequencerConfig(BaseModel):
    steps: int = 8
    bpm: float = 110.0
    swing: float = 0.12
    density: float = 0.85
    root_note: int = Field(60, ge=0, le=127)  # MIDI note number for scale root (C4 = 60)
    gate_length: float = Field(0.8, ge=0.1, le=1.0)  # Note duration as fraction of step duration
    quantize_scale_changes: str = Field("bar", pattern=r"^(immediate|bar)$")
    # Phase 5.5 features
    step_pattern: Optional[str] = None
    direction_pattern: str = "forward"  # forward | backward | ping_pong | random | fugue | song
    voices: int = Field(3, ge=1, le=4)  # Number of voices for fugue mode (1-4)
    note_division: str = Field("sixteenth", pattern=r"^(whole|half|quarter|eighth|sixteenth)$")  # Note division per step

class MutationConfig(BaseModel):
    interval_min_s: int = 120
    interval_max_s: int = 240
    max_changes_per_cycle: int = 2

class IdleConfig(BaseModel):
    timeout_ms: int = 30000
    ambient_profile: str = "slow_fade"
    fade_in_ms: int = 4000
    fade_out_ms: int = 800
    smooth_bpm_transitions: bool = True
    bpm_transition_duration_s: float = 4.0

class SynthConfig(BaseModel):
    backend: str = Field("supercollider", pattern=r"^(supercollider)$")
    voices: int = 8

class LoggingConfig(BaseModel):
    level: str = Field("INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

class HidConfig(BaseModel):
    """HID device configuration for arcade buttons and joystick."""
    device_name: str = "Generic USB Joystick"
    button_mapping: Dict[int, str] = Field(default_factory=lambda: {i: "trigger_step" for i in range(10)})
    joystick_mapping: Dict[str, str] = Field(default_factory=lambda: {
        "up": "osc_a",
        "down": "osc_b", 
        "left": "mod_a",
        "right": "mod_b"
    })

class ApiConfig(BaseModel):
    enabled: bool = True
    port: int = 8080
    host: str = "0.0.0.0"
    log_level: str = "info"

class RootConfig(BaseModel):
    midi: MidiConfig = MidiConfig()
    hid: HidConfig = HidConfig()
    mapping: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    sequencer: SequencerConfig = SequencerConfig()
    scales: List[str] = Field(default_factory=lambda: ["major", "minor", "pentatonic"])
    mutation: MutationConfig = MutationConfig()
    idle: IdleConfig = IdleConfig()
    synth: SynthConfig = SynthConfig()
    logging: LoggingConfig = LoggingConfig()
    api: ApiConfig = ApiConfig()
    cc_profiles: Dict[str, Any] = Field(default_factory=dict)  # Custom CC profile definitions

    @field_validator("scales")
    @classmethod
    def non_empty_scales(cls, v):
        if not v:
            raise ValueError("At least one scale must be defined")
        return v


def load_config(path: str) -> RootConfig:
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return RootConfig(**data)

