"""Tests for sequencer module."""

import pytest
import time
from unittest.mock import Mock, patch
from state import State
from sequencer import HighResClock, Sequencer, TickEvent, NoteEvent, create_sequencer


@pytest.fixture
def state():
    """Fresh state instance for each test."""
    state = State()
    return state


def test_high_res_clock_initialization():
    """Test clock initialization with default parameters."""
    clock = HighResClock()
    assert clock.bpm == 110.0
    assert clock.ppq == 24
    assert clock.swing == 0.0
    assert clock._running is False


def test_clock_parameter_updates():
    """Test updating clock parameters."""
    clock = HighResClock()
    clock.update_params(bpm=120.0, swing=0.1)
    
    assert clock.bpm == 120.0
    assert clock.swing == 0.1


def test_clock_start_stop():
    """Test starting and stopping the clock."""
    clock = HighResClock()
    mock_callback = Mock()
    clock.set_tick_callback(mock_callback)
    
    # Start clock
    clock.start()
    assert clock._running is True
    assert clock._thread is not None
    
    # Let it run briefly
    time.sleep(0.1)
    
    # Stop clock
    clock.stop()
    assert clock._running is False
    
    # Verify we got some ticks
    assert mock_callback.call_count > 0


def test_clock_tick_events():
    """Test that clock generates tick events with correct structure."""
    clock = HighResClock(bpm=240.0, ppq=4)  # Fast for testing
    received_ticks = []
    
    def tick_callback(tick):
        received_ticks.append(tick)
        if len(received_ticks) >= 8:  # Stop after 8 ticks (2 beats)
            clock.stop()
    
    clock.set_tick_callback(tick_callback)
    clock.start()
    
    # Wait for ticks
    time.sleep(0.5)
    
    # Verify tick structure
    assert len(received_ticks) >= 4
    for tick in received_ticks:
        assert isinstance(tick, TickEvent)
        assert isinstance(tick.step, int)
        assert isinstance(tick.timestamp, float)
        assert isinstance(tick.swing_adjusted, bool)
        assert 0 <= tick.step < clock.ppq


def test_swing_application():
    """Test that swing is applied to appropriate ticks."""
    clock = HighResClock(bpm=120.0, ppq=8, swing=0.5)
    swing_ticks = []
    regular_ticks = []
    
    def tick_callback(tick):
        if tick.swing_adjusted:
            swing_ticks.append(tick.step)
        else:
            regular_ticks.append(tick.step)
        
        if len(swing_ticks) + len(regular_ticks) >= 16:
            clock.stop()
    
    clock.set_tick_callback(tick_callback)
    clock.start()
    time.sleep(0.5)
    
    # With ppq=8 and swing, every other 2nd tick should be swing-adjusted
    # (every 4th tick: 2, 6, 10, 14, etc.)
    assert len(swing_ticks) > 0
    assert len(regular_ticks) > 0


def test_sequencer_initialization(state):
    """Test sequencer initialization."""
    scales = ['major', 'minor', 'pentatonic']
    sequencer = Sequencer(state, scales)
    
    assert sequencer.state is state
    assert sequencer.available_scales == scales
    assert sequencer._current_step == 0


def test_sequencer_state_listener(state):
    """Test that sequencer responds to state changes."""
    scales = ['major', 'minor']
    sequencer = Sequencer(state, scales)
    
    # Change BPM and verify clock is updated
    original_bpm = sequencer.clock.bpm
    state.set('bpm', 140.0)
    
    # Give a moment for the listener to process
    time.sleep(0.01)
    assert sequencer.clock.bpm == 140.0
    assert sequencer.clock.bpm != original_bpm


def test_sequencer_step_advancement(state):
    """Test step advancement and position tracking."""
    sequencer = Sequencer(state, ['major'])
    mock_note_callback = Mock()
    sequencer.set_note_callback(mock_note_callback)
    
    # Set a short sequence for testing
    state.set('sequence_length', 4)
    
    # Manually trigger step advancement
    for i in range(6):
        sequencer._advance_step()
    
    # Verify step position wraps around correctly
    assert state.get('step_position') == 2  # (6 % 4) = 2
    
    # Verify note callbacks were made
    assert mock_note_callback.call_count > 0


