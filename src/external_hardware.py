"""External hardware integration manager for Phase 7.

Coordinates CC profiles, MIDI clock, and latency optimization for 
seamless integration with external synthesizers and hardware.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, Callable
import logging
from dataclasses import dataclass
from note_utils import format_note_with_number

try:
    from .cc_profiles import CCProfile, get_profile, load_custom_profiles
    from .midi_clock import MidiClock, MidiClockAdapter, NullMidiClockSender
    from .latency_optimizer import LatencyOptimizer
except ImportError:
    from cc_profiles import CCProfile, get_profile, load_custom_profiles
    from midi_clock import MidiClock, MidiClockAdapter, NullMidiClockSender
    from latency_optimizer import LatencyOptimizer

log = logging.getLogger(__name__)


@dataclass
class HardwareStatus:
    """Status information for external hardware integration."""
    active_profile: Optional[str] = None
    profile_name: Optional[str] = None
    clock_running: bool = False
    clock_bpm: float = 120.0
    latency_avg_ms: float = 0.0
    queue_size: int = 0


class ExternalHardwareManager:
    """Manages external hardware integration features for Phase 7.
    
    Coordinates:
    - CC profile management and parameter mapping
    - MIDI clock synchronization
    - Latency optimization and message prioritization
    """
    
    def __init__(self, midi_output, config):
        """Initialize external hardware manager.
        
        Args:
            midi_output: MIDI output instance
            config: Configuration object with MIDI and CC profile settings
        """
        self.midi_output = midi_output
        self.config = config
        
        # Initialize components
        self._init_cc_profiles()
        self._init_midi_clock()
        self._init_latency_optimizer()
        
        # State
        self.status = HardwareStatus()
        self._parameter_change_callback: Optional[Callable[[str, str, float], None]] = None
        
        # Set initial profile
        self._set_active_profile(config.midi.cc_profile.active_profile)
    
    def _init_cc_profiles(self) -> None:
        """Initialize CC profile system."""
        try:
            # Load custom profiles from config
            load_custom_profiles(self.config.model_dump())
            log.info("CC profiles initialized")
        except Exception as e:
            log.error(f"Failed to initialize CC profiles: {e}")
    
    def _init_midi_clock(self) -> None:
        """Initialize MIDI clock if enabled."""
        self.midi_clock = None
        
        if self.config.midi.clock.enabled and self.midi_output:
            try:
                clock_adapter = MidiClockAdapter(self.midi_output)
                self.midi_clock = MidiClock(clock_adapter)
                log.info("MIDI clock initialized")
            except Exception as e:
                log.error(f"Failed to initialize MIDI clock: {e}")
                self.midi_clock = None
        else:
            log.info("MIDI clock disabled")
    
    def _init_latency_optimizer(self) -> None:
        """Initialize latency optimizer."""
        try:
            throttle_ms = self.config.midi.cc_profile.cc_throttle_ms
            self.latency_optimizer = LatencyOptimizer(self.midi_output, throttle_ms)
            
            if self.midi_output and hasattr(self.midi_output, 'is_connected') and self.midi_output.is_connected:
                self.latency_optimizer.start()
                log.info(f"Latency optimizer started (CC throttle: {throttle_ms}ms)")
            else:
                log.info("Latency optimizer initialized but not started (no MIDI output)")
        except Exception as e:
            log.error(f"Failed to initialize latency optimizer: {e}")
            self.latency_optimizer = None
    
    def start(self) -> None:
        """Start all external hardware integration features."""
        if self.latency_optimizer and self.midi_output:
            if hasattr(self.midi_output, 'is_connected') and self.midi_output.is_connected:
                self.latency_optimizer.start()
        
        log.info("External hardware manager started")
    
    def stop(self) -> None:
        """Stop all external hardware integration features."""
        if self.midi_clock:
            self.midi_clock.stop()
        
        if self.latency_optimizer:
            self.latency_optimizer.stop()
        
        log.info("External hardware manager stopped")
    
    def set_active_profile(self, profile_id: str) -> bool:
        """Set the active CC profile.
        
        Args:
            profile_id: ID of the profile to activate
            
        Returns:
            True if profile was set successfully, False otherwise
        """
        return self._set_active_profile(profile_id)
    
    def _set_active_profile(self, profile_id: str) -> bool:
        """Internal method to set active profile."""
        try:
            profile = get_profile(profile_id)
            if not profile:
                log.error(f"CC profile '{profile_id}' not found")
                return False
            
            self.active_profile = profile
            self.status.active_profile = profile_id
            self.status.profile_name = profile.name
            
            log.info(f"Active CC profile set to: {profile_id} ({profile.name})")
            return True
        
        except Exception as e:
            log.error(f"Failed to set active CC profile '{profile_id}': {e}")
            return False
    
    def get_available_profiles(self) -> Dict[str, str]:
        """Get list of available CC profiles.
        
        Returns:
            Dictionary mapping profile_id to profile_name
        """
        from cc_profiles import list_available_profiles
        return list_available_profiles()
    
    def send_parameter_change(self, param_name: str, value: float, 
                            when: Optional[float] = None) -> bool:
        """Send a parameter change using the active CC profile.
        
        Args:
            param_name: Name of the parameter to change
            value: Parameter value (0.0-1.0)
            when: Optional scheduled time for the change
            
        Returns:
            True if parameter was sent successfully, False otherwise
        """
        if not hasattr(self, 'active_profile') or not self.active_profile:
            log.warning("No active CC profile set")
            return False
        
        try:
            # Map parameter using active profile
            mapping = self.active_profile.map_parameter(param_name, value)
            if not mapping:
                return False
            
            cc_num, cc_value = mapping
            
            # Send via latency optimizer if available
            if self.latency_optimizer:
                channel = self.config.midi.output_channel
                self.latency_optimizer.schedule_cc(cc_num, cc_value, channel, when)
            else:
                # Fallback to direct MIDI output
                if self.midi_output:
                    success = self.midi_output.send_control_change(
                        cc_num, cc_value, self.config.midi.output_channel
                    )
                    if not success:
                        return False
            
            # Call parameter change callback if set
            if self._parameter_change_callback:
                self._parameter_change_callback(param_name, cc_num, value)
            
            log.debug(f"Parameter change: {param_name}={value:.3f} -> CC{cc_num}={cc_value}")
            return True
        
        except Exception as e:
            log.error(f"Failed to send parameter change '{param_name}': {e}")
            return False
    
    def send_note_on(self, note: int, velocity: int, when: Optional[float] = None) -> bool:
        """Send a note on message with latency optimization.
        
        Args:
            note: MIDI note number
            velocity: Note velocity
            when: Optional scheduled time for the note
            
        Returns:
            True if note was sent successfully, False otherwise
        """
        try:
            channel = self.config.midi.output_channel
            
            if self.latency_optimizer:
                self.latency_optimizer.schedule_note_on(note, velocity, channel, when)
            else:
                if self.midi_output:
                    success = self.midi_output.send_note_on(note, velocity, channel)
                    if not success:
                        return False
            
            return True
        
        except Exception as e:
            note_info = format_note_with_number(note)
            log.error(f"Failed to send note on: note={note_info} error={e}")
            return False
    
    def send_note_off(self, note: int, when: Optional[float] = None) -> bool:
        """Send a note off message with latency optimization.
        
        Args:
            note: MIDI note number
            when: Optional scheduled time for the note off
            
        Returns:
            True if note was sent successfully, False otherwise
        """
        try:
            channel = self.config.midi.output_channel
            
            if self.latency_optimizer:
                self.latency_optimizer.schedule_note_off(note, channel, when)
            else:
                if self.midi_output:
                    success = self.midi_output.send_note_off(note, 0, channel)
                    if not success:
                        return False
            
            return True
        
        except Exception as e:
            note_info = format_note_with_number(note)
            log.error(f"Failed to send note off: note={note_info} error={e}")
            return False
    
    def set_bpm(self, bpm: float) -> None:
        """Set BPM for MIDI clock synchronization.
        
        Args:
            bpm: Beats per minute
        """
        self.status.clock_bpm = bpm
        
        if self.midi_clock:
            self.midi_clock.set_bpm(bpm)
            log.debug(f"MIDI clock BPM set to {bpm}")
    
    def start_clock(self) -> bool:
        """Start MIDI clock output.
        
        Returns:
            True if clock was started successfully, False otherwise
        """
        if not self.midi_clock:
            log.warning("MIDI clock not available")
            return False
        
        try:
            self.midi_clock.start()
            self.status.clock_running = True
            log.info("MIDI clock started")
            return True
        
        except Exception as e:
            log.error(f"Failed to start MIDI clock: {e}")
            return False
    
    def stop_clock(self) -> bool:
        """Stop MIDI clock output.
        
        Returns:
            True if clock was stopped successfully, False otherwise
        """
        if not self.midi_clock:
            return True  # Already stopped
        
        try:
            self.midi_clock.stop()
            self.status.clock_running = False
            log.info("MIDI clock stopped")
            return True
        
        except Exception as e:
            log.error(f"Failed to stop MIDI clock: {e}")
            return False
    
    def set_parameter_change_callback(self, callback: Callable[[str, str, float], None]) -> None:
        """Set callback for parameter changes.
        
        Args:
            callback: Function called with (param_name, cc_num, value) on parameter changes
        """
        self._parameter_change_callback = callback
    
    def get_parameter_names(self) -> list[str]:
        """Get list of available parameters for the active profile.
        
        Returns:
            List of parameter names, empty if no active profile
        """
        if hasattr(self, 'active_profile') and self.active_profile:
            return self.active_profile.get_parameter_names()
        return []
    
    def get_status(self) -> HardwareStatus:
        """Get current status of external hardware integration.
        
        Returns:
            Current status information
        """
        # Update dynamic status
        if self.latency_optimizer:
            stats = self.latency_optimizer.get_latency_stats()
            queue_status = self.latency_optimizer.get_queue_status()
            self.status.latency_avg_ms = stats.avg_latency_ms
            self.status.queue_size = queue_status['queue_size']
        
        if self.midi_clock:
            self.status.clock_running = self.midi_clock.status.running
            self.status.clock_bpm = self.midi_clock.status.bpm
        
        return self.status
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics for monitoring.
        
        Returns:
            Dictionary with performance metrics
        """
        metrics = {
            'cc_profile': {
                'active_profile': self.status.active_profile,
                'profile_name': self.status.profile_name,
                'available_parameters': len(self.get_parameter_names())
            },
            'midi_clock': {
                'enabled': self.midi_clock is not None,
                'running': self.status.clock_running,
                'bpm': self.status.clock_bpm
            },
            'latency': {
                'avg_ms': self.status.latency_avg_ms,
                'queue_size': self.status.queue_size
            }
        }
        
        # Add detailed latency stats if available
        if self.latency_optimizer:
            latency_stats = self.latency_optimizer.get_latency_stats()
            queue_status = self.latency_optimizer.get_queue_status()
            
            metrics['latency'].update({
                'min_ms': latency_stats.min_latency_ms,
                'max_ms': latency_stats.max_latency_ms,
                'total_messages': latency_stats.total_messages,
                'queue_utilization': queue_status['queue_utilization'],
                'pending_cc_count': queue_status['pending_cc_count']
            })
        
        return metrics
