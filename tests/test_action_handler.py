"""Tests for action handler module."""

import pytest
from unittest.mock import Mock
from state import State
from sequencer import Sequencer, NoteEvent
from action_handler import ActionHandler
from events import SemanticEvent


@pytest.fixture
def state():
    """Fresh state instance for each test."""
    return State()


@pytest.fixture
def sequencer(state):
    """Mock sequencer for testing."""
    return Mock(spec=Sequencer)


@pytest.fixture
def handler(state, sequencer):
    """Action handler instance for testing."""
    handler = ActionHandler(state, sequencer)
    return handler


def test_action_handler_initialization(state):
    """Test action handler initialization."""
    handler = ActionHandler(state)
    assert handler.state is state
    assert handler.sequencer is None
    
    # Test with sequencer
    sequencer = Mock()
    handler = ActionHandler(state, sequencer)
    assert handler.sequencer is sequencer


def test_set_sequencer(state):
    """Test setting sequencer after initialization."""
    handler = ActionHandler(state)
    sequencer = Mock()
    
    handler.set_sequencer(sequencer)
    assert handler.sequencer is sequencer


def test_unknown_action_handling(handler):
    """Test handling of unknown action types."""
    event = SemanticEvent(type="unknown_action", source="test")
    
    # Should not raise exception
    handler.handle_semantic_event(event)


def test_tempo_action(handler):
    """Test tempo action handling."""
    # Test minimum value
    event = SemanticEvent(type="tempo", source="cc", value=0, raw_cc=20)
    handler.handle_semantic_event(event)
    assert handler.state.get('bpm') == 60.0
    
    # Test maximum value
    event = SemanticEvent(type="tempo", source="cc", value=127, raw_cc=20)
    handler.handle_semantic_event(event)
    assert handler.state.get('bpm') == 200.0
    
    # Test middle value
    event = SemanticEvent(type="tempo", source="cc", value=64, raw_cc=20)
    handler.handle_semantic_event(event)
    expected_bpm = 60.0 + (64 / 127.0) * 140.0
    assert abs(handler.state.get('bpm') - expected_bpm) < 0.1


def test_swing_action(handler):
    """Test swing action handling."""
    # Test minimum value
    event = SemanticEvent(type="swing", source="cc", value=0, raw_cc=23)
    handler.handle_semantic_event(event)
    assert handler.state.get('swing') == 0.0
    
    # Test maximum value
    event = SemanticEvent(type="swing", source="cc", value=127, raw_cc=23)
    handler.handle_semantic_event(event)
    assert handler.state.get('swing') == 0.5
    
    # Test middle value
    event = SemanticEvent(type="swing", source="cc", value=64, raw_cc=23)
    handler.handle_semantic_event(event)
    expected_swing = (64 / 127.0) * 0.5
    assert abs(handler.state.get('swing') - expected_swing) < 0.01


def test_density_action(handler):
    """Test density action handling."""
    event = SemanticEvent(type="density", source="cc", value=100, raw_cc=24)
    handler.handle_semantic_event(event)
    
    expected_density = 100 / 127.0
    assert abs(handler.state.get('density') - expected_density) < 0.01


