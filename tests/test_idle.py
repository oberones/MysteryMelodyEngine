"""Tests for idle mode functionality.

Phase 6: Comprehensive testing of idle mode detection, smooth transitions,
and integration with mutation engine and action handlers.
Updated to test smooth transitions and no-restoration behavior.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from state import State, reset_state
from idle import IdleManager, IdleProfile, create_idle_manager
from config import IdleConfig
from action_handler import ActionHandler
from mutation import create_mutation_engine, MutationEngine
from events import SemanticEvent


@pytest.fixture
def state():
    """Fresh state instance for each test."""
    reset_state()
    return State()


@pytest.fixture
def idle_config():
    """Standard idle configuration for testing."""
    return IdleConfig(
        timeout_ms=1000,  # 1 second for fast tests
        ambient_profile="slow_fade",
        fade_in_ms=100,
        fade_out_ms=50
    )


@pytest.fixture
def idle_manager(state, idle_config):
    """Idle manager instance for testing."""
    return create_idle_manager(idle_config, state)


class TestIdleManager:
    """Test idle manager functionality."""
    
    def test_initialization(self, idle_manager, idle_config):
        """Test idle manager initialization."""
        assert idle_manager.config == idle_config
        assert idle_manager.timeout_seconds == 1.0  # 1000ms
        assert not idle_manager.is_idle
        assert not idle_manager.transition.is_transitioning
        assert idle_manager.current_profile is not None
        assert idle_manager.current_profile.name == "slow_fade"
    
    def test_idle_profiles_creation(self, idle_manager):
        """Test that idle profiles are created correctly."""
        profiles = idle_manager.idle_profiles
        
        # Check that expected profiles exist
        assert "slow_fade" in profiles
        assert "minimal" in profiles
        assert "meditative" in profiles
        
        # Check slow_fade profile
        slow_fade = profiles["slow_fade"]
        assert slow_fade.name == "slow_fade"
        assert "density" in slow_fade.params
        assert slow_fade.params["density"] == 0.3
        assert "bpm" in slow_fade.params
        assert slow_fade.params["bpm"] == 65.0
    
    def test_interaction_tracking(self, idle_manager):
        """Test interaction tracking and time calculations."""
        # Initial state
        initial_time = idle_manager.get_time_since_last_interaction()
        assert initial_time >= 0.0
        assert initial_time < 0.1  # Should be very recent
        
        # Touch interaction (preserve_tempo param is now ignored)
        time.sleep(0.1)
        idle_manager.touch()
        new_time = idle_manager.get_time_since_last_interaction()
        assert new_time < initial_time
        
        # Time to idle calculation
        time_to_idle = idle_manager.get_time_to_idle()
        assert time_to_idle > 0.9  # Should be close to 1 second
        assert time_to_idle <= 1.0
    
    def test_manual_idle_control(self, idle_manager, state):
        """Test manual idle mode control with smooth transitions and no restoration."""
        # Set up some initial state
        state.set('density', 0.8, source='test')
        state.set('bpm', 120.0, source='test')
        
        # Force start of idle transition
        idle_manager.force_idle()
        assert idle_manager.transition.is_transitioning
        assert idle_manager.transition.direction == "to_idle"
        assert not idle_manager.is_idle  # Not yet fully idle
        
        # Wait a brief moment for transition to progress
        time.sleep(0.05)
        
        # Values should be transitioning (somewhere between start and target)
        current_density = state.get('density')
        current_bpm = state.get('bpm')
        
        # Force interruption (simulating user interaction)
        idle_manager.force_active()
        assert not idle_manager.is_idle
        assert not idle_manager.transition.is_transitioning
        
        # Values should remain wherever they were during transition (no restoration)
        interrupted_density = state.get('density')
        interrupted_bpm = state.get('bpm')
        assert interrupted_density == current_density  # No change from interruption
        assert interrupted_bpm == current_bpm          # No change from interruption
    
    def test_automatic_idle_detection(self, idle_manager, state):
        """Test automatic idle detection after timeout with smooth transition."""
        # Set up initial state
        state.set('density', 0.9, source='test')
        state.set('bpm', 140.0, source='test')
        
        # Start idle manager
        idle_manager.start()
        
        try:
            # Should not be idle initially
            assert not idle_manager.is_idle
            assert not idle_manager.transition.is_transitioning
            
            # Wait for timeout to trigger transition
            time.sleep(1.1)
            
            # Should be transitioning now
            assert idle_manager.transition.is_transitioning
            assert idle_manager.transition.direction == "to_idle"
            
            # Wait longer for transition to complete
            # Using fade_in_ms from test config (100ms) plus margin
            time.sleep(0.2)
            
            # Should now be fully idle
            assert idle_manager.is_idle
            assert not idle_manager.transition.is_transitioning
            assert state.get('density') == 0.3  # Idle profile applied
            
            # Touch to interrupt idle - no restoration expected
            original_density_before_touch = state.get('density')
            idle_manager.touch()
            
            # Should exit idle mode immediately with no restoration
            assert not idle_manager.is_idle
            assert not idle_manager.transition.is_transitioning
            # Density should remain at idle value (no restoration)
            assert state.get('density') == original_density_before_touch
            
        finally:
            idle_manager.stop()
    
    def test_idle_state_callbacks(self, idle_manager):
        """Test idle state change callbacks - only called when fully idle."""
        callback_mock = Mock()
        idle_manager.add_idle_state_callback(callback_mock)
        
        # Start the idle manager thread
        idle_manager.start()
        
        try:
            # Force idle transition start - should not call callback yet
            idle_manager.force_idle()
            callback_mock.assert_not_called()  # Only transitioning, not yet idle
            
            # Wait for transition to complete (100ms from test config + margin)
            time.sleep(0.15)
            
            # Now should be fully idle and callback should be called
            callback_mock.assert_called_with(True)
            
            callback_mock.reset_mock()
            
            # Force active (interrupt)
            idle_manager.force_active()
            callback_mock.assert_called_with(False)
            
            # Remove callback
            idle_manager.remove_idle_state_callback(callback_mock)
            callback_mock.reset_mock()
            
            # Should not be called anymore
            idle_manager.force_idle()
            time.sleep(0.15)  # Wait for transition
            callback_mock.assert_not_called()
        
        finally:
            idle_manager.stop()
    
    def test_status_reporting(self, idle_manager):
        """Test status reporting functionality."""
        status = idle_manager.get_status()
        
        # Check initial status
        assert 'is_idle' in status
        assert 'is_transitioning' in status
        assert 'transition_direction' in status
        assert 'timeout_seconds' in status
        assert 'time_since_last_interaction' in status
        assert 'time_to_idle' in status
        assert 'current_profile' in status
        
        assert not status['is_idle']
        assert not status['is_transitioning']
        assert status['transition_direction'] == 'none'
        assert status['timeout_seconds'] == 1.0
        assert status['current_profile'] == 'slow_fade'
        
        # Start the idle manager thread
        idle_manager.start()
        
        try:
            # Check status during transition
            idle_manager.force_idle()
            status = idle_manager.get_status()
            assert not status['is_idle']  # Not yet fully idle
            assert status['is_transitioning']
            assert status['transition_direction'] == 'to_idle'
            
            # Check status after transition completes
            time.sleep(0.15)  # Wait for transition
            status = idle_manager.get_status()
            assert status['is_idle']
            assert not status['is_transitioning']
            assert status['transition_direction'] == 'none'
            assert status['time_to_idle'] == -1.0  # Negative when already idle
        
        finally:
            idle_manager.stop()


class TestIdleIntegration:
    """Test idle mode integration with other components."""
    
    def test_action_handler_integration(self, state, idle_config):
        """Test action handler integration with idle manager - no restoration behavior."""
        idle_manager = create_idle_manager(idle_config, state)
        action_handler = ActionHandler(state)
        action_handler.set_idle_manager(idle_manager)
        
        # Start the idle manager thread
        idle_manager.start()
        
        try:
            # Set up initial state
            state.set('bpm', 120.0, source='test')
            state.set('density', 0.8, source='test')
            
            # Force idle mode to completion
            idle_manager.force_idle()
            time.sleep(0.15)  # Wait for transition to complete
            assert idle_manager.is_idle
            
            # Check that idle profile was applied
            assert state.get('bpm') == 65.0  # From slow_fade profile
            assert state.get('density') == 0.3
            
            # Handle any event - should interrupt idle mode with no restoration
            event = SemanticEvent(type='tempo', source='test', value=64, raw_note=None)
            action_handler.handle_semantic_event(event)
            
            # Should have exited idle mode
            assert not idle_manager.is_idle
            assert not idle_manager.transition.is_transitioning
            
            # The action handler will set the new tempo value from the CC
            # No restoration should happen - starts from idle values
            current_bpm = state.get('bpm')
            expected_bpm = 60.0 + (64 / 127.0) * 140.0  # Tempo action mapping
            assert abs(current_bpm - expected_bpm) < 0.1
            
            # Density should remain at idle value (no restoration)
            assert state.get('density') == 0.3  # Still at idle value, no restoration
        
        finally:
            idle_manager.stop()
    
    def test_mutation_engine_integration(self, state, idle_config):
        """Test mutation engine integration with idle mode."""
        from config import MutationConfig
        
        mutation_config = MutationConfig(
            interval_min_s=1,
            interval_max_s=1,
            max_changes_per_cycle=1
        )
        
        idle_manager = create_idle_manager(idle_config, state)
        mutation_engine = create_mutation_engine(mutation_config, state)
        
        # Connect idle manager to mutation engine
        mutation_engine.set_idle_manager(idle_manager)
        
        # Initially mutations should be disabled (before idle state is set)
        assert not mutation_engine.are_mutations_enabled()
        
        # Start idle manager - should keep mutations disabled (not idle yet)
        idle_manager.start()
        time.sleep(0.1)  # Allow callback to process
        assert not mutation_engine.are_mutations_enabled()
        
        # Force idle mode to completion - should enable mutations
        idle_manager.force_idle()
        time.sleep(0.15)  # Wait for transition and callback to process
        assert mutation_engine.are_mutations_enabled()
        
        # Exit idle mode - should disable mutations
        idle_manager.force_active()
        time.sleep(0.1)  # Allow callback to process
        assert not mutation_engine.are_mutations_enabled()
        
        # Clean up
        idle_manager.stop()
        mutation_engine.stop()


class TestIdleNoRestorationBehavior:
    """Test the new no-restoration behavior when exiting idle mode."""
    
    def test_no_restoration_on_interrupt(self, state, idle_config):
        """Test that no parameters are restored when idle is interrupted."""
        idle_manager = create_idle_manager(idle_config, state)
        action_handler = ActionHandler(state)
        action_handler.set_idle_manager(idle_manager)
        
        # Start the idle manager thread
        idle_manager.start()
        
        try:
            # Set initial state
            original_bpm = 130.0
            original_density = 0.9
            state.set('bpm', original_bpm, source='test')
            state.set('density', original_density, source='test')
            
            # Force idle mode to completion
            idle_manager.force_idle()
            time.sleep(0.15)  # Wait for transition to complete
            assert idle_manager.is_idle
            
            # Verify idle profile was applied
            assert state.get('bpm') == 65.0  # From slow_fade profile
            assert state.get('density') == 0.3
            
            # Interrupt idle with any action
            event = SemanticEvent(type='density', source='cc', value=90, raw_note=None)
            action_handler.handle_semantic_event(event)
            
            # Should have exited idle mode
            assert not idle_manager.is_idle
            
            # NO restoration should happen - action applies to current (idle) state
            # BPM should remain at idle value
            assert state.get('bpm') == 65.0  # Still at idle value
            
            # Density should be set by the action to the new value
            expected_density = 90 / 127.0  # Density action mapping
            assert abs(state.get('density') - expected_density) < 0.01
            assert state.get('density') != original_density  # Not restored
        
        finally:
            idle_manager.stop()
    
    def test_smooth_transition_timing(self, state, idle_config):
        """Test that smooth transitions take the expected time."""
        idle_manager = create_idle_manager(idle_config, state)
        
        # Start the idle manager thread
        idle_manager.start()
        
        try:
            # Set initial state
            state.set('density', 0.8, source='test')
            
            # Force idle transition
            start_time = time.time()
            idle_manager.force_idle()
            
            # Should be transitioning immediately
            assert idle_manager.transition.is_transitioning
            assert idle_manager.transition.direction == "to_idle"
            
            # Wait for transition to complete (fade_in_ms from test config = 100ms)
            time.sleep(0.15)
            
            # Should be fully idle now
            assert idle_manager.is_idle
            assert not idle_manager.transition.is_transitioning
            
            elapsed_ms = (time.time() - start_time) * 1000
            # Should have taken approximately the fade_in_ms time
            assert elapsed_ms >= 100  # At least the fade time
            assert elapsed_ms < 200   # But not too much longer
        
        finally:
            idle_manager.stop()
    
    def test_interrupt_during_transition(self, state, idle_config):
        """Test interrupting idle transition before it completes."""
        idle_manager = create_idle_manager(idle_config, state)
        
        # Start the idle manager thread
        idle_manager.start()
        
        try:
            # Set initial state
            state.set('density', 0.8, source='test')
            state.set('bpm', 120.0, source='test')
            
            # Start idle transition
            idle_manager.force_idle()
            assert idle_manager.transition.is_transitioning
            
            # Wait enough for transition to begin but not complete
            time.sleep(0.05)  # Half the transition time
            
            # Should still be transitioning (not complete yet)
            assert idle_manager.transition.is_transitioning
            assert not idle_manager.is_idle
            
            # Interrupt the transition
            idle_manager.force_active()
            
            # Should stop transitioning immediately
            assert not idle_manager.transition.is_transitioning
            assert not idle_manager.is_idle
            
            # Values may or may not have changed depending on timing,
            # but the key point is that we don't restore them
            current_density = state.get('density')
            current_bpm = state.get('bpm')
            
            # These should be whatever they were when interrupted
            # (no restoration to original values)
            assert current_density is not None
            assert current_bpm is not None
            
            # The important thing is we interrupted successfully
            # and aren't trying to restore original state
        
        finally:
            idle_manager.stop()


class TestIdleManagerEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_multiple_idle_transitions(self, idle_manager, state):
        """Test multiple rapid idle transitions."""
        # Start the idle manager thread
        idle_manager.start()
        
        try:
            # Set initial state
            state.set('density', 0.7, source='test')
            
            # Multiple rapid transitions
            for _ in range(3):
                idle_manager.force_idle()
                assert idle_manager.transition.is_transitioning or idle_manager.is_idle
                
                # Wait a moment for possible transition
                time.sleep(0.05)
                
                idle_manager.force_active()
                assert not idle_manager.is_idle
                assert not idle_manager.transition.is_transitioning
            
            # Final state should depend on where the transitions left off
            final_density = state.get('density')
            # Should be different from original since transitions occurred
            assert final_density != 0.7
        
        finally:
            idle_manager.stop()
    
    def test_idle_with_missing_profile_params(self, state, idle_config):
        """Test idle mode when some profile parameters don't exist in state."""
        # Create idle manager with a custom profile
        idle_manager = create_idle_manager(idle_config, state)
        
        # Start the idle manager thread
        idle_manager.start()
        
        try:
            # Set only some of the parameters that the idle profile expects
            state.set('density', 0.8, source='test')
            # Don't set 'bpm' - it should get the default
            
            # Enter idle mode - should not crash
            idle_manager.force_idle()
            time.sleep(0.15)  # Wait for transition to complete
            assert idle_manager.is_idle
            
            # Exit idle mode - no restoration expected
            idle_manager.force_active()
            assert not idle_manager.is_idle
            # No specific assertions about values since no restoration happens
        
        finally:
            idle_manager.stop()
    
    def test_callback_exception_handling(self, idle_manager):
        """Test that callback exceptions don't break idle mode."""
        def bad_callback(is_idle):
            raise RuntimeError("Callback error")
        
        def good_callback(is_idle):
            good_callback.called = True
            good_callback.is_idle = is_idle
        
        good_callback.called = False
        
        idle_manager.add_idle_state_callback(bad_callback)
        idle_manager.add_idle_state_callback(good_callback)
        
        # Start the idle manager thread
        idle_manager.start()
        
        try:
            # Should not raise exception despite bad callback
            idle_manager.force_idle()
            time.sleep(0.15)  # Wait for transition to complete
            assert idle_manager.is_idle
            assert good_callback.called
            assert good_callback.is_idle
        
        finally:
            idle_manager.stop()


def test_create_idle_manager_factory():
    """Test the factory function for creating idle managers."""
    state = State()
    config = IdleConfig(timeout_ms=5000, ambient_profile="minimal")
    
    manager = create_idle_manager(config, state)
    
    assert isinstance(manager, IdleManager)
    assert manager.config == config
    assert manager.state == state
    assert manager.timeout_seconds == 5.0
    assert manager.current_profile.name == "minimal"
    assert manager.timeout_seconds == 5.0
    assert manager.current_profile.name == "minimal"


def test_create_idle_manager_factory():
    """Test the factory function for creating idle managers."""
    state = State()
    config = IdleConfig(timeout_ms=5000, ambient_profile="minimal")
    
    manager = create_idle_manager(config, state)
    
    assert isinstance(manager, IdleManager)
    assert manager.config == config
    assert manager.state == state
    assert manager.timeout_seconds == 5.0
    assert manager.current_profile.name == "minimal"
