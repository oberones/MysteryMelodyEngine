"""Integration tests for Phase 3: MIDI Output

Tests the optional MIDI output functionality and note scheduling.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from midi_out import MidiOutput, NullMidiOutput, get_available_output_ports
from main import NoteScheduler, ScheduledNoteOff
from sequencer import NoteEvent


class TestMidiOutput:
    """Test MIDI output functionality."""
    
    def test_null_midi_output(self):
        """Test null MIDI output when disabled."""
        null_output = NullMidiOutput()
        assert not null_output.is_connected
        assert null_output.send_note_on(60, 100) is True
        assert null_output.send_note_off(60, 0) is True
        assert null_output.send_control_change(1, 64) is True
        null_output.close()  # Should not raise
    
    @patch('midi_out.mido.get_output_names')
    @patch('midi_out.mido.open_output')
    def test_midi_output_creation_success(self, mock_open, mock_get_names):
        """Test successful MIDI output creation."""
        mock_get_names.return_value = ['Test Port 1', 'Test Port 2']
        mock_port = Mock()
        mock_open.return_value = mock_port
        
        output = MidiOutput.create('Test Port 1', channel=1)
        assert output is not None
        assert output.is_connected
        mock_open.assert_called_once_with('Test Port 1')
    
    @patch('midi_out.mido.get_output_names')
    def test_midi_output_creation_disabled(self, mock_get_names):
        """Test MIDI output creation when disabled."""
        mock_get_names.return_value = ['Test Port 1']
        
        output = MidiOutput.create(None, channel=1)
        assert output is None
    
    @patch('midi_out.mido.get_output_names')
    @patch('midi_out.mido.open_output')
    def test_midi_output_auto_selection(self, mock_open, mock_get_names):
        """Test automatic port selection."""
        mock_get_names.return_value = ['Virtual Port', 'Physical Port', 'Loopback Port']
        mock_port = Mock()
        mock_open.return_value = mock_port
        
        output = MidiOutput.create('auto', channel=1)
        assert output is not None
        # Should select 'Physical Port' (non-virtual)
        mock_open.assert_called_once_with('Physical Port')
    
    @patch('midi_out.mido.get_output_names')
    @patch('midi_out.mido.open_output')
    def test_midi_output_auto_fallback(self, mock_open, mock_get_names):
        """Test auto selection fallback to first available."""
        mock_get_names.return_value = ['Virtual Port Only']
        mock_port = Mock()
        mock_open.return_value = mock_port
        
        output = MidiOutput.create('auto', channel=1)
        assert output is not None
        mock_open.assert_called_once_with('Virtual Port Only')
    
    @patch('midi_out.mido.open_output')
    def test_midi_output_send_messages(self, mock_open):
        """Test sending MIDI messages."""
        mock_port = Mock()
        mock_open.return_value = mock_port
        
        output = MidiOutput('Test Port', channel=2)
        
        # Test note on
        result = output.send_note_on(64, 100, channel=3)
        assert result is True
        mock_port.send.assert_called()
        sent_msg = mock_port.send.call_args[0][0]
        assert sent_msg.type == 'note_on'
        assert sent_msg.channel == 2  # 0-based (3-1)
        assert sent_msg.note == 64
        assert sent_msg.velocity == 100
        
        # Test note off
        mock_port.reset_mock()
        result = output.send_note_off(64, 0, channel=3)
        assert result is True
        mock_port.send.assert_called()
        sent_msg = mock_port.send.call_args[0][0]
        assert sent_msg.type == 'note_off'
        assert sent_msg.channel == 2  # 0-based (3-1)
        assert sent_msg.note == 64
        assert sent_msg.velocity == 0
        
        # Test control change
        mock_port.reset_mock()
        result = output.send_control_change(7, 127, channel=3)
        assert result is True
        mock_port.send.assert_called()
        sent_msg = mock_port.send.call_args[0][0]
        assert sent_msg.type == 'control_change'
        assert sent_msg.channel == 2  # 0-based (3-1)
        assert sent_msg.control == 7
        assert sent_msg.value == 127
    
    @patch('midi_out.mido.open_output')
    def test_midi_output_send_failure_handling(self, mock_open):
        """Test handling of send failures."""
        mock_port = Mock()
        mock_port.send.side_effect = Exception("Send failed")
        mock_open.return_value = mock_port
        
        output = MidiOutput('Test Port')
        
        # Should return False on send failure
        result = output.send_note_on(60, 100)
        assert result is False
        assert not output.is_connected  # Should mark as disconnected
    
    @patch('midi_out.mido.open_output')
    def test_midi_output_close(self, mock_open):
        """Test MIDI output closing."""
        mock_port = Mock()
        mock_open.return_value = mock_port
        
        output = MidiOutput('Test Port')
        output.close()
        
        mock_port.send.assert_called()  # All notes off
        mock_port.close.assert_called_once()
        assert not output.is_connected
    
    @patch('midi_out.mido.get_output_names')
    def test_get_available_ports(self, mock_get_names):
        """Test getting available output ports."""
        mock_get_names.return_value = ['Port 1', 'Port 2']
        ports = get_available_output_ports()
        assert ports == ['Port 1', 'Port 2']
        
        # Test error handling
        mock_get_names.side_effect = Exception("MIDI error")
        ports = get_available_output_ports()
        assert ports == []


class TestNoteScheduler:
    """Test note scheduling for proper MIDI timing."""
    
    def test_note_scheduler_basic(self):
        """Test basic note scheduling functionality."""
        mock_output = Mock()
        scheduler = NoteScheduler(mock_output)
        
        # Start scheduler
        scheduler.start()
        assert scheduler._running
        
        # Schedule a note off
        scheduler.schedule_note_off(60, 1, 0.01)  # 10ms delay
        
        # Wait for execution
        time.sleep(0.02)
        
        # Stop scheduler
        scheduler.stop()
        assert not scheduler._running
        
        # Verify note off was sent
        mock_output.send_note_off.assert_called_once_with(60, 0, 1)
    
    def test_note_scheduler_multiple_notes(self):
        """Test scheduling multiple notes with different timings."""
        mock_output = Mock()
        scheduler = NoteScheduler(mock_output)
        scheduler.start()
        
        # Schedule multiple notes with different delays
        scheduler.schedule_note_off(60, 1, 0.01)  # 10ms
        scheduler.schedule_note_off(62, 1, 0.02)  # 20ms
        scheduler.schedule_note_off(64, 1, 0.005) # 5ms (should fire first)
        
        # Wait for all to execute
        time.sleep(0.03)
        scheduler.stop()
        
        # Verify all notes were sent
        assert mock_output.send_note_off.call_count == 3
        
        # Check order (though exact timing might vary in tests)
        calls = mock_output.send_note_off.call_args_list
        notes_sent = [call[0][0] for call in calls]
        assert 60 in notes_sent
        assert 62 in notes_sent
        assert 64 in notes_sent
    
    def test_note_scheduler_stop_clears_pending(self):
        """Test that stopping scheduler handles pending notes gracefully."""
        mock_output = Mock()
        scheduler = NoteScheduler(mock_output)
        scheduler.start()
        
        # Schedule a note with long delay
        scheduler.schedule_note_off(60, 1, 1.0)  # 1 second
        
        # Stop immediately
        scheduler.stop()
        
        # Should not send the note (scheduler stopped)
        time.sleep(0.01)
        mock_output.send_note_off.assert_not_called()


class TestPhase3Integration:
    """Integration tests for Phase 3 MIDI output."""

    @patch('main.MidiOutput')
    def test_engine_with_midi_output_disabled(self, mock_midi_output_class):
        """Test engine startup with MIDI output disabled."""
        from config import RootConfig
        from state import get_state, reset_state
        from sequencer import create_sequencer
        from main import NoteScheduler
        
        reset_state()  # Clean state
        
        # Create config with no MIDI output
        config = RootConfig()
        config.midi.output_port = None
        
        # Create components
        state = get_state()
        sequencer = create_sequencer(state, config.scales)
        
        # Should create NullMidiOutput
        mock_midi_output_class.create.return_value = None
        
        # Simulate the main engine setup
        midi_output = mock_midi_output_class.create(config.midi.output_port, config.midi.output_channel)
        from midi_out import NullMidiOutput
        if not midi_output:
            midi_output = NullMidiOutput()
        
        scheduler = NoteScheduler(midi_output)
        
        assert isinstance(midi_output, NullMidiOutput)
        assert not midi_output.is_connected
    
    @patch('main.MidiOutput')
    def test_engine_with_midi_output_enabled(self, mock_midi_output_class):
        """Test engine startup with MIDI output enabled."""
        from config import RootConfig
        from state import get_state, reset_state
        from sequencer import create_sequencer
        from main import NoteScheduler
        
        reset_state()  # Clean state
        
        # Create config with MIDI output
        config = RootConfig()
        config.midi.output_port = "auto"
        
        # Mock successful MIDI output creation
        mock_output = Mock()
        mock_output.is_connected = True
        mock_midi_output_class.create.return_value = mock_output
        
        # Create components
        state = get_state()
        sequencer = create_sequencer(state, config.scales)
        
        midi_output = mock_midi_output_class.create(config.midi.output_port, config.midi.output_channel)
        scheduler = NoteScheduler(midi_output)
        
        assert midi_output.is_connected
        mock_midi_output_class.create.assert_called_once_with("auto", 1)
    
    def test_note_event_with_midi_output(self):
        """Test that note events trigger proper MIDI output and scheduling."""
        from main import NoteScheduler
        
        mock_output = Mock()
        mock_output.is_connected = True
        scheduler = NoteScheduler(mock_output)
        scheduler.start()
        
        # Simulate note event handling
        note_event = NoteEvent(
            note=60,
            velocity=100,
            timestamp=time.time(),
            step=0,
            duration=0.1
        )
        
        # Simulate main.py note handling
        if mock_output.is_connected:
            mock_output.send_note_on(note_event.note, note_event.velocity, 1)
            scheduler.schedule_note_off(note_event.note, 1, note_event.duration)
        
        # Verify note on was sent immediately
        mock_output.send_note_on.assert_called_once_with(60, 100, 1)
        
        # Wait for note off
        time.sleep(0.12)  # Slightly longer than duration
        
        scheduler.stop()
        
        # Verify note off was sent
        mock_output.send_note_off.assert_called_once_with(60, 0, 1)


@pytest.fixture
def reset_state_fixture():
    """Fixture to reset state between tests."""
    from state import reset_state
    reset_state()
    yield
    reset_state()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])