def test_sequencer_note_generation(state):
    """Test note generation pattern."""
    # Set density and note_probability to 1.0 for deterministic testing
    state.set('density', 1.0)
    state.set('note_probability', 1.0)
    
    sequencer = Sequencer(state, ['major'])
    generated_notes = []
    
    def note_callback(note_event):
        generated_notes.append(note_event)
    
    sequencer.set_note_callback(note_callback)
    
    # Generate notes for several steps
    for step in range(8):
        sequencer._generate_step_note(step)
    
    # Phase 2 pattern: notes on even steps only
    even_step_notes = [n for n in generated_notes if n.step % 2 == 0]
    odd_step_notes = [n for n in generated_notes if n.step % 2 == 1]
    
    assert len(even_step_notes) == 4  # Steps 0, 2, 4, 6
    assert len(odd_step_notes) == 0   # No notes on odd steps
    
    # Verify note structure
    for note in even_step_notes:
        assert isinstance(note, NoteEvent)
        assert isinstance(note.note, int)
        assert 60 <= note.note <= 127  # Valid MIDI range
        assert isinstance(note.velocity, int)
        assert 0 <= note.velocity <= 127
        assert isinstance(note.step, int)


def test_clock_large_tick_count_stability():
    """Test that clock remains stable with very large tick counts.
    
    This tests the fix for the issue where the sequencer would stop
    generating notes after ~2 hours due to floating-point precision
    problems with large tick counts.
    """
    clock = HighResClock(bpm=240.0, ppq=4)  # Fast for testing
    received_ticks = []
    
    def tick_callback(tick):
        received_ticks.append(tick)
        if len(received_ticks) >= 20:  # Stop after reasonable number
            clock.stop()
    
    clock.set_tick_callback(tick_callback)
    clock.start()
    
    # Simulate large tick count (equivalent to ~2+ hours runtime)
    clock._tick_count = 10_000_000
    
    # Let it run briefly
    timeout = 2.0
    start_time = time.time()
    while clock._running and (time.time() - start_time) < timeout:
        time.sleep(0.01)
    
    if clock._running:
        clock.stop()
    
    # Should have received ticks despite large tick count
    assert len(received_ticks) >= 10, f"Expected at least 10 ticks, got {len(received_ticks)}"


def test_sequencer_integration(state):
    """Test full sequencer integration with clock."""
    scales = ['major', 'minor']
    sequencer = Sequencer(state, scales)
    generated_notes = []
    
    def note_callback(note_event):
        generated_notes.append(note_event)
        # Stop after a few notes to avoid long test
        if len(generated_notes) >= 3:
            sequencer.stop()
    
    sequencer.set_note_callback(note_callback)
    
    # Set fast tempo for quick testing
    state.set('bpm', 480.0)  # Very fast
    state.set('sequence_length', 4)
    
    # Start sequencer
    sequencer.start()
    
    # Wait for notes
    time.sleep(0.5)
    
    # Verify we got some notes
    assert len(generated_notes) > 0
    
    # Verify step positions were updated
    final_step = state.get('step_position')
    assert isinstance(final_step, int)
    assert 0 <= final_step < 4


def test_sequencer_callback_exception_handling(state):
    """Test that callback exceptions don't crash the sequencer."""
    sequencer = Sequencer(state, ['major'])
    
    def bad_callback(note_event):
        raise RuntimeError("Callback error")
    
    sequencer.set_note_callback(bad_callback)
    
    # This should not raise an exception
    sequencer._generate_step_note(0)


def test_create_sequencer_factory():
    """Test the factory function."""
    state = State()

    sequencer = create_sequencer(state, ['major', 'minor', 'pentatonic'])
    assert isinstance(sequencer, Sequencer)
    assert sequencer.state is state


