"""
Tests for Phase 4 features: Scale mapping and probability.
"""

import pytest
import time
from unittest.mock import Mock, call

from state import State, get_state, reset_state
from sequencer import Sequencer, NoteEvent
from scale_mapper import ScaleMapper


@pytest.fixture(autouse=True)
def setup_teardown():
    """Fixture to reset state before each test."""
    reset_state()
    yield


def test_scale_mapper_major_scale():
    mapper = ScaleMapper()
    mapper.set_scale("major", root_note=60)  # C4
    # C, D, E, F, G, A, B
    expected_notes = [60, 62, 64, 65, 67, 69, 71]
    for i, expected in enumerate(expected_notes):
        assert mapper.get_note(i) == expected
    # Test octave
    assert mapper.get_note(7) == 72  # Next C


def test_scale_mapper_pentatonic_minor():
    mapper = ScaleMapper()
    mapper.set_scale("pentatonic_minor", root_note=57)  # A3
    # A, C, D, E, G
    expected_notes = [57, 60, 62, 64, 67]
    notes = mapper.get_notes(5)
    assert notes == expected_notes


def test_sequencer_uses_scale_mapper():
    state = get_state()
    scales = ["pentatonic_minor"]
    state.set('scale_index', 0)
    state.set('root_note', 57)  # A3 to match expected notes
    
    sequencer = Sequencer(state, scales)
    mock_note_callback = Mock()
    sequencer.set_note_callback(mock_note_callback)

    # Force density and probability to 1.0 for deterministic test
    state.set('density', 1.0)
    state.set('note_probability', 1.0)
    
    sequencer.start()
    time.sleep(0.5)  # Let it run for a few steps
    sequencer.stop()

    assert mock_note_callback.call_count > 0
    
    # Expected notes from A minor pentatonic scale starting at A3 (root 57)
    # Sequencer plays on even steps (0, 2, 4, 6), mapping to degrees (0, 1, 2, 3)
    expected_notes = [57, 60, 62, 64] 
    
    for i, mock_call in enumerate(mock_note_callback.call_args_list):
        note_event: NoteEvent = mock_call.args[0]
        assert note_event.note == expected_notes[i]


def test_density_and_probability_gating():
    state = get_state()
    scales = ["major"]
    sequencer = Sequencer(state, scales)
    mock_note_callback = Mock()
    sequencer.set_note_callback(mock_note_callback)

    # Test with zero density - no notes should be generated
    state.set('density', 0.0)
    state.set('note_probability', 1.0)
    sequencer.start()
    time.sleep(0.5)
    sequencer.stop()
    mock_note_callback.assert_not_called()

    # Test with zero probability - no notes should be generated
    state.set('density', 1.0)
    state.set('note_probability', 0.0)
    sequencer.start()
    time.sleep(0.5)
    sequencer.stop()
    mock_note_callback.assert_not_called()

def test_quantized_scale_change():
    state = get_state()
    scales = ["major", "minor"]
    sequencer = Sequencer(state, scales)
    
    # Set initial scale to major
    state.set('scale_index', 0, source='test')
    sequencer._update_scale_from_state(force=True) # Force immediate update
    assert sequencer.scale_mapper.current_scale_name == "major"

    # Request a change to minor, should be quantized
    state.set('scale_index', 1, source='test')
    assert sequencer._pending_scale_index == 1
    assert sequencer.scale_mapper.current_scale_name == "major" # Still major

    # Advance to the next bar (step 0)
    sequencer._current_step = sequencer.state.get('sequence_length') - 1
    sequencer._advance_step() # This will wrap around to step 0

    # The scale change should have been applied
    assert sequencer._pending_scale_index is None
    assert sequencer.scale_mapper.current_scale_name == "minor"
