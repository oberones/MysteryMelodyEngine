"""Integration tests for Phase 2 engine components."""

import pytest
import time
from unittest.mock import Mock, patch
from mido import Message
from config import RootConfig
from router import Router
from state import State, reset_state, get_state
from sequencer import create_sequencer, NoteEvent
from action_handler import ActionHandler
from events import SemanticEvent


@pytest.fixture
def config():
    """Test configuration."""
    return RootConfig(
        midi={'input_port': 'test', 'channel': 1},
        mapping={
            'buttons': {'60-69': 'trigger_step'},
            'ccs': {
                '20': 'tempo',
                '21': 'filter_cutoff',
                '22': 'reverb_mix',
                '23': 'swing',
                '24': 'density',
                '25': 'master_volume',
                '50': 'sequence_length',
                '51': 'scale_select',
                '52': 'chaos_lock',
                '60': 'mode',
                '61': 'palette',
                '62': 'drift',
            }
        },
        sequencer={'steps': 8, 'bpm': 120.0, 'swing': 0.1, 'density': 0.8},
        scales=['major', 'minor', 'pentatonic']
    )


@pytest.fixture
def integrated_system(config):
    """Full integrated system for testing."""
    reset_state()
    state = get_state()
    
    # Initialize state from config
    state.update_multiple({
        'bpm': config.sequencer.bpm,
        'swing': config.sequencer.swing,
        'density': config.sequencer.density,
        'sequence_length': config.sequencer.steps,
    }, source='config')
    
    # Create components
    sequencer = create_sequencer(state, config.scales)
    action_handler = ActionHandler(state, sequencer)
    
    # Track generated notes
    generated_notes = []
    def note_callback(note_event):
        generated_notes.append(note_event)
    
    sequencer.set_note_callback(note_callback)
    action_handler.set_note_callback(note_callback)
    
    # Set up semantic event handling
    semantic_events = []
    def handle_semantic(evt):
        semantic_events.append(evt)
        action_handler.handle_semantic_event(evt)
    
    router = Router(config, handle_semantic)
    
    return {
        'state': state,
        'sequencer': sequencer,
        'action_handler': action_handler,
        'router': router,
        'generated_notes': generated_notes,
        'semantic_events': semantic_events,
    }


def test_midi_to_state_integration(integrated_system):
    """Test full MIDI message to state change flow."""
    system = integrated_system
    
    # Send tempo change via MIDI
    tempo_msg = Message('control_change', channel=0, control=20, value=100)
    system['router'].route(tempo_msg)
    
    # Verify semantic event was generated
    assert len(system['semantic_events']) == 1
    semantic_event = system['semantic_events'][0]
    assert semantic_event.type == 'tempo'
    assert semantic_event.value == 100
    
    # Verify state was updated
    expected_bpm = 60.0 + (100 / 127.0) * 140.0
    assert abs(system['state'].get('bpm') - expected_bpm) < 1.0


def test_button_trigger_integration(integrated_system):
    """Test button press triggering step advancement and note generation."""
    system = integrated_system
    
    # Send button press
    button_msg = Message('note_on', channel=0, note=64, velocity=100)
    system['router'].route(button_msg)
    
    # Verify semantic event
    assert len(system['semantic_events']) == 1
    semantic_event = system['semantic_events'][0]
    assert semantic_event.type == 'trigger_step'
    assert semantic_event.raw_note == 64
    assert semantic_event.value == 100
    
    # Verify note was generated
    assert len(system['generated_notes']) == 1
    note_event = system['generated_notes'][0]
    assert note_event.note == 64
    assert note_event.velocity == 100
    
    # Verify step position was advanced
    assert system['state'].get('step_position') == 1


def test_sequencer_clock_integration(integrated_system):
    """Test sequencer running with clock generating steps."""
    system = integrated_system
    
    # Set very fast tempo for quick testing
    system['state'].set('bpm', 960.0)  # Very fast
    system['state'].set('sequence_length', 4)
    
    # Set up step pattern for note generation (required since Phase 5.5)
    system['sequencer'].set_step_pattern([True, True, True, True])  # All steps active
    system['sequencer'].set_step_probabilities([1.0, 1.0, 1.0, 1.0])  # 100% probability
    
    # Start sequencer
    system['sequencer'].start()
    
    # Wait for some steps
    time.sleep(0.2)
    
    # Stop sequencer
    system['sequencer'].stop()
    
    # Verify notes were generated
    assert len(system['generated_notes']) > 0
    
    # Verify step position was updated
    final_step = system['state'].get('step_position')
    assert isinstance(final_step, int)
    assert 0 <= final_step < 4


def test_parameter_change_affects_sequencer(integrated_system):
    """Test that parameter changes affect the running sequencer."""
    system = integrated_system
    
    # Start with one BPM
    initial_bpm = 120.0
    system['state'].set('bpm', initial_bpm)
    
    # Start sequencer
    system['sequencer'].start()
    
    # Change BPM via MIDI
    new_bpm_cc = 80  # Should map to ~148 BPM
    tempo_msg = Message('control_change', channel=0, control=20, value=new_bpm_cc)
    system['router'].route(tempo_msg)
    
    # Give time for change to propagate
    time.sleep(0.01)
    
    # Verify sequencer clock was updated
    expected_bpm = 60.0 + (new_bpm_cc / 127.0) * 140.0
    assert abs(system['sequencer'].clock.bpm - expected_bpm) < 1.0
    
    system['sequencer'].stop()