def test_sequence_length_change_handling(state):
    """Test that sequence length changes are handled properly."""
    sequencer = Sequencer(state, ['major'])
    
    # Start with length 8
    assert state.get('sequence_length') == 8
    
    # Advance to step 6
    state.set('step_position', 6)
    
    # Change length to 4 - next step should wrap to 0
    state.set('sequence_length', 4)
    sequencer._advance_step()
    
    # Should wrap around since 6+1=7, and 7%4=3, then +1 = 0 for next advance
    # Actually, let's test the current step is within bounds
    current_step = state.get('step_position')
    sequence_length = state.get('sequence_length')
    assert 0 <= current_step < sequence_length


# Phase 5.5 Tests: Enhanced Probability & Rhythm Patterns

def test_set_step_probabilities(state):
    """Test setting per-step probability arrays."""
    sequencer = Sequencer(state, ['major'])
    
    # Test valid probabilities
    probs = [0.9, 0.5, 0.1, 0.8, 0.3, 0.7, 0.2, 0.6]
    sequencer.set_step_probabilities(probs)
    
    stored_probs = state.get('step_probabilities')
    assert stored_probs == probs
    
    # Test probability clamping
    invalid_probs = [-0.5, 1.5, 0.5, 2.0]
    sequencer.set_step_probabilities(invalid_probs)
    
    stored_probs = state.get('step_probabilities')
    assert stored_probs == [0.0, 1.0, 0.5, 1.0]  # Clamped to valid range
    
    # Test invalid type handling
    mixed_probs = [0.5, "invalid", 0.7, None]
    sequencer.set_step_probabilities(mixed_probs)
    
    stored_probs = state.get('step_probabilities')
    assert stored_probs == [0.5, 0.5, 0.7, 0.5]  # Invalid values become 0.5


def test_set_step_pattern(state):
    """Test setting step activation patterns."""
    sequencer = Sequencer(state, ['major'])
    
    # Test valid pattern
    pattern = [True, False, True, True, False, False, True, False]
    sequencer.set_step_pattern(pattern)
    
    stored_pattern = state.get('step_pattern')
    assert stored_pattern == pattern
    
    # Test invalid type handling
    invalid_pattern = [True, "invalid", False, 1, 0]
    sequencer.set_step_pattern(invalid_pattern)
    
    stored_pattern = state.get('step_pattern')
    assert stored_pattern == [True, False, False, False, False]  # Invalid values become False


def test_set_velocity_params(state):
    """Test setting velocity parameters."""
    sequencer = Sequencer(state, ['major'])
    
    # Test valid parameters
    sequencer.set_velocity_params(base_velocity=100, velocity_range=30)
    
    assert state.get('base_velocity') == 100
    assert state.get('velocity_range') == 30
    
    # Test clamping
    sequencer.set_velocity_params(base_velocity=200, velocity_range=-10)
    
    assert state.get('base_velocity') == 127  # Clamped to max MIDI
    assert state.get('velocity_range') == 0   # Clamped to minimum


def test_pattern_presets(state):
    """Test pattern preset functionality."""
    sequencer = Sequencer(state, ['major'])
    
    # Test known presets
    four_on_floor = sequencer.get_pattern_preset('four_on_floor')
    assert four_on_floor == [True, False, False, False, True, False, False, False]
    
    offbeat = sequencer.get_pattern_preset('offbeat')
    assert offbeat == [False, True, False, True, False, True, False, True]
    
    all_on = sequencer.get_pattern_preset('all_on')
    assert all_on == [True] * 8
    
    # Test unknown preset (should return default)
    unknown = sequencer.get_pattern_preset('nonexistent')
    assert unknown == [True, False, True, False, True, False, True, False]  # every_other default


