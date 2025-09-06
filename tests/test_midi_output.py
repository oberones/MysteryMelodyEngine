"""Unit tests for MIDI output module."""

import pytest
from unittest.mock import Mock, patch, call
from midi_out import MidiOutput, NullMidiOutput, get_available_output_ports


class TestMidiOutputUnit:
    """Unit tests for MidiOutput class."""
    
    @patch('midi_out.mido.open_output')
    def test_connection_success(self, mock_open):
        """Test successful MIDI port connection."""
        mock_port = Mock()
        mock_open.return_value = mock_port
        
        output = MidiOutput('Test Port', channel=2)
        assert output.is_connected
        assert output.port_name == 'Test Port'
        assert output.channel == 2
        mock_open.assert_called_once_with('Test Port')
    
    @patch('midi_out.mido.open_output')
    def test_connection_failure(self, mock_open):
        """Test MIDI port connection failure."""
        mock_open.side_effect = Exception("Port not found")
        
        output = MidiOutput('Bad Port')
        assert not output.is_connected
        assert output.port is None
    
    @patch('midi_out.mido.get_output_names')
    @patch('midi_out.mido.open_output')
    def test_auto_port_selection_prefers_non_virtual(self, mock_open, mock_get_names):
        """Test auto port selection prefers non-virtual ports."""
        mock_get_names.return_value = ['Virtual MIDI', 'Hardware Synth', 'Loopback Port']
        mock_port = Mock()
        mock_open.return_value = mock_port
        
        output = MidiOutput('auto')
        assert output.port_name == 'Hardware Synth'
        mock_open.assert_called_once_with('Hardware Synth')
    
    @patch('midi_out.mido.get_output_names')
    @patch('midi_out.mido.open_output')
    def test_auto_port_selection_fallback(self, mock_open, mock_get_names):
        """Test auto port selection falls back to any available port."""
        mock_get_names.return_value = ['Virtual Only']
        mock_port = Mock()
        mock_open.return_value = mock_port
        
        output = MidiOutput('auto')
        assert output.port_name == 'Virtual Only'
        mock_open.assert_called_once_with('Virtual Only')
    
    @patch('midi_out.mido.get_output_names')
    def test_auto_port_no_ports_available(self, mock_get_names):
        """Test auto port selection when no ports available."""
        mock_get_names.return_value = []
        
        output = MidiOutput('auto')
        assert not output.is_connected
    
    @patch('midi_out.mido.open_output')
    def test_ensure_connected_reconnection(self, mock_open):
        """Test reconnection logic when connection is lost."""
        mock_port = Mock()
        mock_open.return_value = mock_port
        
        output = MidiOutput('Test Port')
        assert output.is_connected
        
        # Simulate connection loss
        output._is_connected = False
        
        # Should reconnect on next operation
        result = output._ensure_connected()
        assert result is True
        assert output.is_connected
    
    @patch('midi_out.mido.open_output')
    def test_send_note_on_basic(self, mock_open):
        """Test basic note on sending."""
        mock_port = Mock()
        mock_open.return_value = mock_port
        
        output = MidiOutput('Test Port', channel=1)
        result = output.send_note_on(64, 100)
        
        assert result is True
        mock_port.send.assert_called_once()
        sent_msg = mock_port.send.call_args[0][0]
        assert sent_msg.type == 'note_on'
        assert sent_msg.channel == 0  # 0-based
        assert sent_msg.note == 64
        assert sent_msg.velocity == 100
    
    @patch('midi_out.mido.open_output')
    def test_send_note_on_zero_velocity_converts_to_note_off(self, mock_open):
        """Test that note on with velocity 0 becomes note off."""
        mock_port = Mock()
        mock_open.return_value = mock_port
        
        output = MidiOutput('Test Port')
        result = output.send_note_on(64, 0)
        
        assert result is True
        mock_port.send.assert_called_once()
        sent_msg = mock_port.send.call_args[0][0]
        assert sent_msg.type == 'note_off'
        assert sent_msg.note == 64
        assert sent_msg.velocity == 0
    
    @patch('midi_out.mido.open_output')
    def test_send_note_off_basic(self, mock_open):
        """Test basic note off sending."""
        mock_port = Mock()
        mock_open.return_value = mock_port
        
        output = MidiOutput('Test Port', channel=2)
        result = output.send_note_off(64, 64, channel=3)
        
        assert result is True
        mock_port.send.assert_called_once()
        sent_msg = mock_port.send.call_args[0][0]
        assert sent_msg.type == 'note_off'
        assert sent_msg.channel == 2  # 0-based (channel 3 -> 2)
        assert sent_msg.note == 64
        assert sent_msg.velocity == 64
    
    @patch('midi_out.mido.open_output')
    def test_send_control_change_basic(self, mock_open):
        """Test basic control change sending."""
        mock_port = Mock()
        mock_open.return_value = mock_port
        
        output = MidiOutput('Test Port', channel=1)
        result = output.send_control_change(7, 127, channel=5)
        
        assert result is True
        mock_port.send.assert_called_once()
        sent_msg = mock_port.send.call_args[0][0]
        assert sent_msg.type == 'control_change'
        assert sent_msg.channel == 4  # 0-based (channel 5 -> 4)
        assert sent_msg.control == 7
        assert sent_msg.value == 127
    
    @patch('midi_out.mido.open_output')
    def test_send_all_notes_off(self, mock_open):
        """Test all notes off message."""
        mock_port = Mock()
        mock_open.return_value = mock_port
        
        output = MidiOutput('Test Port', channel=1)
        result = output.send_all_notes_off(channel=2)
        
        assert result is True
        mock_port.send.assert_called_once()
        sent_msg = mock_port.send.call_args[0][0]
        assert sent_msg.type == 'control_change'
        assert sent_msg.channel == 1  # 0-based (channel 2 -> 1)
        assert sent_msg.control == 123  # All Notes Off
        assert sent_msg.value == 0
    
    @patch('midi_out.mido.open_output')
    def test_send_failure_marks_disconnected(self, mock_open):
        """Test that send failures mark connection as lost."""
        mock_port = Mock()
        mock_port.send.side_effect = Exception("Send failed")
        mock_open.return_value = mock_port
        
        output = MidiOutput('Test Port')
        assert output.is_connected
        
        result = output.send_note_on(60, 100)
        assert result is False
        assert not output.is_connected
    
    @patch('midi_out.mido.open_output')
    def test_close_sends_all_notes_off(self, mock_open):
        """Test that closing sends all notes off."""
        mock_port = Mock()
        mock_open.return_value = mock_port
        
        output = MidiOutput('Test Port', channel=3)
        output.close()
        
        # Should send all notes off then close
        calls = mock_port.send.call_args_list
        assert len(calls) == 1
        sent_msg = calls[0][0][0]
        assert sent_msg.type == 'control_change'
        assert sent_msg.control == 123  # All Notes Off
        
        mock_port.close.assert_called_once()
        assert not output.is_connected
    
    @patch('midi_out.mido.open_output')
    def test_close_handles_exceptions(self, mock_open):
        """Test that close handles exceptions gracefully."""
        mock_port = Mock()
        mock_port.send.side_effect = Exception("Send error")
        mock_port.close.side_effect = Exception("Close error")
        mock_open.return_value = mock_port
        
        output = MidiOutput('Test Port')
        
        # Should not raise exceptions
        output.close()
        assert not output.is_connected