def test_swing_parameter_integration(integrated_system):
    """Test swing parameter changes affecting sequencer."""
    system = integrated_system
    
    # Set swing via MIDI
    swing_msg = Message('control_change', channel=0, control=23, value=64)
    system['router'].route(swing_msg)
    
    # Verify state change
    expected_swing = (64 / 127.0) * 0.5
    assert abs(system['state'].get('swing') - expected_swing) < 0.01
    
    # Verify sequencer clock was updated
    assert abs(system['sequencer'].clock.swing - expected_swing) < 0.01


def test_sequence_length_change_integration(integrated_system):
    """Test sequence length changes affecting sequencer behavior."""
    system = integrated_system
    
    # Change sequence length via MIDI
    length_msg = Message('control_change', channel=0, control=50, value=32)  # Should map to ~9 steps
    system['router'].route(length_msg)
    
    # Verify state change
    new_length = system['state'].get('sequence_length')
    assert new_length > 1
    
    # Advance steps and verify wrapping works with new length
    for i in range(new_length + 2):
        system['sequencer']._advance_step()
    
    # Should have wrapped around
    final_step = system['state'].get('step_position')
    assert 0 <= final_step < new_length


def test_multiple_parameter_changes(integrated_system):
    """Test handling multiple parameter changes in sequence."""
    system = integrated_system
    
    # Send multiple CC messages
    messages = [
        Message('control_change', channel=0, control=20, value=80),   # tempo
        Message('control_change', channel=0, control=23, value=40),   # swing
        Message('control_change', channel=0, control=24, value=90),   # density
        Message('control_change', channel=0, control=50, value=60),   # sequence_length
    ]
    
    for msg in messages:
        system['router'].route(msg)
    
    # Verify all semantic events were generated
    assert len(system['semantic_events']) == 4
    
    # Verify state changes
    assert system['state'].get('bpm') > 60.0
    assert system['state'].get('swing') > 0.0
    assert system['state'].get('density') > 0.7
    assert system['state'].get('sequence_length') > 8


def test_invalid_channel_filtering(integrated_system):
    """Test that messages on wrong channel are filtered out."""
    system = integrated_system
    
    # Send message on channel 1 (config expects channel 0 in mido terms)
    wrong_channel_msg = Message('control_change', channel=1, control=20, value=100)
    system['router'].route(wrong_channel_msg)
    
    # Should not generate semantic events
    assert len(system['semantic_events']) == 0


def test_note_off_filtering(integrated_system):
    """Test that note_off messages are filtered out."""
    system = integrated_system
    
    # Send note_off message
    note_off_msg = Message('note_off', channel=0, note=64, velocity=0)
    system['router'].route(note_off_msg)
    
    # Should not generate semantic events
    assert len(system['semantic_events']) == 0


def test_unknown_cc_filtering(integrated_system):
    """Test that unknown CC messages are filtered out."""
    system = integrated_system
    
    # Send CC on unmapped controller
    unknown_cc_msg = Message('control_change', channel=0, control=99, value=50)
    system['router'].route(unknown_cc_msg)
    
    # Should not generate semantic events
    assert len(system['semantic_events']) == 0


def test_state_change_listener_integration(integrated_system):
    """Test that state change listeners work in integrated system."""
    system = integrated_system
    
    # Add a test listener
    state_changes = []
    def test_listener(change):
        state_changes.append(change)
    
    system['state'].add_listener(test_listener)
    
    # Make a change via MIDI
    tempo_msg = Message('control_change', channel=0, control=20, value=64)
    system['router'].route(tempo_msg)
    
    # Verify listener was called
    assert len(state_changes) == 1
    change = state_changes[0]
    assert change.parameter == 'bpm'
    assert change.source == 'midi'


def test_error_handling_integration(integrated_system):
    """Test error handling in integrated system."""
    system = integrated_system
    
    # Set up a bad note callback that raises an exception
    def bad_callback(note_event):
        raise RuntimeError("Test error")
    
    system['action_handler'].set_note_callback(bad_callback)
    
    # Send button press - should not crash
    button_msg = Message('note_on', channel=0, note=60, velocity=100)
    system['router'].route(button_msg)
    
    # Should still generate semantic event despite callback error
    assert len(system['semantic_events']) == 1


def test_config_initialization_integration(integrated_system):
    """Test that config values are properly applied to system."""
    system = integrated_system
    
    # Verify state was initialized from config
    assert system['state'].get('bpm') == 120.0
    assert system['state'].get('swing') == 0.1
    assert system['state'].get('density') == 0.8
    assert system['state'].get('sequence_length') == 8
    
    # Verify sequencer has correct scales
    assert system['sequencer'].available_scales == ['major', 'minor', 'pentatonic']