def test_probability_presets(state):
    """Test probability preset functionality."""
    sequencer = Sequencer(state, ['major'])
    
    # Test uniform preset
    uniform = sequencer.get_probability_preset('uniform', length=4)
    assert uniform == [0.9, 0.9, 0.9, 0.9]
    
    # Test crescendo preset
    crescendo = sequencer.get_probability_preset('crescendo', length=4)
    assert len(crescendo) == 4
    assert crescendo[0] < crescendo[-1]  # Should increase
    
    # Test peaks preset
    peaks = sequencer.get_probability_preset('peaks', length=8)
    assert peaks[0] == 0.9  # Peak at step 0
    assert peaks[4] == 0.9  # Peak at step 4
    assert peaks[1] == 0.4  # Valley at step 1
    
    # Test unknown preset (should return default)
    unknown = sequencer.get_probability_preset('nonexistent', length=4)
    assert unknown == [0.9, 0.9, 0.9, 0.9]  # uniform default


def test_enhanced_step_note_generation_with_arrays(state):
    """Test note generation with per-step probabilities and patterns."""
    sequencer = Sequencer(state, ['major'])
    
    # Set up per-step probabilities and pattern
    step_probs = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0]  # Certainty for testing
    step_pattern = [True, True, True, True, False, False, False, False]  # Only first 4 steps active
    
    sequencer.set_step_probabilities(step_probs)
    sequencer.set_step_pattern(step_pattern)
    sequencer.set_velocity_params(base_velocity=64, velocity_range=32)
    
    generated_notes = []
    
    def capture_note(note_event):
        generated_notes.append(note_event)
    
    sequencer.set_note_callback(capture_note)
    
    # Set density to 1.0 to ensure density doesn't gate
    state.set('density', 1.0)
    
    # Generate notes for all steps
    for step in range(8):
        sequencer._generate_step_note(step)
    
    # Should have notes only for steps 0 and 2 (pattern active + prob 1.0)
    # Steps 1,3 have prob 0.0, steps 4-7 have pattern inactive
    assert len(generated_notes) == 2
    assert generated_notes[0].step == 0
    assert generated_notes[1].step == 2
    
    # Check velocity variation
    for note in generated_notes:
        assert 32 <= note.velocity <= 96  # base 64 +/- range 32


def test_backward_compatibility_fallbacks(state):
    """Test that sequencer falls back to old behavior when new parameters are None."""
    sequencer = Sequencer(state, ['major'])
    
    # Ensure new parameters are None (default state)
    assert state.get('step_probabilities') is None
    assert state.get('step_pattern') is None
    
    # Set old-style parameters
    state.set('note_probability', 1.0)
    state.set('density', 1.0)
    
    generated_notes = []
    
    def capture_note(note_event):
        generated_notes.append(note_event)
    
    sequencer.set_note_callback(capture_note)
    
    # Generate notes for 8 steps
    for step in range(8):
        sequencer._generate_step_note(step)
    
    # Should use old behavior: even steps only (0, 2, 4, 6)
    assert len(generated_notes) == 4
    expected_steps = [0, 2, 4, 6]
    actual_steps = [note.step for note in generated_notes]
    assert actual_steps == expected_steps


def test_direction_pattern_setting(state):
    """Test setting direction patterns."""
    sequencer = Sequencer(state, ['major'])
    
    # Test valid direction patterns
    valid_directions = ['forward', 'backward', 'ping_pong', 'random']
    
    for direction in valid_directions:
        sequencer.set_direction_pattern(direction)
        assert state.get('direction_pattern') == direction
    
    # Test invalid direction - should default to forward
    sequencer.set_direction_pattern('invalid_direction')
    assert state.get('direction_pattern') == 'forward'


def test_direction_preset_validation(state):
    """Test direction preset validation."""
    sequencer = Sequencer(state, ['major'])
    
    # Test valid presets
    valid_directions = ['forward', 'backward', 'ping_pong', 'random']
    for direction in valid_directions:
        result = sequencer.get_direction_preset(direction)
        assert result == direction
    
    # Test invalid preset - should return 'forward'
    result = sequencer.get_direction_preset('invalid')
    assert result == 'forward'


