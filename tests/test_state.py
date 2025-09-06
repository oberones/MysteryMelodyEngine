"""Tests for state management module."""

import pytest
import time
from unittest.mock import Mock
from state import State, StateChange, get_state, reset_state


@pytest.fixture
def state():
    """Fresh state instance for each test."""
    reset_state()
    return get_state()


def test_state_initialization(state):
    """Test that state initializes with default values."""
    assert state.get('bpm') == 110.0
    assert state.get('swing') == 0.12
    assert state.get('density') == 0.85
    assert state.get('sequence_length') == 8
    assert state.get('scale_index') == 0
    assert state.get('root_note') == 60
    assert state.get('chaos_lock') is False
    assert state.get('idle_mode') is False
    assert state.get('step_position') == 0


def test_parameter_validation():
    """Test parameter validation and clamping."""
    state = State()
    
    # BPM validation
    assert state.set('bpm', 0.5) is True  # Below min, should clamp
    assert state.get('bpm') == 1.0
    assert state.set('bpm', 250.0) is True  # Above max, should clamp
    assert state.get('bpm') == 200.0
    
    # Swing validation
    assert state.set('swing', -0.1) is True  # Below min
    assert state.get('swing') == 0.0
    assert state.set('swing', 0.8) is True  # Above max
    assert state.get('swing') == 0.5
    
    # Density validation
    assert state.set('density', -0.1) is True
    assert state.get('density') == 0.0
    assert state.set('density', 1.5) is True
    assert state.get('density') == 1.0
    
    # Sequence length validation
    assert state.set('sequence_length', 0) is True
    assert state.get('sequence_length') == 1
    assert state.set('sequence_length', 50) is True
    assert state.get('sequence_length') == 32
    
    # Root note validation
    assert state.set('root_note', -10) is True  # Below min
    assert state.get('root_note') == 0
    assert state.set('root_note', 150) is True  # Above max
    assert state.get('root_note') == 127


def test_change_listeners():
    """Test that change listeners are called correctly."""
    state = State()
    mock_listener = Mock()
    state.add_listener(mock_listener)
    
    # Make a change
    result = state.set('bpm', 120.0, source='test')
    assert result is True
    
    # Verify listener was called
    mock_listener.assert_called_once()
    change = mock_listener.call_args[0][0]
    assert isinstance(change, StateChange)
    assert change.parameter == 'bpm'
    assert change.old_value == 110.0  # Default value
    assert change.new_value == 120.0
    assert change.source == 'test'
    assert isinstance(change.timestamp, float)


def test_no_change_no_notification():
    """Test that setting the same value doesn't trigger notifications."""
    state = State()
    mock_listener = Mock()
    state.add_listener(mock_listener)
    
    # Set initial value
    state.set('bpm', 120.0)
    mock_listener.reset_mock()
    
    # Set same value again
    result = state.set('bpm', 120.0)
    assert result is False  # No change
    mock_listener.assert_not_called()


def test_listener_exception_handling():
    """Test that listener exceptions don't break state updates."""
    state = State()
    
    def bad_listener(change):
        raise RuntimeError("Listener error")
    
    def good_listener(change):
        good_listener.called = True
    
    good_listener.called = False
    
    state.add_listener(bad_listener)
    state.add_listener(good_listener)
    
    # Should not raise exception
    result = state.set('bpm', 120.0)
    assert result is True
    assert state.get('bpm') == 120.0
    assert good_listener.called is True


def test_listener_removal():
    """Test removing listeners."""
    state = State()
    mock_listener = Mock()
    
    state.add_listener(mock_listener)
    state.set('bpm', 120.0)
    assert mock_listener.call_count == 1
    
    state.remove_listener(mock_listener)
    state.set('bpm', 130.0)
    assert mock_listener.call_count == 1  # No additional calls


def test_update_multiple():
    """Test updating multiple parameters atomically."""
    state = State()
    mock_listener = Mock()
    state.add_listener(mock_listener)
    
    updates = {
        'bpm': 120.0,
        'swing': 0.2,
        'density': 0.9
    }
    
    changes = state.update_multiple(updates, source='batch')
    assert changes == 3
    
    # Verify all values were set
    assert state.get('bpm') == 120.0
    assert state.get('swing') == 0.2
    assert state.get('density') == 0.9
    
    # Verify listener was called for each change
    assert mock_listener.call_count == 3


def test_get_all():
    """Test getting all parameters."""
    state = State()
    state.set('bpm', 120.0)
    state.set('swing', 0.2)
    
    all_params = state.get_all()
    assert isinstance(all_params, dict)
    assert all_params['bpm'] == 120.0
    assert all_params['swing'] == 0.2
    
    # Verify it's a copy (mutations don't affect state)
    all_params['bpm'] = 999.0
    assert state.get('bpm') == 120.0


def test_thread_safety():
    """Basic test for thread safety using the lock."""
    state = State()
    
    # This is a basic test - full thread safety would require more complex testing
    import threading
    
    def update_worker():
        for i in range(10):
            state.set('bpm', 100.0 + i)
    
    threads = [threading.Thread(target=update_worker) for _ in range(3)]
    
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    # Should have a valid BPM value without crashes
    bpm = state.get('bpm')
    assert 100.0 <= bpm <= 109.0


def test_global_state_singleton():
    """Test that get_state returns the same instance."""
    reset_state()
    state1 = get_state()
    state2 = get_state()
    assert state1 is state2
    
    # Changes in one should be visible in the other
    state1.set('bpm', 150.0)
    assert state2.get('bpm') == 150.0


def test_unknown_parameter_handling():
    """Test handling of unknown parameters."""
    state = State()
    
    # Should allow unknown parameters but log a warning
    result = state.set('unknown_param', 42)
    assert result is True
    assert state.get('unknown_param') == 42
