"""Tests for the mutation engine.

Phase 5: Test mutation rule boundaries, weighted selection, and scheduling.
"""

import pytest
import time
import threading
from unittest.mock import MagicMock
from config import MutationConfig
from state import State, StateChange
from mutation import MutationEngine, MutationRule, create_mutation_engine


class TestMutationRule:
    """Test mutation rule behavior."""
    
    def test_rule_creation(self):
        """Test creation of mutation rules."""
        rule = MutationRule(
            parameter="bpm",
            weight=2.0,
            delta_range=(-5.0, 5.0),
            description="Tempo drift"
        )
        
        assert rule.parameter == "bpm"
        assert rule.weight == 2.0
        assert rule.delta_range == (-5.0, 5.0)
        assert rule.description == "Tempo drift"
    
    def test_apply_delta(self):
        """Test delta application."""
        rule = MutationRule(
            parameter="density",
            delta_range=(-0.1, 0.1),
            delta_scale=1.0
        )
        
        current_value = 0.5
        # Apply delta multiple times to test range
        for _ in range(100):
            new_value = rule.apply_delta(current_value)
            delta = new_value - current_value
            # Delta should be within expected range
            assert -0.1 <= delta <= 0.1
    
    def test_apply_delta_with_scale(self):
        """Test delta application with scaling."""
        rule = MutationRule(
            parameter="bpm",
            delta_range=(-1.0, 1.0),
            delta_scale=5.0  # Scale up the delta
        )
        
        current_value = 120.0
        new_value = rule.apply_delta(current_value)
        delta = new_value - current_value
        # Delta should be scaled: -5.0 to 5.0
        assert -5.0 <= delta <= 5.0