class TestNullMidiOutput:
    """Test the null MIDI output implementation."""
    
    def test_null_output_methods(self):
        """Test that all null output methods return success."""
        null_output = NullMidiOutput()
        
        assert null_output.send_note_on(60, 100) is True
        assert null_output.send_note_off(60, 0) is True
        assert null_output.send_control_change(7, 127) is True
        assert null_output.send_all_notes_off() is True
        assert not null_output.is_connected
        
        # Should not raise
        null_output.close()


class TestMidiOutputFactory:
    """Test the MidiOutput factory method."""
    
    @patch('midi_out.MidiOutput.__init__', return_value=None)
    def test_create_with_port_name(self, mock_init):
        """Test factory with specific port name."""
        # Mock successful connection
        with patch.object(MidiOutput, 'is_connected', True):
            result = MidiOutput.create('Test Port', channel=2)
            assert result is not None
            mock_init.assert_called_once_with('Test Port', 2)
    
    def test_create_disabled(self):
        """Test factory when disabled (None port)."""
        result = MidiOutput.create(None)
        assert result is None
    
    @patch('midi_out.MidiOutput.__init__', return_value=None)
    def test_create_connection_failed(self, mock_init):
        """Test factory when connection fails."""
        # Mock failed connection
        with patch.object(MidiOutput, 'is_connected', False):
            result = MidiOutput.create('Bad Port')
            assert result is None


class TestMidiOutputUtilities:
    """Test utility functions."""
    
    @patch('midi_out.mido.get_output_names')
    def test_get_available_output_ports_success(self, mock_get_names):
        """Test getting available ports successfully."""
        mock_get_names.return_value = ['Port 1', 'Port 2']
        
        ports = get_available_output_ports()
        assert ports == ['Port 1', 'Port 2']
    
    @patch('midi_out.mido.get_output_names')
    def test_get_available_output_ports_error(self, mock_get_names):
        """Test getting available ports with error."""
        mock_get_names.side_effect = Exception("MIDI system error")
        
        ports = get_available_output_ports()
        assert ports == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