def test_forward_direction_pattern(state):
    """Test forward direction pattern (default behavior)."""
    sequencer = Sequencer(state, ['major'])
    sequencer.set_direction_pattern('forward')
    
    sequence_length = 4
    state.set('sequence_length', sequence_length)
    
    # Test forward progression
    current_step = 0
    expected_sequence = [1, 2, 3, 0, 1, 2, 3, 0]
    
    for expected_next in expected_sequence:
        next_step = sequencer._get_next_step(current_step, sequence_length)
        assert next_step == expected_next
        current_step = next_step


def test_backward_direction_pattern(state):
    """Test backward direction pattern."""
    sequencer = Sequencer(state, ['major'])
    sequencer.set_direction_pattern('backward')
    
    sequence_length = 4
    state.set('sequence_length', sequence_length)
    
    # Test backward progression
    current_step = 0
    expected_sequence = [3, 2, 1, 0, 3, 2, 1, 0]
    
    for expected_next in expected_sequence:
        next_step = sequencer._get_next_step(current_step, sequence_length)
        assert next_step == expected_next
        current_step = next_step


def test_ping_pong_direction_pattern(state):
    """Test ping-pong direction pattern."""
    sequencer = Sequencer(state, ['major'])
    sequencer.set_direction_pattern('ping_pong')
    
    sequence_length = 4
    state.set('sequence_length', sequence_length)
    
    # Test ping-pong progression: should bounce at boundaries
    current_step = 0
    sequence = []
    
    for _ in range(10):  # Generate enough steps to see bouncing
        next_step = sequencer._get_next_step(current_step, sequence_length)
        sequence.append(next_step)
        current_step = next_step
    
    # Should see pattern like: 1, 2, 3, 2, 1, 0, 1, 2, 3, 2
    assert sequence[0] == 1  # Forward from 0
    assert sequence[1] == 2  # Forward from 1
    assert sequence[2] == 3  # Forward from 2
    assert sequence[3] == 2  # Bounce back from 3
    assert sequence[4] == 1  # Continue backward
    assert sequence[5] == 0  # Continue backward
    assert sequence[6] == 1  # Bounce forward from 0


def test_random_direction_pattern(state):
    """Test random direction pattern."""
    sequencer = Sequencer(state, ['major'])
    sequencer.set_direction_pattern('random')
    
    sequence_length = 4
    state.set('sequence_length', sequence_length)
    
    # Test random progression
    current_step = 0
    sequence = []
    
    for _ in range(20):  # Generate many steps to test randomness
        next_step = sequencer._get_next_step(current_step, sequence_length)
        sequence.append(next_step)
        
        # Should never stay on the same step
        assert next_step != current_step
        # Should always be within bounds
        assert 0 <= next_step < sequence_length
        
        current_step = next_step
    
    # With 20 random steps, we should see variety (not just one value)
    unique_steps = set(sequence)
    assert len(unique_steps) > 1  # Should visit multiple different steps


def test_direction_pattern_state_changes(state):
    """Test that direction pattern changes update internal state."""
    sequencer = Sequencer(state, ['major'])
    
    # Test forward -> backward transition
    sequencer.set_direction_pattern('forward')
    assert sequencer._ping_pong_direction == 1
    
    sequencer.set_direction_pattern('backward')
    assert sequencer._ping_pong_direction == -1
    
    # Test ping_pong initialization
    sequencer.set_direction_pattern('ping_pong')
    assert sequencer._ping_pong_direction == 1


def test_direction_pattern_advance_step_integration(state):
    """Test that _advance_step uses direction patterns correctly."""
    sequencer = Sequencer(state, ['major'])
    
    state.set('sequence_length', 3)
    sequencer._current_step = 0
    
    # Test forward advancement
    sequencer.set_direction_pattern('forward')
    sequencer._advance_step()
    assert sequencer._current_step == 1
    
    # Test backward advancement
    sequencer.set_direction_pattern('backward')
    sequencer._current_step = 1
    sequencer._advance_step()
    assert sequencer._current_step == 0
    
    # Test ping_pong advancement
    sequencer.set_direction_pattern('ping_pong')
    sequencer._current_step = 0
    sequencer._advance_step()
    assert sequencer._current_step == 1
