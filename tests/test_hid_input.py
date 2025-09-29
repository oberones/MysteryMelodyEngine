"""Tests for HID input and hybrid input functionality."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from events import SemanticEvent
from hid_input import HidInput
from hybrid_input import HybridInput, HybridInputConfig


class TestHidInput:
    """Test HID input dual backend functionality."""
    
    def test_hid_input_initialization(self):
        """Test HID input dual backend initialization."""
        callback = Mock()
        button_mapping = {0: "trigger_step", 1: "trigger_step"}
        joystick_mapping = {"up": "osc_a", "down": "osc_b"}
        
        hid_input = HidInput(
            device_name="Test Joystick",
            button_mapping=button_mapping,
            joystick_mapping=joystick_mapping,
            callback=callback
        )
        
        assert hid_input.device_name == "Test Joystick"
        assert hid_input.button_mapping == button_mapping
        assert hid_input.joystick_mapping == joystick_mapping
        assert hid_input.callback == callback
        assert hid_input._backend is None  # Not started yet
        assert hid_input._backend_type is None
        
    def test_backend_selection_pygame_success(self):
        """Test pygame backend selection success."""
        callback = Mock()
        hid_input = HidInput("Test", {0: "trigger_step"}, {"up": "osc_a"}, callback)
        
        # Mock pygame backend success
        with patch('hid_input.pygame_available', True), \
             patch('hid_input.PygameHidInput') as mock_pygame_class:
            mock_pygame_instance = Mock()
            mock_pygame_class.return_value = mock_pygame_instance
            
            hid_input.start()
            
            # Verify pygame backend was used
            assert hid_input._backend == mock_pygame_instance
            assert hid_input._backend_type == "pygame"
            mock_pygame_instance.start.assert_called_once()
            
    def test_backend_selection_hidapi_fallback(self):
        """Test hidapi fallback when pygame fails."""
        callback = Mock()
        hid_input = HidInput("Test", {0: "trigger_step"}, {"up": "osc_a"}, callback)
        
        # Mock pygame failure, hidapi success
        with patch('hid_input.pygame_available', True), \
             patch('hid_input.hidapi_available', True), \
             patch('hid_input.PygameHidInput') as mock_pygame_class, \
             patch('hid_input.HidapiInput') as mock_hidapi_class:
            
            mock_pygame_class.side_effect = Exception("pygame failed")
            mock_hidapi_instance = Mock()
            mock_hidapi_class.return_value = mock_hidapi_instance
            
            hid_input.start()
            
            # Verify hidapi fallback was used
            assert hid_input._backend == mock_hidapi_instance
            assert hid_input._backend_type == "hidapi"
            mock_hidapi_instance.start.assert_called_once()
        
    def test_start_no_backends_available(self):
        """Test HID input start with no backends available."""
        callback = Mock()
        hid_input = HidInput("Test", {}, {}, callback)
        
        # Mock no backends available
        with patch('hid_input.pygame_available', False), \
             patch('hid_input.hidapi_available', False):
            with pytest.raises(RuntimeError, match="No HID backend could initialize device"):
                hid_input.start()
    
    def test_start_all_backends_fail(self):
        """Test HID input start when all backends fail."""
        callback = Mock()
        hid_input = HidInput("Test", {}, {}, callback)
        
        # Mock all backends fail
        with patch('hid_input.pygame_available', True), \
             patch('hid_input.hidapi_available', True), \
             patch('hid_input.PygameHidInput') as mock_pygame_class, \
             patch('hid_input.HidapiInput') as mock_hidapi_class:
            
            mock_pygame_class.side_effect = Exception("pygame failed")
            mock_hidapi_class.side_effect = Exception("hidapi failed")
            
            with pytest.raises(RuntimeError, match="No HID backend could initialize device"):
                hid_input.start()
    
    def test_stop_backend(self):
        """Test stopping HID input backend."""
        callback = Mock()
        hid_input = HidInput("Test", {}, {}, callback)
        
        # Mock backend
        mock_backend = Mock()
        hid_input._backend = mock_backend
        hid_input._backend_type = "pygame"
        
        hid_input.stop()
        
        mock_backend.stop.assert_called_once()
        assert hid_input._backend is None
        assert hid_input._backend_type is None


class TestPygameHidInput:
    """Test pygame-specific HID input functionality."""
    
    def test_pygame_button_state_tracking(self):
        """Test pygame backend button state and debouncing."""
        from hid_input import PygameHidInput
        callback = Mock()
        pygame_input = PygameHidInput("Test", {0: "trigger_step"}, {}, callback)
        
        # Check button states initialized
        assert 0 in pygame_input.button_states
        assert not pygame_input.button_states[0].pressed
        assert pygame_input.button_states[0].debounce_time == 0.05
    @patch('pygame.init')
    @patch('pygame.joystick.init')
    @patch('pygame.joystick.get_count', return_value=0)
    @patch('pygame.joystick.quit')
    @patch('pygame.quit')
    def test_pygame_start_no_devices(self, mock_quit, mock_joystick_quit, mock_get_count, 
                              mock_joystick_init, mock_init):
        """Test pygame backend start with no devices."""
        from hid_input import PygameHidInput
        callback = Mock()
        pygame_input = PygameHidInput("Test", {}, {}, callback)
        
        with pytest.raises(RuntimeError, match="pygame joystick 'Test' not found"):
            pygame_input.start()
            
    @patch('pygame.init')
    @patch('pygame.joystick.init')
    @patch('pygame.joystick.get_count', return_value=1)
    @patch('pygame.joystick.quit')
    @patch('pygame.quit')
    def test_pygame_start_with_matching_device(self, mock_quit, mock_joystick_quit,
                                        mock_get_count, mock_joystick_init, mock_init):
        """Test pygame backend start with matching device."""
        from hid_input import PygameHidInput
        callback = Mock()
        pygame_input = PygameHidInput("Generic USB Joystick", {0: "trigger_step"}, {"up": "osc_a"}, callback)
        
        # Mock joystick device
        mock_joystick = Mock()
        mock_joystick.get_name.return_value = "Generic USB Joystick"
        mock_joystick.get_numbuttons.return_value = 10
        mock_joystick.get_numaxes.return_value = 2
        mock_joystick.get_numhats.return_value = 1
        
        with patch('pygame.joystick.Joystick', return_value=mock_joystick):
            with patch.object(pygame_input, '_input_thread'):
                pygame_input.start()
                
                assert pygame_input._joystick == mock_joystick
                mock_joystick.init.assert_called_once()
    
    def test_pygame_hat_to_direction_conversion(self):
        """Test pygame backend hat values to direction string conversion."""
        from hid_input import PygameHidInput
        callback = Mock()
        pygame_input = PygameHidInput("Test", {}, {}, callback)
        
        assert pygame_input._hat_to_direction(0, 1) == "up"
        assert pygame_input._hat_to_direction(0, -1) == "down"
        assert pygame_input._hat_to_direction(-1, 0) == "left"
        assert pygame_input._hat_to_direction(1, 0) == "right"
        assert pygame_input._hat_to_direction(0, 0) is None
    
    def test_pygame_axes_to_direction_conversion(self):
        """Test pygame backend axis values to direction conversion."""
        from hid_input import PygameHidInput
        callback = Mock()
        pygame_input = PygameHidInput("Test", {}, {}, callback)
        
        # Mock joystick
        mock_joystick = Mock()
        mock_joystick.get_numaxes.return_value = 2
        pygame_input._joystick = mock_joystick
        
        # Test different axis values
        mock_joystick.get_axis.side_effect = [0.8, 0.0]  # Right
        assert pygame_input._axes_to_direction() == "right"
        
        mock_joystick.get_axis.side_effect = [-0.8, 0.0]  # Left
        assert pygame_input._axes_to_direction() == "left"
        
        mock_joystick.get_axis.side_effect = [0.0, 0.8]  # Down
        assert pygame_input._axes_to_direction() == "down"
        
        mock_joystick.get_axis.side_effect = [0.0, -0.8]  # Up
        assert pygame_input._axes_to_direction() == "up"
        
        mock_joystick.get_axis.side_effect = [0.1, 0.1]  # Inside deadzone
        assert pygame_input._axes_to_direction() is None
        
    def test_pygame_emit_event_exception_handling(self):
        """Test pygame backend HID input event emission exception handling."""
        from hid_input import PygameHidInput
        callback = Mock(side_effect=Exception("Test error"))
        pygame_input = PygameHidInput("Test", {}, {}, callback)
        
        test_event = SemanticEvent(type="test", source="hid", value=100)
        
        # Should not raise exception
        pygame_input._emit_event(test_event)


class TestHybridInputConfig:
    """Test hybrid input configuration."""
    
    def test_config_creation(self):
        """Test HybridInputConfig creation."""
        config = HybridInputConfig(
            midi_port="auto",
            midi_channel=1,
            hid_device_name="Generic USB Joystick",
            hid_button_mapping={0: "trigger_step"},
            hid_joystick_mapping={"up": "osc_a"}
        )
        
        assert config.midi_port == "auto"
        assert config.midi_channel == 1
        assert config.hid_device_name == "Generic USB Joystick"
        assert config.hid_button_mapping == {0: "trigger_step"}
        assert config.hid_joystick_mapping == {"up": "osc_a"}


class TestHybridInput:
    """Test hybrid input system."""
    
    def test_hybrid_input_initialization(self):
        """Test hybrid input initialization."""
        config = HybridInputConfig(
            midi_port="auto",
            midi_channel=1, 
            hid_device_name="Test",
            hid_button_mapping={},
            hid_joystick_mapping={}
        )
        callback = Mock()
        
        hybrid = HybridInput(config, callback)
        
        assert hybrid.config == config
        assert hybrid.router_callback == callback
        assert hybrid.midi_input is None
        assert hybrid.hid_input is None
        
    def test_set_semantic_handler(self):
        """Test setting semantic event handler."""
        config = HybridInputConfig("auto", 1, "Test", {}, {})
        hybrid = HybridInput(config, Mock())
        
        handler = Mock()
        hybrid.set_semantic_handler(handler)
        
        assert hybrid._handle_semantic_event == handler
        
    @patch('hybrid_input.MidiInput')
    @patch('hybrid_input.HidInput')
    def test_start_success(self, mock_hid_input_class, mock_midi_input_class):
        """Test successful hybrid input start."""
        config = HybridInputConfig("auto", 1, "Test", {0: "trigger_step"}, {"up": "osc_a"})
        router_callback = Mock()
        semantic_handler = Mock()
        
        # Mock MIDI input
        mock_midi_input = Mock()
        mock_midi_input_class.create.return_value = mock_midi_input
        
        # Mock HID input
        mock_hid_input = Mock()
        mock_hid_input_class.return_value = mock_hid_input
        
        hybrid = HybridInput(config, router_callback)
        hybrid.set_semantic_handler(semantic_handler)
        
        hybrid.start()
        
        # Check MIDI input setup
        mock_midi_input_class.create.assert_called_once_with("auto", hybrid._handle_midi_message)
        assert hybrid.midi_input == mock_midi_input
        
        # Check HID input setup
        mock_hid_input_class.assert_called_once_with(
            device_name="Test",
            button_mapping={0: "trigger_step"},
            joystick_mapping={"up": "osc_a"},
            callback=hybrid._handle_hid_event
        )
        mock_hid_input.start.assert_called_once()
        assert hybrid.hid_input == mock_hid_input
        
    @patch('hybrid_input.MidiInput')
    def test_start_midi_failure(self, mock_midi_input_class):
        """Test hybrid input start with MIDI failure."""
        config = HybridInputConfig("auto", 1, "Test", {}, {})
        hybrid = HybridInput(config, Mock())
        
        mock_midi_input_class.create.side_effect = Exception("MIDI error")
        
        with pytest.raises(Exception, match="MIDI error"):
            hybrid.start()
            
    @patch('hybrid_input.MidiInput')
    @patch('hybrid_input.HidInput')
    def test_start_hid_failure_continues(self, mock_hid_input_class, mock_midi_input_class):
        """Test hybrid input continues with HID failure."""
        config = HybridInputConfig("auto", 1, "Test", {}, {})
        hybrid = HybridInput(config, Mock())
        
        # MIDI succeeds
        mock_midi_input = Mock()
        mock_midi_input_class.create.return_value = mock_midi_input
        
        # HID fails
        mock_hid_input = Mock()
        mock_hid_input.start.side_effect = Exception("HID error")
        mock_hid_input_class.return_value = mock_hid_input
        
        # Should not raise exception
        hybrid.start()
        
        # MIDI should still be set up
        assert hybrid.midi_input == mock_midi_input
        assert hybrid.hid_input == mock_hid_input
        
    def test_handle_midi_message(self):
        """Test MIDI message handling."""
        config = HybridInputConfig("auto", 1, "Test", {}, {})
        router_callback = Mock()
        
        hybrid = HybridInput(config, router_callback)
        
        # Test MIDI message handling
        test_message = "test_midi_message"
        hybrid._handle_midi_message(test_message)
        
        router_callback.assert_called_once_with(test_message)
        
    def test_handle_hid_event(self):
        """Test HID semantic event handling."""
        config = HybridInputConfig("auto", 1, "Test", {}, {})
        semantic_handler = Mock()
        
        hybrid = HybridInput(config, Mock())
        hybrid.set_semantic_handler(semantic_handler)
        
        # Test HID event handling
        test_event = SemanticEvent(type="trigger_step", source="hid_button", value=100)
        hybrid._handle_hid_event(test_event)
        
        semantic_handler.assert_called_once_with(test_event)
        
    def test_stop(self):
        """Test hybrid input stop."""
        config = HybridInputConfig("auto", 1, "Test", {}, {})
        hybrid = HybridInput(config, Mock())
        
        # Mock inputs
        mock_midi = Mock()
        mock_hid = Mock()
        hybrid.midi_input = mock_midi
        hybrid.hid_input = mock_hid
        
        hybrid.stop()
        
        mock_hid.stop.assert_called_once()
        mock_midi.close.assert_called_once()
        
    @patch('config.load_config')
    def test_create_from_config_with_defaults(self, mock_load_config):
        """Test creating hybrid input from config with defaults."""
        # Mock config without HID section
        mock_config = Mock()
        mock_config.midi.input_port = "auto"
        mock_config.midi.input_channel = 1
        # No hid attribute - should use defaults
        del mock_config.hid
        
        router_callback = Mock()
        semantic_handler = Mock()
        
        hybrid = HybridInput.create_from_config(mock_config, router_callback, semantic_handler)
        
        assert hybrid.config.midi_port == "auto"
        assert hybrid.config.midi_channel == 1
        assert hybrid.config.hid_device_name == "Generic USB Joystick"
        assert len(hybrid.config.hid_button_mapping) == 10  # 10 buttons
        assert "up" in hybrid.config.hid_joystick_mapping
        
    def test_create_from_config_with_hid_section(self):
        """Test creating hybrid input from config with HID section."""
        # Mock config with HID section
        mock_config = Mock()
        mock_config.midi.input_port = "test_port"
        mock_config.midi.input_channel = 2
        mock_config.hid.device_name = "Custom Joystick"
        mock_config.hid.button_mapping = {0: "test_action"}
        mock_config.hid.joystick_mapping = {"up": "test_osc"}
        
        router_callback = Mock()
        semantic_handler = Mock()
        
        hybrid = HybridInput.create_from_config(mock_config, router_callback, semantic_handler)
        
        assert hybrid.config.midi_port == "test_port"
        assert hybrid.config.midi_channel == 2
        assert hybrid.config.hid_device_name == "Custom Joystick"
        assert hybrid.config.hid_button_mapping == {0: "test_action"}
        assert hybrid.config.hid_joystick_mapping == {"up": "test_osc"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
