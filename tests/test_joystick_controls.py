"""Tests for new joystick tempo and direction controls."""

import pytest
from src.action_handler import ActionHandler
from src.state import State
from src.sequencer import Sequencer
from src.events import SemanticEvent


@pytest.fixture
def test_setup():
    """Set up test components."""
    state = State()
    action_handler = ActionHandler(state)
    sequencer = Sequencer(state, ['major', 'minor', 'pentatonic'])
    action_handler.set_sequencer(sequencer)
    
    # Set initial values
    state.set('bpm', 120.0)
    state.set('direction_pattern', 'forward')
    
    return state, action_handler, sequencer


def test_tempo_up_control(test_setup):
    """Test tempo up joystick control."""
    state, action_handler, sequencer = test_setup
    
    # Test tempo increase
    event = SemanticEvent(type='tempo_up', value=127, source='test')
    action_handler.handle_semantic_event(event)
    
    assert state.get('bpm') == 125.0  # 120 + 5
    
    # Test another increase
    action_handler.handle_semantic_event(event)
    assert state.get('bpm') == 130.0  # 125 + 5


def test_tempo_down_control(test_setup):
    """Test tempo down joystick control."""
    state, action_handler, sequencer = test_setup
    
    # Test tempo decrease
    event = SemanticEvent(type='tempo_down', value=127, source='test')
    action_handler.handle_semantic_event(event)
    
    assert state.get('bpm') == 115.0  # 120 - 5
    
    # Test another decrease
    action_handler.handle_semantic_event(event)
    assert state.get('bpm') == 110.0  # 115 - 5


def test_tempo_limits(test_setup):
    """Test tempo control respects BPM limits."""
    state, action_handler, sequencer = test_setup
    
    # Test minimum limit
    state.set('bpm', 60.0)
    event = SemanticEvent(type='tempo_down', value=127, source='test')
    action_handler.handle_semantic_event(event)
    assert state.get('bpm') == 60.0  # Should not go below 60
    
    # Test maximum limit
    state.set('bpm', 200.0)
    event = SemanticEvent(type='tempo_up', value=127, source='test')
    action_handler.handle_semantic_event(event)
    assert state.get('bpm') == 200.0  # Should not go above 200


def test_direction_right_control(test_setup):
    """Test direction right joystick control."""
    state, action_handler, sequencer = test_setup
    
    # Test direction cycle: forward -> backward
    event = SemanticEvent(type='direction_right', value=127, source='test')
    action_handler.handle_semantic_event(event)
    assert state.get('direction_pattern') == 'backward'
    
    # Test direction cycle: backward -> ping_pong
    action_handler.handle_semantic_event(event)
    assert state.get('direction_pattern') == 'ping_pong'
    
    # Test direction cycle: ping_pong -> random
    action_handler.handle_semantic_event(event)
    assert state.get('direction_pattern') == 'random'


def test_direction_left_control(test_setup):
    """Test direction left joystick control."""
    state, action_handler, sequencer = test_setup
    
    # Start with backward pattern
    state.set('direction_pattern', 'backward')
    
    # Test direction cycle: backward -> forward
    event = SemanticEvent(type='direction_left', value=127, source='test')
    action_handler.handle_semantic_event(event)
    assert state.get('direction_pattern') == 'forward'
    
    # Test wraparound: forward -> song (last pattern)
    action_handler.handle_semantic_event(event)
    assert state.get('direction_pattern') == 'song'


def test_direction_full_cycle(test_setup):
    """Test full direction pattern cycle."""
    state, action_handler, sequencer = test_setup
    
    expected_patterns = ['forward', 'backward', 'ping_pong', 'random', 'fugue', 'song']
    
    # Test forward cycle through all patterns
    event_right = SemanticEvent(type='direction_right', value=127, source='test')
    
    for i in range(1, len(expected_patterns)):
        action_handler.handle_semantic_event(event_right)
        assert state.get('direction_pattern') == expected_patterns[i]
    
    # Test wraparound back to forward
    action_handler.handle_semantic_event(event_right)
    assert state.get('direction_pattern') == 'forward'


def test_joystick_press_only_response(test_setup):
    """Test that joystick controls only respond to press (127), not release (0)."""
    state, action_handler, sequencer = test_setup
    
    initial_bpm = state.get('bpm')
    initial_direction = state.get('direction_pattern')
    
    # Test tempo controls ignore release (value=0)
    event_release = SemanticEvent(type='tempo_up', value=0, source='test')
    action_handler.handle_semantic_event(event_release)
    assert state.get('bpm') == initial_bpm  # Should not change
    
    event_release = SemanticEvent(type='tempo_down', value=0, source='test')
    action_handler.handle_semantic_event(event_release)
    assert state.get('bpm') == initial_bpm  # Should not change
    
    # Test direction controls ignore release (value=0)
    event_release = SemanticEvent(type='direction_right', value=0, source='test')
    action_handler.handle_semantic_event(event_release)
    assert state.get('direction_pattern') == initial_direction  # Should not change
    
    event_release = SemanticEvent(type='direction_left', value=0, source='test')
    action_handler.handle_semantic_event(event_release)
    assert state.get('direction_pattern') == initial_direction  # Should not change


def test_joystick_action_handler_registration(test_setup):
    """Test that joystick action handlers are properly registered."""
    state, action_handler, sequencer = test_setup
    
    # Check that all new joystick handlers are registered
    joystick_actions = ['tempo_up', 'tempo_down', 'direction_left', 'direction_right']
    
    for action in joystick_actions:
        assert action in action_handler._action_handlers, f"Handler for '{action}' not registered"
