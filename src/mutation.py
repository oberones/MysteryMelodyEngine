"""Mutation Engine for periodic parameter changes.

Phase 5: Implements scheduled mild parameter perturbations every 2-4 minutes.
Phase 6: Respects idle mode - mutations enabled when idle, disabled when active.
Provides weighted random parameter selection and bounded delta application.
"""

from __future__ import annotations
import random
import time
import threading
import logging
from typing import Dict, List, Callable, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from config import MutationConfig
from state import State, StateChange

if TYPE_CHECKING:
    from idle import IdleManager

log = logging.getLogger(__name__)


@dataclass
class MutationRule:
    """Defines how a parameter can be mutated."""
    parameter: str
    weight: float = 1.0  # Higher weight = more likely to be selected
    delta_range: Tuple[float, float] = (-0.1, 0.1)  # Min/max delta values
    delta_scale: float = 1.0  # Scale factor for delta application
    description: str = ""
    
    def apply_delta(self, current_value: float) -> float:
        """Apply a random delta to the current value."""
        delta = random.uniform(self.delta_range[0], self.delta_range[1])
        return current_value + (delta * self.delta_scale)


@dataclass
class MutationEvent:
    """Records a mutation that was applied."""
    timestamp: float = field(default_factory=time.time)
    parameter: str = ""
    old_value: float = 0.0
    new_value: float = 0.0
    delta: float = 0.0
    rule_description: str = ""


