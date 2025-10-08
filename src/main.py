import time
import logging
import argparse
import threading
from typing import Optional
from dataclasses import dataclass
from config import load_config
from router import Router
from midi_in import MidiInput
from hybrid_input import HybridInput
from midi_out import MidiOutput, NullMidiOutput
from events import SemanticEvent
from logging_utils import configure_logging
from state import get_state, reset_state
from sequencer import create_sequencer, NoteEvent
from action_handler import ActionHandler
from mutation import create_mutation_engine
from idle import create_idle_manager
from cc_profiles import load_custom_profiles
from note_utils import format_note_with_number, format_rest
from api_server import create_api_server


@dataclass
class ScheduledNoteOff:
    """Represents a scheduled note off event."""
    note: int
    channel: int
    timestamp: float


class NoteScheduler:
    """Handles scheduling of note off events for proper MIDI note timing."""
    
    def __init__(self, midi_output):
        self.midi_output = midi_output
        self._scheduled_notes: list[ScheduledNoteOff] = []
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the note scheduler thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._scheduler_thread, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the note scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
    
    def schedule_note_off(self, note: int, channel: int, delay: float):
        """Schedule a note off event after the specified delay."""
        timestamp = time.time() + delay
        scheduled = ScheduledNoteOff(note, channel, timestamp)
        
        with self._lock:
            self._scheduled_notes.append(scheduled)
            # Keep list sorted by timestamp for efficiency
            self._scheduled_notes.sort(key=lambda x: x.timestamp)
    
    def _scheduler_thread(self):
        """Main scheduler thread that processes note off events."""
        while self._running:
            current_time = time.time()
            notes_to_remove = []
            
            with self._lock:
                # Process all notes that are due
                for scheduled in self._scheduled_notes:
                    if scheduled.timestamp <= current_time:
                        # Send note off
                        self.midi_output.send_note_off(scheduled.note, 0, scheduled.channel)
                        notes_to_remove.append(scheduled)
                    else:
                        # List is sorted, so we can break here
                        break
                
                # Remove processed notes
                for note in notes_to_remove:
                    self._scheduled_notes.remove(note)
            
            # Sleep for a short time to avoid busy waiting
            time.sleep(0.001)  # 1ms resolution


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Mystery Music Engine Phase 2")
    p.add_argument("--config", default="config.yaml", help="Path to config YAML")
    p.add_argument("--log-level", default=None, help="Override log level (DEBUG/INFO/...)")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None):
    args = parse_args(argv)
    cfg = load_config(args.config)
    level = args.log_level or cfg.logging.level
    configure_logging(level)
    log = logging.getLogger("engine")
    log.info("engine_start phase=7 version=0.7.0")
    log.debug("config_loaded json=%s", cfg.model_dump_json())

    # Log all configuration values for transparency
    log.info("=== CONFIGURATION SUMMARY ===")
    log.info(f"config_file={args.config}")
    log.info(f"log_level={level}")
    
    # MIDI Configuration
    log.info(f"midi_input_port={cfg.midi.input_port}")
    log.info(f"midi_output_port={cfg.midi.output_port}")
    log.info(f"midi_input_channel={cfg.midi.input_channel}")
    log.info(f"midi_output_channel={cfg.midi.output_channel}")
    
    # HID Configuration
    log.info(f"hid_device_name={cfg.hid.device_name}")
    log.info(f"hid_button_mapping={cfg.hid.button_mapping}")
    log.info(f"hid_joystick_mapping={cfg.hid.joystick_mapping}")
    
    # Phase 7: MIDI Clock Configuration
    log.info(f"midi_clock_enabled={cfg.midi.clock.enabled}")
    log.info(f"midi_clock_send_start_stop={cfg.midi.clock.send_start_stop}")
    log.info(f"midi_clock_send_song_position={cfg.midi.clock.send_song_position}")
    
    # Phase 7: CC Profile Configuration  
    log.info(f"cc_profile_active={cfg.midi.cc_profile.active_profile}")
    log.info(f"cc_profile_smoothing={cfg.midi.cc_profile.parameter_smoothing}")
    log.info(f"cc_profile_throttle_ms={cfg.midi.cc_profile.cc_throttle_ms}")
    
    # Sequencer Configuration
    log.info(f"sequencer_steps={cfg.sequencer.steps}")
    log.info(f"sequencer_bpm={cfg.sequencer.bpm}")
    log.info(f"sequencer_swing={cfg.sequencer.swing}")
    log.info(f"sequencer_density={cfg.sequencer.density}")
    log.info(f"sequencer_root_note={format_note_with_number(cfg.sequencer.root_note)}")
    log.info(f"sequencer_gate_length={cfg.sequencer.gate_length}")
    log.info(f"sequencer_quantize_scale_changes={cfg.sequencer.quantize_scale_changes}")
    
    # Phase 5.5 Sequencer Features
    log.info(f"sequencer_step_pattern={cfg.sequencer.step_pattern}")
    log.info(f"sequencer_direction_pattern={cfg.sequencer.direction_pattern}")
    log.info(f"sequencer_voices={cfg.sequencer.voices}")
    
    # Scales
    log.info(f"available_scales={cfg.scales}")
    
    # Mutation Configuration
    log.info(f"mutation_interval_min_s={cfg.mutation.interval_min_s}")
    log.info(f"mutation_interval_max_s={cfg.mutation.interval_max_s}")
    log.info(f"mutation_max_changes_per_cycle={cfg.mutation.max_changes_per_cycle}")
    
    # Idle Configuration
    log.info(f"idle_timeout_ms={cfg.idle.timeout_ms}")
    log.info(f"idle_ambient_profile={cfg.idle.ambient_profile}")
    log.info(f"idle_fade_in_ms={cfg.idle.fade_in_ms}")
    log.info(f"idle_fade_out_ms={cfg.idle.fade_out_ms}")
    
    # Synth Configuration
    log.info(f"synth_backend={cfg.synth.backend}")
    log.info(f"synth_voices={cfg.synth.voices}")
    
    # API Configuration
    log.info(f"api_enabled={cfg.api.enabled}")
    log.info(f"api_port={cfg.api.port}")
    
    # Mapping Configuration Summary
    button_mappings = list(cfg.mapping.get('buttons', {}).keys()) if cfg.mapping else []
    cc_mappings = list(cfg.mapping.get('ccs', {}).keys()) if cfg.mapping else []
    log.info(f"button_mappings={button_mappings}")
    log.info(f"cc_mappings={cc_mappings}")
    log.info("=== END CONFIGURATION ===")

    # Load custom CC profiles from configuration
    load_custom_profiles(cfg.model_dump())

    # Initialize state and sequencer
    state = get_state()
    
    # Initialize state from config
    state.update_multiple({
        'bpm': cfg.sequencer.bpm,
        'swing': cfg.sequencer.swing,
        'density': cfg.sequencer.density,
        'sequence_length': cfg.sequencer.steps,
        'root_note': cfg.sequencer.root_note,
        'gate_length': cfg.sequencer.gate_length,
        'voices': cfg.sequencer.voices,
        'smooth_idle_transitions': cfg.idle.smooth_bpm_transitions,
        'idle_transition_duration_s': cfg.idle.bpm_transition_duration_s,
    }, source='config')
    
    # Create sequencer
    sequencer = create_sequencer(state, cfg.scales)
    
    # Apply Phase 5.5 configuration if present
    if cfg.sequencer.step_pattern:
        try:
            pattern = sequencer.get_pattern_preset(cfg.sequencer.step_pattern)
            sequencer.set_step_pattern(pattern)
            log.info(f"applied_step_pattern={cfg.sequencer.step_pattern}")
        except Exception as e:
            log.warning(f"failed_to_apply_step_pattern={cfg.sequencer.step_pattern} error={e}")
    
    if cfg.sequencer.direction_pattern and cfg.sequencer.direction_pattern != 'forward':
        try:
            sequencer.set_direction_pattern(cfg.sequencer.direction_pattern)
            log.info(f"applied_direction_pattern={cfg.sequencer.direction_pattern}")
        except Exception as e:
            log.warning(f"failed_to_apply_direction_pattern={cfg.sequencer.direction_pattern} error={e}")
    
    # Initialize MIDI output (optional)
    midi_output = MidiOutput.create(cfg.midi.output_port, cfg.midi.output_channel)
    if midi_output:
        log.info(f"MIDI output enabled on port: {cfg.midi.output_port}")
    else:
        midi_output = NullMidiOutput()
        log.info("MIDI output disabled")

    # Create action handler
    action_handler = ActionHandler(state, sequencer)
    
    # Phase 7: Initialize external hardware manager
    from external_hardware import ExternalHardwareManager
    external_hardware = ExternalHardwareManager(midi_output, cfg)
    external_hardware.start()
    action_handler.set_external_hardware(external_hardware)
    log.info("External hardware manager initialized and connected")
    
    # Create mutation engine
    mutation_engine = create_mutation_engine(cfg.mutation, state)
    
    # Auto-integrate NTS-1 plugin if NTS-1 CC profile is active
    if cfg.midi.cc_profile.active_profile == "korg_nts1_mk2":
        try:
            from nts1_mutation_plugin import setup_nts1_mutations
            
            # Determine style from config or use default
            config_dict = cfg.model_dump()
            nts1_config = config_dict.get("mutation", {}).get("nts1_plugin", {})
            style = nts1_config.get("style", "default")
            replace_default = nts1_config.get("replace_default_rules", True)
            
            # Clear default rules if requested
            if replace_default:
                mutation_engine._rules.clear()
                log.info("Cleared default mutation rules for NTS-1 plugin")
            
            # Set up NTS-1 mutations
            setup_nts1_mutations(mutation_engine, state, style)
            log.info(f"NTS-1 mutation plugin auto-loaded (style={style}, replace_default={replace_default})")
            
        except ImportError as e:
            log.warning(f"NTS-1 plugin not available: {e}")
        except Exception as e:
            log.error(f"Failed to auto-load NTS-1 plugin: {e}")
    
    # Create idle manager
    idle_manager = create_idle_manager(cfg.idle, state)
    
    # Connect idle manager to action handler and mutation engine
    action_handler.set_idle_manager(idle_manager)
    mutation_engine.set_idle_manager(idle_manager)

    # Initialize note scheduler for proper note off timing
    note_scheduler = NoteScheduler(midi_output)
    note_scheduler.start()    # Set up note callback for sequencer-generated notes
    def handle_note_event(note_event: NoteEvent):
        # Format note information with both name and number
        if note_event.note == -1:
            note_info = format_rest()
        else:
            note_info = format_note_with_number(note_event.note)
        
        log.info(f"note_event note={note_info} velocity={note_event.velocity} step={note_event.step} duration={note_event.duration:.3f}")
        
        # Send directly via MIDI output (no latency optimizer)
        if midi_output and midi_output.is_connected and note_event.note != -1:
            midi_output.send_note_on(note_event.note, note_event.velocity, cfg.midi.output_channel)
            note_scheduler.schedule_note_off(note_event.note, cfg.midi.output_channel, note_event.duration)
        
        # TODO Phase 4+: Send to synthesis backend
    
    sequencer.set_note_callback(handle_note_event)
    action_handler.set_note_callback(handle_note_event)
    
    # Set up semantic event handling
    def handle_semantic(evt: SemanticEvent):
        log.info("semantic %s", evt.log_str())
        action_handler.handle_semantic_event(evt)

    router = Router(cfg, handle_semantic)
    
    # Initialize API server if enabled
    api_server = create_api_server(cfg, handle_semantic)
    if api_server:
        api_server.start()
        log.info(f"API server started on port {cfg.api.port}")
    
    # Use hybrid input system for both HID and MIDI inputs
    try:
        hybrid_input = HybridInput.create_from_config(cfg, router.route, handle_semantic)
        hybrid_input.start()
        log.info("Hybrid input system started (HID + MIDI)")
    except Exception as e:
        log.error("hybrid_input_failed error=%s", e)
        return 2

    # Start sequencer
    sequencer.start()
    log.info("sequencer_started")
    
    # Start mutation engine
    mutation_engine.start()
    log.info("mutation_engine_started")
    
    # Start idle manager
    idle_manager.start()
    log.info("idle_manager_started")

    try:
        while True:
            time.sleep(1.0)
            # Check for mutations periodically (alternative to threading)
            mutation_engine.maybe_mutate()
            
            # Log current state periodically for debugging
            if log.isEnabledFor(logging.DEBUG):
                current_state = state.get_all()
                mutation_stats = mutation_engine.get_stats()
                idle_status = idle_manager.get_status()
                log.debug(f"state_snapshot {current_state}")
                log.debug(f"mutation_stats {mutation_stats}")
                log.debug(f"idle_status {idle_status}")
    except KeyboardInterrupt:
        log.info("shutdown signal=keyboard_interrupt")
    finally:
        try:
            sequencer.stop()
            mutation_engine.stop()
            idle_manager.stop()
            external_hardware.stop()  # Stop external hardware manager
            note_scheduler.stop()
            hybrid_input.stop()  # Stop hybrid input system
            if api_server:
                api_server.stop()  # Stop API server
            if midi_output:
                midi_output.close()
        except Exception:  # noqa: broad-except
            log.exception("shutdown_error")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
