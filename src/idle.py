"""Idle mode management for the generative engine.

Tracks user interaction and manages transition to/from ambient idle mode.
Phase 6: Idle mode detection and handling.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Callable
import time
import logging
import threading
from dataclasses import dataclass, field
from state import State, StateChange
from config import IdleConfig

log = logging.getLogger(__name__)


@dataclass
class IdleProfile:
    """Defines an ambient idle profile."""
    name: str
    params: Dict[str, Any]
    description: str


@dataclass
class IdleTransitionState:
    """Tracks the current state of idle transition."""
    is_transitioning: bool = False
    direction: str = "none"  # "to_idle", "from_idle", "none"
    start_time: float = 0.0
    start_values: Dict[str, Any] = field(default_factory=dict)
    target_values: Dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0


class IdleManager:
    """Manages idle mode detection and ambient profile switching.
    
    Tracks the last interaction timestamp and smoothly transitions to ambient mode
    after the configured timeout. When interactions are detected during idle mode,
    the system immediately stops the idle transition and allows normal parameter
    modification without attempting to restore previous values.
    """
    
    def __init__(self, config: IdleConfig, state: State):
        self.config = config
        self.state = state
        self.timeout_seconds = config.timeout_ms / 1000.0
        
        # Interaction tracking
        self.last_interaction_time = time.time()
        self.is_idle = False
        
        # Smooth transition state (no longer saving state for restoration)
        self.transition = IdleTransitionState()
        
        # Idle profiles
        self.idle_profiles = self._create_idle_profiles()
        self.current_profile = self.idle_profiles.get(config.ambient_profile)
        
        # Threading
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # Callbacks
        self._idle_state_callbacks: list[Callable[[bool], None]] = []
        
        log.info(f"idle_manager_init timeout={self.timeout_seconds:.1f}s profile={config.ambient_profile}")
    
    def _create_idle_profiles(self) -> Dict[str, IdleProfile]:
        """Create predefined idle profiles."""
        return {
            "slow_fade": IdleProfile(
                name="slow_fade",
                params={
                    'density': 0.3,          # Reduce note density
                    'bpm': 65.0,             # Slower tempo
                    'scale_index': 2,        # Switch to pentatonic (assumed index 2)
                    'reverb_mix': 90,        # More reverb
                    'filter_cutoff': 40,     # Darker filter
                    'master_volume': 60,     # Quieter
                },
                description="Slow, ambient fade with reduced density and darker tones"
            ),
            "minimal": IdleProfile(
                name="minimal",
                params={
                    'density': 0.15,
                    'bpm': 50.0,
                    'scale_index': 2,        # Pentatonic
                    'reverb_mix': 100,       # Full reverb
                    'swing': 0.05,           # Less swing
                    'master_volume': 40,     # Very quiet
                },
                description="Minimal ambient with very low density"
            ),
            "meditative": IdleProfile(
                name="meditative",
                params={
                    'density': 0.4,
                    'bpm': 72.0,
                    'scale_index': 1,        # Minor (assumed index 1)
                    'reverb_mix': 80,
                    'filter_cutoff': 30,     # Very dark
                    'swing': 0.0,            # No swing, straight
                    'master_volume': 50,
                },
                description="Meditative ambient with minor tonality"
            )
        }
    
    def add_idle_state_callback(self, callback: Callable[[bool], None]):
        """Add a callback to be notified of idle state changes."""
        with self._lock:
            self._idle_state_callbacks.append(callback)
    
    def remove_idle_state_callback(self, callback: Callable[[bool], None]):
        """Remove an idle state callback."""
        with self._lock:
            if callback in self._idle_state_callbacks:
                self._idle_state_callbacks.remove(callback)
    
    def start(self):
        """Start the idle detection and transition thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._idle_monitor_thread, daemon=True)
        self._thread.start()
        log.info("idle_manager_started")
    
    def stop(self):
        """Stop the idle manager."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        log.info("idle_manager_stopped")
    
    def touch(self, preserve_tempo: bool = False):
        """Record an interaction, resetting the idle timer.
        
        Args:
            preserve_tempo: This parameter is now ignored as we no longer restore state.
                           Kept for backward compatibility.
        """
        with self._lock:
            self.last_interaction_time = time.time()
            
            # If we were idle or transitioning, immediately stop idle mode
            if self.is_idle or self.transition.is_transitioning:
                self._interrupt_idle_mode()
    
    def force_idle(self):
        """Force entry into idle mode (for testing/manual control)."""
        with self._lock:
            if not self.is_idle and not self.transition.is_transitioning:
                self._begin_idle_transition()
    
    def force_active(self):
        """Force exit from idle mode (for testing/manual control)."""
        with self._lock:
            if self.is_idle or self.transition.is_transitioning:
                self._interrupt_idle_mode()
    
    def get_time_since_last_interaction(self) -> float:
        """Get time in seconds since last interaction."""
        with self._lock:
            return time.time() - self.last_interaction_time
    
    def get_time_to_idle(self) -> float:
        """Get time in seconds until idle mode (negative if already idle)."""
        if self.is_idle:
            return -1.0
        
        time_since = self.get_time_since_last_interaction()
        return max(0.0, self.timeout_seconds - time_since)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current idle manager status."""
        with self._lock:
            return {
                'is_idle': self.is_idle,
                'is_transitioning': self.transition.is_transitioning,
                'transition_direction': self.transition.direction,
                'timeout_seconds': self.timeout_seconds,
                'time_since_last_interaction': self.get_time_since_last_interaction(),
                'time_to_idle': self.get_time_to_idle(),
                'current_profile': self.current_profile.name if self.current_profile else None,
            }
    
    def _idle_monitor_thread(self):
        """Monitor for activity and manage transitions."""
        try:
            while self._running:
                current_time = time.time()
                
                if self.transition.is_transitioning:
                    self._update_transition()
                    # Sleep briefly during transitions for smooth updates
                    time.sleep(0.01)  # 10ms updates during transition
                elif self.is_idle:
                    # Already idle, just monitor
                    time.sleep(0.1)  # 100ms when idle
                elif current_time - self.last_interaction_time >= self.timeout_seconds:
                    # Begin idle transition
                    self._begin_idle_transition()
                    # Don't sleep here, immediately check if transitioning
                else:
                    # Not idle, normal monitoring
                    time.sleep(0.1)  # 100ms polling for faster response
                    
        except Exception as e:
            log.error(f"Error in idle monitor thread: {e}")
            import traceback
            traceback.print_exc()
    
    def _begin_idle_transition(self):
        """Begin smooth transition to idle mode."""
        if not self.current_profile:
            log.warning("idle_transition_no_profile")
            return
        
        log.info("idle_transition_begin")
        
        # Set up transition state
        self.transition.is_transitioning = True
        self.transition.direction = "to_idle"
        self.transition.start_time = time.time()
        self.transition.duration_ms = self.config.fade_in_ms
        self.transition.start_values = {}
        self.transition.target_values = {}
        
        # Capture current values and set targets
        for param, target_value in self.current_profile.params.items():
            current_value = self.state.get(param)
            if current_value is not None:
                self.transition.start_values[param] = current_value
                self.transition.target_values[param] = target_value
        
        log.debug(f"idle_transition_setup params={list(self.transition.start_values.keys())}")
    
    def _update_transition(self):
        """Update the current transition state."""
        elapsed_ms = (time.time() - self.transition.start_time) * 1000
        progress = min(1.0, elapsed_ms / self.transition.duration_ms)
        
        # Apply linear interpolation for all parameters
        for param in self.transition.start_values:
            start_val = self.transition.start_values[param]
            target_val = self.transition.target_values[param]
            
            # Linear interpolation
            if isinstance(start_val, (int, float)) and isinstance(target_val, (int, float)):
                current_val = start_val + (target_val - start_val) * progress
                self.state.set(param, current_val, source='idle_transition')
            else:
                # For non-numeric values, switch at 50% progress
                if progress >= 0.5:
                    self.state.set(param, target_val, source='idle_transition')
        
        # Check if transition is complete
        if progress >= 1.0:
            self._complete_idle_transition()
        
        # Debug log every 1 second during transition
        if int(elapsed_ms) % 1000 < 100:  # Approximately every second
            log.debug(f"idle_transition_progress progress={progress:.2f} elapsed_ms={elapsed_ms:.0f}")
    
    def _complete_idle_transition(self):
        """Complete the transition to idle mode."""
        log.info("idle_transition_complete")
        
        # Set final values
        if self.current_profile:
            for param, value in self.current_profile.params.items():
                self.state.set(param, value, source='idle')
        
        # Mark as fully idle
        self.is_idle = True
        self.transition.is_transitioning = False
        self.transition.direction = "none"
        
        # Notify callbacks
        self._notify_idle_state_callbacks(True)
        
        log.info(f"idle_mode_active profile={self.current_profile.name if self.current_profile else 'none'}")
    
    def _interrupt_idle_mode(self):
        """Interrupt idle mode or transition - no state restoration."""
        was_idle = self.is_idle
        was_transitioning = self.transition.is_transitioning
        
        if not was_idle and not was_transitioning:
            return
        
        log.info(f"idle_mode_interrupt was_idle={was_idle} was_transitioning={was_transitioning}")
        
        # Simply stop the idle state and transitions - no restoration
        self.is_idle = False
        self.transition.is_transitioning = False
        self.transition.direction = "none"
        
        # Update interaction time to prevent immediate re-entry
        self.last_interaction_time = time.time()
        
        # Notify callbacks only if we were actually in idle mode
        if was_idle:
            self._notify_idle_state_callbacks(False)
        
        log.info("idle_mode_interrupted_no_restoration")
    
    def _notify_idle_state_callbacks(self, is_idle: bool):
        """Notify all idle state callbacks."""
        for callback in self._idle_state_callbacks:
            try:
                callback(is_idle)
            except Exception as e:
                log.error(f"idle_callback_error callback={callback} error={e}")


def create_idle_manager(config: IdleConfig, state: State) -> IdleManager:
    """Factory function to create and configure an idle manager."""
    return IdleManager(config, state)