def test_sequence_length_action(handler):
    """Test sequence length action handling."""
    # Test minimum value -> length 1
    event = SemanticEvent(type="sequence_length", source="cc", value=0, raw_cc=50)
    handler.handle_semantic_event(event)
    assert handler.state.get('sequence_length') == 1
    
    # Test maximum value -> length 32
    event = SemanticEvent(type="sequence_length", source="cc", value=127, raw_cc=50)
    handler.handle_semantic_event(event)
    assert handler.state.get('sequence_length') == 32
    
    # Test middle value
    event = SemanticEvent(type="sequence_length", source="cc", value=64, raw_cc=50)
    handler.handle_semantic_event(event)
    expected_length = max(1, min(32, 1 + (64 * 31) // 127))
    assert handler.state.get('sequence_length') == expected_length


def test_scale_select_action(handler):
    """Test scale selection action handling."""
    # Test scale index mapping
    event = SemanticEvent(type="scale_select", source="cc", value=0, raw_cc=51)
    handler.handle_semantic_event(event)
    assert handler.state.get('scale_index') == 0
    
    event = SemanticEvent(type="scale_select", source="cc", value=32, raw_cc=51)
    handler.handle_semantic_event(event)
    assert handler.state.get('scale_index') == 2  # 32 // 16 = 2
    
    event = SemanticEvent(type="scale_select", source="cc", value=127, raw_cc=51)
    handler.handle_semantic_event(event)
    assert handler.state.get('scale_index') == 7  # 127 // 16 = 7


def test_chaos_lock_action(handler):
    """Test chaos lock action handling."""
    # Test lock off (value <= 63)
    event = SemanticEvent(type="chaos_lock", source="cc", value=50, raw_cc=52)
    handler.handle_semantic_event(event)
    assert handler.state.get('chaos_lock') is False
    
    # Test lock on (value > 63)
    event = SemanticEvent(type="chaos_lock", source="cc", value=100, raw_cc=52)
    handler.handle_semantic_event(event)
    assert handler.state.get('chaos_lock') is True


def test_mode_action(handler):
    """Test mode action handling."""
    event = SemanticEvent(type="mode", source="cc", value=48, raw_cc=60)
    handler.handle_semantic_event(event)
    assert handler.state.get('mode') == 3  # 48 // 16 = 3


def test_palette_action(handler):
    """Test palette action handling."""
    event = SemanticEvent(type="palette", source="cc", value=80, raw_cc=61)
    handler.handle_semantic_event(event)
    assert handler.state.get('palette') == 5  # 80 // 16 = 5


def test_drift_action(handler):
    """Test drift action handling."""
    # Test center value (no drift)
    event = SemanticEvent(type="drift", source="cc", value=64, raw_cc=62)
    handler.handle_semantic_event(event)
    assert abs(handler.state.get('drift')) < 0.01
    
    # Test maximum positive drift
    event = SemanticEvent(type="drift", source="cc", value=127, raw_cc=62)
    handler.handle_semantic_event(event)
    expected_drift = ((127 - 63.5) / 63.5) * 0.2
    assert abs(handler.state.get('drift') - expected_drift) < 0.01
    
    # Test maximum negative drift
    event = SemanticEvent(type="drift", source="cc", value=0, raw_cc=62)
    handler.handle_semantic_event(event)
    expected_drift = ((0 - 63.5) / 63.5) * 0.2
    assert abs(handler.state.get('drift') - expected_drift) < 0.01


def test_filter_cutoff_action(handler):
    """Test filter cutoff action handling."""
    event = SemanticEvent(type="filter_cutoff", source="cc", value=85, raw_cc=21)
    handler.handle_semantic_event(event)
    assert handler.state.get('filter_cutoff') == 85


def test_reverb_mix_action(handler):
    """Test reverb mix action handling."""
    event = SemanticEvent(type="reverb_mix", source="cc", value=45, raw_cc=22)
    handler.handle_semantic_event(event)
    assert handler.state.get('reverb_mix') == 45


def test_master_volume_action(handler):
    """Test master volume action handling."""
    event = SemanticEvent(type="master_volume", source="cc", value=110, raw_cc=25)
    handler.handle_semantic_event(event)
    assert handler.state.get('master_volume') == 110


def test_trigger_step_action(handler):
    """Test step trigger action handling."""
    # Setup mock note callback
    note_events = []
    def note_callback(note_event):
        note_events.append(note_event)
    
    handler.set_note_callback(note_callback)
    
    # Test step trigger
    event = SemanticEvent(
        type="trigger_step", 
        source="button", 
        value=100, 
        raw_note=64,
        channel=1
    )
    
    initial_step = handler.state.get('step_position')
    handler.handle_semantic_event(event)
    
    # Check that step was advanced
    new_step = handler.state.get('step_position')
    sequence_length = handler.state.get('sequence_length')
    expected_step = (initial_step + 1) % sequence_length
    assert new_step == expected_step
    
    # Check that note event was generated
    assert len(note_events) == 1
    note_event = note_events[0]
    assert note_event.note == 64
    assert note_event.velocity == 100
    assert note_event.step == initial_step


def test_trigger_step_velocity_clamping(handler):
    """Test that trigger step clamps velocity properly."""
    note_events = []
    handler.set_note_callback(lambda ne: note_events.append(ne))
    
    # Test high velocity clamping
    event = SemanticEvent(
        type="trigger_step",
        source="button",
        value=150,  # Above max
        raw_note=60
    )
    handler.handle_semantic_event(event)
    assert note_events[0].velocity == 127
    
    # Test low velocity clamping
    note_events.clear()
    event = SemanticEvent(
        type="trigger_step",
        source="button",
        value=30,  # Below min
        raw_note=60
    )
    handler.handle_semantic_event(event)
    assert note_events[0].velocity == 60


def test_reserved_action(handler):
    """Test reserved action handling (should be a no-op)."""
    event = SemanticEvent(type="reserved", source="cc", value=42, raw_cc=53)
    
    # Should not raise exception
    handler.handle_semantic_event(event)


def test_action_handler_exception_handling(handler):
    """Test that action handler exceptions are caught and logged."""
    # Create a handler with a state that will cause validation errors
    event = SemanticEvent(type="tempo", source="cc", value=None)  # None value
    
    # Should not raise exception even with None value
    handler.handle_semantic_event(event)


def test_note_callback_setting(handler):
    """Test setting and using note callback."""
    note_events = []
    
    def note_callback(note_event):
        note_events.append(note_event)
    
    handler.set_note_callback(note_callback)
    
    # Trigger a note-generating action
    event = SemanticEvent(
        type="trigger_step",
        source="button",
        value=80,
        raw_note=67
    )
    handler.handle_semantic_event(event)
    
    assert len(note_events) == 1
    assert note_events[0].note == 67
    assert note_events[0].velocity == 80


def test_note_probability_action(handler, state):
    """Test note_probability action handling."""
    # Test normal range
    event = SemanticEvent(type="note_probability", source="cc", value=64)
    handler.handle_semantic_event(event)
    expected = 64 / 127.0  # 0.504
    assert abs(state.get('note_probability') - expected) < 0.001
    
    # Test edge cases
    event = SemanticEvent(type="note_probability", source="cc", value=0)
    handler.handle_semantic_event(event)
    assert state.get('note_probability') == 0.0
    
    event = SemanticEvent(type="note_probability", source="cc", value=127)
    handler.handle_semantic_event(event)
    assert state.get('note_probability') == 1.0