class TestMutationEngine:
    """Test mutation engine functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test mutation config."""
        return MutationConfig(
            interval_min_s=1,  # Short intervals for testing
            interval_max_s=2,
            max_changes_per_cycle=2
        )
    
    @pytest.fixture
    def state(self):
        """Create test state."""
        state = State()
        # Set some initial values
        state.set("bpm", 120.0)
        state.set("density", 0.8)
        state.set("swing", 0.1)
        return state
    
    @pytest.fixture
    def engine(self, config, state):
        """Create test mutation engine."""
        return MutationEngine(config, state)
    
    def test_engine_creation(self, config, state):
        """Test mutation engine creation."""
        engine = MutationEngine(config, state)
        
        assert engine.config == config
        assert engine.state == state
        assert len(engine._rules) > 0  # Should have default rules
        assert not engine._running
    
    def test_factory_function(self, config, state):
        """Test factory function."""
        engine = create_mutation_engine(config, state)
        assert isinstance(engine, MutationEngine)
    
    def test_add_remove_rules(self, engine):
        """Test adding and removing mutation rules."""
        initial_count = len(engine._rules)
        
        # Add a custom rule
        custom_rule = MutationRule(
            parameter="custom_param",
            weight=1.0,
            delta_range=(-0.5, 0.5)
        )
        engine.add_rule(custom_rule)
        
        assert len(engine._rules) == initial_count + 1
        
        # Remove the rule
        removed = engine.remove_rule("custom_param")
        assert removed
        assert len(engine._rules) == initial_count
        
        # Try to remove non-existent rule
        removed = engine.remove_rule("nonexistent")
        assert not removed
    
    def test_rule_selection(self, engine, state):
        """Test weighted rule selection."""
        # Add test parameters to state
        state.set("test_param1", 1.0)
        state.set("test_param2", 2.0)
        state.set("test_param3", 3.0)
        
        # Clear existing rules and add test rules
        engine._rules.clear()
        engine.add_rule(MutationRule("test_param1", weight=1.0))
        engine.add_rule(MutationRule("test_param2", weight=3.0))  # Higher weight
        engine.add_rule(MutationRule("test_param3", weight=1.0))
        
        # Temporarily set max_changes to 1 to test individual selection
        original_max = engine.config.max_changes_per_cycle
        engine.config.max_changes_per_cycle = 1
        
        try:
            # Select rules multiple times to test weighting
            selections = {"test_param1": 0, "test_param2": 0, "test_param3": 0}
            
            for _ in range(300):  # More iterations for better statistics
                selected = engine._select_mutation_rules()
                for rule in selected:
                    selections[rule.parameter] += 1
            
            # test_param2 should be selected more often due to higher weight
            # With weight 3:1:1, param2 should get ~60% of selections
            assert selections["test_param2"] > selections["test_param1"] * 2
            assert selections["test_param2"] > selections["test_param3"] * 2
        finally:
            engine.config.max_changes_per_cycle = original_max
    
    def test_mutation_application(self, engine, state):
        """Test applying mutations."""
        initial_bpm = state.get("bpm")
        
        # Find BPM rule
        bpm_rule = None
        for rule in engine._rules:
            if rule.parameter == "bpm":
                bpm_rule = rule
                break
        
        assert bpm_rule is not None
        
        # Apply mutation
        result = engine._apply_mutation(bpm_rule)
        assert result  # Should succeed
        
        # Check that BPM changed
        new_bpm = state.get("bpm")
        assert new_bpm != initial_bpm
        
        # Check mutation history
        assert len(engine._history) > 0
        last_mutation = engine._history[-1]
        assert last_mutation.parameter == "bpm"
        assert last_mutation.old_value == initial_bpm
        assert last_mutation.new_value == new_bpm
    
    def test_mutation_bounds(self, engine, state):
        """Test that mutations respect parameter bounds."""
        # Test density bounds
        state.set("density", 0.95)  # Near upper bound
        
        density_rule = MutationRule(
            parameter="density",
            delta_range=(0.1, 0.2),  # Only positive deltas
            delta_scale=1.0
        )
        
        # Apply mutation - should be clamped to 1.0
        engine._apply_mutation(density_rule)
        final_density = state.get("density")
        assert final_density <= 1.0  # Should be clamped
    
    def test_start_stop(self, engine):
        """Test starting and stopping the engine."""
        assert not engine._running
        
        # Start engine
        engine.start()
        assert engine._running
        assert engine._thread is not None
        
        # Wait a bit to ensure thread is running
        time.sleep(0.1)
        assert engine._thread.is_alive()
        
        # Stop engine
        engine.stop()
        assert not engine._running
        
        # Thread should terminate
        time.sleep(0.1)
        assert not engine._thread.is_alive()
    
    def test_force_mutation(self, engine, state):
        """Test forced mutation."""
        # Enable mutations for testing (simulate idle state)
        engine._mutations_enabled = True
        
        initial_history_len = len(engine._history)
        
        # Force a mutation
        engine.force_mutation()
        
        # Should have applied some mutations
        assert len(engine._history) > initial_history_len
    
    def test_maybe_mutate_timing(self, engine):
        """Test maybe_mutate timing logic."""
        # Enable mutations for testing (simulate idle state)
        engine._mutations_enabled = True
        
        # Set next mutation time in the past
        engine._next_mutation_time = time.time() - 1.0
        
        initial_history_len = len(engine._history)
        engine.maybe_mutate()
        
        # Should have triggered a mutation
        assert len(engine._history) > initial_history_len
        
        # Next mutation time should be updated
        assert engine._next_mutation_time > time.time()
    
    def test_get_stats(self, engine):
        """Test statistics retrieval."""
        stats = engine.get_stats()
        
        assert isinstance(stats, dict)
        assert "running" in stats
        assert "mutations_enabled" in stats
        assert "total_mutations" in stats
        assert "rules_count" in stats
        assert "time_to_next_mutation_s" in stats
        
        assert stats["running"] == engine._running
        assert stats["mutations_enabled"] == engine._mutations_enabled
        assert stats["total_mutations"] == len(engine._history)
        assert stats["rules_count"] == len(engine._rules)
    
    def test_get_history(self, engine):
        """Test mutation history retrieval."""
        # Enable mutations for testing (simulate idle state)
        engine._mutations_enabled = True
        
        # Get all history
        history = engine.get_history()
        assert len(history) == len(engine._history)
        
        # Add some mutations
        engine.force_mutation()
        
        # Get limited history
        limited = engine.get_history(count=1)
        assert len(limited) == 1
        assert limited[0] == engine._history[-1]
    
    def test_state_listener(self, engine, state):
        """Test state change listening."""
        # Enable mutations for testing (simulate idle state)
        engine._mutations_enabled = True
        
        # Track state changes
        changes = []
        
        def track_changes(change: StateChange):
            changes.append(change)
        
        state.add_listener(track_changes)
        
        # Apply a mutation
        engine.force_mutation()
        
        # Should have received change notifications
        mutation_changes = [c for c in changes if c.source == "mutation"]
        assert len(mutation_changes) > 0
    
    def test_history_trimming(self, engine):
        """Test that mutation history is trimmed."""
        # Set small history limit for testing
        original_limit = engine._max_history
        engine._max_history = 3
        
        try:
            # Force multiple mutations
            for _ in range(5):
                engine.force_mutation()
            
            # History should be trimmed
            assert len(engine._history) <= 3
        finally:
            engine._max_history = original_limit
    
    def test_parameter_not_found(self, engine, state):
        """Test handling of missing parameters."""
        # Create rule for non-existent parameter
        bad_rule = MutationRule(parameter="nonexistent")
        
        # Should return False and not crash
        result = engine._apply_mutation(bad_rule)
        assert not result
    
    def test_threading_safety(self, engine, state):
        """Test thread safety of mutation operations."""
        # Start engine
        engine.start()
        
        try:
            # Perform operations from multiple threads
            def stress_test():
                for _ in range(10):
                    engine.get_stats()
                    engine.get_history()
                    time.sleep(0.01)
            
            threads = [threading.Thread(target=stress_test) for _ in range(3)]
            
            for t in threads:
                t.start()
            
            for t in threads:
                t.join()
            
            # Should not crash
            assert engine._running
            
        finally:
            engine.stop()


