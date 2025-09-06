"""State management for the generative engine.

Provides observable parameter store with change listeners and validation.
Phase 2: Basic state container with change notifications.
"""

from __future__ import annotations
from typing import Dict, Any, Callable, List, Optional, Union
from dataclasses import dataclass, field
import logging
import threading
import time

log = logging.getLogger(__name__)


@dataclass
class StateChange:
    """Represents a state parameter change."""
    parameter: str
    old_value: Any
    new_value: Any
    timestamp: float = field(default_factory=time.time)
    source: str = "unknown"  # e.g., 'midi', 'mutation', 'idle'


class State:
    """Central parameter store with change notifications.
    
    Maintains core engine parameters like tempo, density, swing, etc.
    Provides validation and change listener support.
    """
    
    def __init__(self):
        self._params: Dict[str, Any] = {}
        self._listeners: List[Callable[[StateChange], None]] = []
        self._lock = threading.RLock()
        
        # Initialize default parameters
        self._init_defaults()
    
    def _init_defaults(self):
        """Initialize default parameter values."""
        defaults = {
            'bpm': 110.0,
            'swing': 0.12,
            'density': 0.85,
            'note_probability': 0.9, # Probability of a note playing on an active step
            'sequence_length': 8,
            'scale_index': 0,  # Index into scales list
            'root_note': 60,  # MIDI note number for scale root (C4)
            'chaos_lock': False,
            'drift': 0.0,
            'filter_cutoff': 64,
            'reverb_mix': 32,
            'master_volume': 100,
            # Phase 5.5: Enhanced probability and rhythm patterns
            'step_probabilities': None,  # Array of per-step probabilities (fallback to note_probability if None)
            'step_pattern': None,  # Array of booleans for step activation (fallback to even-step pattern if None)
            'base_velocity': 80,  # Base velocity for notes
            'velocity_range': 40,  # Range for velocity variation (+/- from base)
            'mode': 0,
            'palette': 0,
            'idle_mode': False,
            'step_position': 0,  # Current step in sequence (0-based)
        }
        
        for param, value in defaults.items():
            self._params[param] = value
    
    def add_listener(self, listener: Callable[[StateChange], None]):
        """Add a change listener."""
        with self._lock:
            self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable[[StateChange], None]):
        """Remove a change listener."""
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)
    
    def get(self, param: str, default: Any = None) -> Any:
        """Get a parameter value."""
        with self._lock:
            return self._params.get(param, default)
    
    def set(self, param: str, value: Any, source: str = "unknown") -> bool:
        """Set a parameter value with validation.
        
        Returns True if value was changed, False if unchanged or invalid.
        """
        # Validate and clamp value
        validated_value = self._validate_param(param, value)
        if validated_value is None:
            log.warning(f"Invalid value for parameter {param}: {value}")
            return False
        
        with self._lock:
            old_value = self._params.get(param)
            if old_value == validated_value:
                return False  # No change
            
            self._params[param] = validated_value
            
            # Notify listeners
            change = StateChange(
                parameter=param,
                old_value=old_value,
                new_value=validated_value,
                source=source
            )
            
            for listener in self._listeners:
                try:
                    listener(change)
                except Exception as e:
                    log.error(f"State listener error: {e}")
            
            log.debug(f"state_change param={param} old={old_value} new={validated_value} source={source}")
            return True
    
    def update_multiple(self, updates: Dict[str, Any], source: str = "unknown") -> int:
        """Update multiple parameters atomically.
        
        Returns count of parameters that were actually changed.
        """
        changes = 0
        for param, value in updates.items():
            if self.set(param, value, source):
                changes += 1
        return changes
    
    def get_all(self) -> Dict[str, Any]:
        """Get a copy of all parameters."""
        with self._lock:
            return self._params.copy()
    
    def _validate_param(self, param: str, value: Any) -> Optional[Any]:
        """Validate and clamp parameter values."""
        if param == 'bpm':
            return max(1.0, min(200.0, float(value)))
        elif param == 'swing':
            return max(0.0, min(0.5, float(value)))
        elif param == 'density':
            return max(0.0, min(1.0, float(value)))
        elif param == 'note_probability':
            return max(0.0, min(1.0, float(value)))
        elif param == 'sequence_length':
            return max(1, min(32, int(value)))
        elif param == 'scale_index':
            return max(0, int(value))  # Upper bound checked by sequencer
        elif param == 'root_note':
            return max(0, min(127, int(value)))  # Valid MIDI note range
        elif param in ('filter_cutoff', 'reverb_mix', 'master_volume'):
            return max(0, min(127, int(value)))
        elif param == 'drift':
            return max(-0.2, min(0.2, float(value)))
        elif param in ('chaos_lock', 'idle_mode'):
            return bool(value)
        elif param in ('mode', 'palette'):
            return max(0, min(7, int(value)))  # 8 modes/palettes
        elif param == 'step_position':
            return max(0, int(value))  # Upper bound checked by sequencer
        else:
            # Unknown parameter - allow through but log
            log.debug(f"Unknown parameter {param}, allowing value {value}")
            return value


# Global state instance
_state_instance: Optional[State] = None


def get_state() -> State:
    """Get the global state instance."""
    global _state_instance
    if _state_instance is None:
        _state_instance = State()
    return _state_instance


def reset_state():
    """Reset global state (primarily for testing)."""
    global _state_instance
    _state_instance = None