class MutationEngine:
    """Periodic parameter mutation system.
    
    Schedules random parameter changes based on weighted rules.
    Maintains history of mutations for logging and analysis.
    Phase 6: Respects idle mode - only mutates when system is idle.
    """
    
    def __init__(self, config: MutationConfig, state: State):
        self.config = config
        self.state = state
        self._rules: List[MutationRule] = []
        self._history: List[MutationEvent] = []
        self._max_history = 100  # Keep last 100 mutations
        
        # Threading
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._next_mutation_time = 0.0
        
        # State listener for logging changes
        self._mutation_listener: Optional[Callable[[StateChange], None]] = None
        
        # Idle mode integration
        self._idle_manager: Optional[IdleManager] = None
        self._mutations_enabled = False  # Start disabled until idle manager indicates idle state
        
        # Initialize default mutation rules
        self._init_default_rules()
        
        log.info(f"mutation_engine_init rules={len(self._rules)} interval={config.interval_min_s}-{config.interval_max_s}s max_changes={config.max_changes_per_cycle}")
    
    def _init_default_rules(self):
        """Initialize default mutation rules for various parameters."""
        self._rules = [
            # Timing and rhythm parameters
            MutationRule(
                parameter="bpm",
                weight=2.0,
                delta_range=(-5.0, 5.0),
                delta_scale=1.0,
                description="Tempo drift"
            ),
            MutationRule(
                parameter="swing",
                weight=1.5,
                delta_range=(-0.05, 0.05),
                delta_scale=1.0,
                description="Swing adjustment"
            ),
            MutationRule(
                parameter="density",
                weight=3.0,
                delta_range=(-0.1, 0.1),
                delta_scale=1.0,
                description="Density variation"
            ),
            MutationRule(
                parameter="note_probability",
                weight=2.5,
                delta_range=(-0.05, 0.05),
                delta_scale=1.0,
                description="Note probability shift"
            ),
            
            # Musical scale parameters
            MutationRule(
                parameter="note_probability",
                weight=2.5,
                delta_range=(-0.05, 0.05),
                delta_scale=1.0,
                description="Note probability shift"
            ),
            
            # Audio parameters
            MutationRule(
                parameter="filter_cutoff",
                weight=2.0,
                delta_range=(-10.0, 10.0),
                delta_scale=1.0,
                description="Filter cutoff drift"
            ),
            MutationRule(
                parameter="reverb_mix",
                weight=1.5,
                delta_range=(-5.0, 5.0),
                delta_scale=1.0,
                description="Reverb mix adjustment"
            ),
            
            # Sequence parameters
            MutationRule(
                parameter="sequence_length",
                weight=1.0,
                delta_range=(-2, 2),
                delta_scale=1.0,
                description="Sequence length change"
            ),
            
            # Drift parameter (for BPM modulation)
            MutationRule(
                parameter="drift",
                weight=1.5,
                delta_range=(-0.05, 0.05),
                delta_scale=1.0,
                description="BPM drift envelope"
            ),
        ]
    
    def add_rule(self, rule: MutationRule):
        """Add a custom mutation rule."""
        with self._lock:
            self._rules.append(rule)
            log.debug(f"mutation_rule_added parameter={rule.parameter} weight={rule.weight}")
    
    def remove_rule(self, parameter: str) -> bool:
        """Remove mutation rule for a parameter."""
        with self._lock:
            for i, rule in enumerate(self._rules):
                if rule.parameter == parameter:
                    removed = self._rules.pop(i)
                    log.debug(f"mutation_rule_removed parameter={removed.parameter}")
                    return True
            return False
    
    def set_idle_manager(self, idle_manager: IdleManager):
        """Set the idle manager for idle mode awareness."""
        self._idle_manager = idle_manager
        # Register callback to track idle state changes
        idle_manager.add_idle_state_callback(self._on_idle_state_change)
        log.debug("mutation_engine_idle_integration_enabled")
    
    def _on_idle_state_change(self, is_idle: bool):
        """Handle idle state changes."""
        with self._lock:
            old_enabled = self._mutations_enabled
            self._mutations_enabled = is_idle
            
            if old_enabled != self._mutations_enabled:
                status = "enabled" if self._mutations_enabled else "disabled"
                log.info(f"mutations_{status} idle_state={is_idle}")
    
    def are_mutations_enabled(self) -> bool:
        """Check if mutations are currently enabled."""
        with self._lock:
            return self._mutations_enabled
    
    def start(self):
        """Start the mutation engine thread."""
        if self._running:
            return
        
        with self._lock:
            self._running = True
            self._schedule_next_mutation()
            
            # Set up state listener to track our mutations
            if self._mutation_listener is None:
                self._mutation_listener = self._on_state_change
                self.state.add_listener(self._mutation_listener)
            
            self._thread = threading.Thread(target=self._mutation_thread, daemon=True)
            self._thread.start()
            
        log.info("mutation_engine_started")
    
    def stop(self):
        """Stop the mutation engine."""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            
            # Remove state listener
            if self._mutation_listener:
                self.state.remove_listener(self._mutation_listener)
                self._mutation_listener = None
        
        # Wait for thread to finish
        if self._thread:
            self._thread.join(timeout=1.0)
        
        log.info("mutation_engine_stopped")
    
    def maybe_mutate(self):
        """Check if it's time to mutate and do so if needed.
        
        This method can be called from the main loop for manual triggering.
        """
        current_time = time.time()
        if current_time >= self._next_mutation_time:
            self._perform_mutation_cycle()
    
    def force_mutation(self):
        """Force a mutation cycle immediately (for testing/debugging)."""
        self._perform_mutation_cycle()
    
    def get_history(self, count: Optional[int] = None) -> List[MutationEvent]:
        """Get mutation history."""
        with self._lock:
            if count is None:
                return self._history.copy()
            else:
                return self._history[-count:].copy()
    
    def get_stats(self) -> Dict:
        """Get mutation engine statistics."""
        with self._lock:
            current_time = time.time()
            time_to_next = max(0.0, self._next_mutation_time - current_time)
            
            return {
                "running": self._running,
                "mutations_enabled": self._mutations_enabled,
                "total_mutations": len(self._history),
                "rules_count": len(self._rules),
                "time_to_next_mutation_s": time_to_next,
                "next_mutation_time": self._next_mutation_time,
            }
    
    def _schedule_next_mutation(self):
        """Schedule the next mutation cycle."""
        interval = random.uniform(self.config.interval_min_s, self.config.interval_max_s)
        self._next_mutation_time = time.time() + interval
        log.debug(f"mutation_scheduled interval={interval:.1f}s next_time={self._next_mutation_time:.1f}")
    
    def _mutation_thread(self):
        """Main mutation thread that checks for scheduled mutations."""
        while self._running:
            try:
                current_time = time.time()
                if current_time >= self._next_mutation_time:
                    self._perform_mutation_cycle()
                
                # Sleep for a short time to avoid busy waiting
                time.sleep(1.0)
                
            except Exception as e:
                log.error(f"mutation_thread_error error={e}")
                time.sleep(5.0)  # Back off on errors
    
    def _perform_mutation_cycle(self):
        """Perform a complete mutation cycle."""
        with self._lock:
            # Check if mutations are enabled (idle mode)
            if not self._mutations_enabled:
                log.debug("mutation_cycle_skipped reason=mutations_disabled")
                self._schedule_next_mutation()
                return
            
            if not self._rules:
                log.warning("mutation_cycle_skipped reason=no_rules")
                self._schedule_next_mutation()
                return
            
            # Select parameters to mutate
            selected_rules = self._select_mutation_rules()
            if not selected_rules:
                log.debug("mutation_cycle_skipped reason=no_selection")
                self._schedule_next_mutation()
                return
            
            mutations_applied = 0
            
            # Apply mutations
            for rule in selected_rules:
                if self._apply_mutation(rule):
                    mutations_applied += 1
            
            log.info(f"mutation_cycle_complete rules_selected={len(selected_rules)} mutations_applied={mutations_applied}")
            
            # Schedule next cycle
            self._schedule_next_mutation()
    
    def _select_mutation_rules(self) -> List[MutationRule]:
        """Select rules for mutation using weighted random selection."""
        if not self._rules:
            return []
        
        max_changes = min(self.config.max_changes_per_cycle, len(self._rules))
        if max_changes <= 0:
            return []
        
        # Create weighted list
        weighted_rules = []
        for rule in self._rules:
            # Check if parameter exists in state
            current_value = self.state.get(rule.parameter)
            if current_value is not None:
                weighted_rules.append(rule)
        
        if not weighted_rules:
            return []
        
        # Select rules without replacement using weighted selection
        selected = []
        available_rules = weighted_rules.copy()
        
        for _ in range(max_changes):
            if not available_rules:
                break
            
            # Calculate total weight
            total_weight = sum(rule.weight for rule in available_rules)
            if total_weight <= 0:
                break
            
            # Select rule
            target = random.uniform(0, total_weight)
            cumulative = 0.0
            
            for i, rule in enumerate(available_rules):
                cumulative += rule.weight
                if cumulative >= target:
                    selected.append(rule)
                    available_rules.pop(i)
                    break
        
        return selected
    
    def _apply_mutation(self, rule: MutationRule) -> bool:
        """Apply a single mutation rule."""
        current_value = self.state.get(rule.parameter)
        if current_value is None:
            log.warning(f"mutation_skipped parameter={rule.parameter} reason=not_found")
            return False
        
        try:
            # Calculate new value
            new_value = rule.apply_delta(float(current_value))
            delta = new_value - float(current_value)
            
            # Apply the change (State will handle validation/clamping)
            if self.state.set(rule.parameter, new_value, source="mutation"):
                # Get the actual value that was set (after validation)
                final_value = self.state.get(rule.parameter)
                
                # Record mutation event
                event = MutationEvent(
                    parameter=rule.parameter,
                    old_value=float(current_value),
                    new_value=float(final_value),
                    delta=delta,
                    rule_description=rule.description
                )
                
                self._history.append(event)
                
                # Trim history if needed
                if len(self._history) > self._max_history:
                    self._history = self._history[-self._max_history:]
                
                log.info(f"mutation_applied parameter={rule.parameter} old={current_value} new={final_value} delta={delta:.3f} description={rule.description}")
                return True
            else:
                log.debug(f"mutation_no_change parameter={rule.parameter} value={current_value}")
                return False
                
        except Exception as e:
            log.error(f"mutation_failed parameter={rule.parameter} error={e}")
            return False
    
    def _on_state_change(self, change: StateChange):
        """Handle state changes to track mutations."""
        # We only care about changes from mutation source for statistics
        if change.source == "mutation":
            log.debug(f"mutation_state_change parameter={change.parameter} old={change.old_value} new={change.new_value}")


def create_mutation_engine(config: MutationConfig, state: State) -> MutationEngine:
    """Factory function to create a mutation engine."""
    return MutationEngine(config, state)