class TestMutationIntegration:
    """Integration tests for mutation engine with other components."""
    
    def test_mutation_with_sequencer_state(self):
        """Test mutations affect sequencer parameters."""
        config = MutationConfig(
            interval_min_s=1,
            interval_max_s=2,
            max_changes_per_cycle=1
        )
        
        state = State()
        # Set initial values for parameters that exist in mutation rules
        state.set("bpm", 120.0)
        state.set("density", 0.8)
        state.set("swing", 0.1)
        state.set("note_probability", 0.9)
        state.set("filter_cutoff", 64)
        state.set("reverb_mix", 32)
        
        engine = MutationEngine(config, state)
        
        # Enable mutations for testing (simulate idle state)
        engine._mutations_enabled = True
        
        # Track state changes
        changes = []
        state.add_listener(lambda c: changes.append(c))
        
        # Force mutation multiple times to ensure we get a change
        for _ in range(5):
            engine.force_mutation()
        
        # Should have mutation changes
        mutation_changes = [c for c in changes if c.source == "mutation"]
        assert len(mutation_changes) > 0
        
        # Changes should be for valid sequencer parameters
        valid_params = {"bpm", "density", "swing", "sequence_length", "note_probability", 
                       "filter_cutoff", "reverb_mix", "drift", "master_volume"}
        for change in mutation_changes:
            assert change.parameter in valid_params
    
    def test_config_integration(self):
        """Test that mutation config is properly used."""
        config = MutationConfig(
            interval_min_s=10,
            interval_max_s=20,
            max_changes_per_cycle=3
        )
        
        state = State()
        engine = MutationEngine(config, state)
        
        # Check that config values are used
        assert engine.config.interval_min_s == 10
        assert engine.config.interval_max_s == 20
        assert engine.config.max_changes_per_cycle == 3
        
        # Force mutation should respect max_changes_per_cycle
        engine.force_mutation()
        
        # Count recent mutations (within last second)
        recent_time = time.time() - 1.0
        recent_mutations = [m for m in engine._history if m.timestamp >= recent_time]
        assert len(recent_mutations) <= 3
