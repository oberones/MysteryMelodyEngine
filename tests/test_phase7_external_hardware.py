"""Tests for Phase 7 external hardware integration features.

Tests CC profiles, MIDI clock, and latency optimization functionality.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock
from cc_profiles import CCParameter, CCProfile, CurveType, CCProfileRegistry
from midi_clock import MidiClock, ClockStatus
from latency_optimizer import LatencyOptimizer, CCThrottler
from external_hardware import ExternalHardwareManager


class TestCCProfiles:
    """Test CC profile system."""
    
    def test_cc_parameter_linear_scaling(self):
        """Test linear parameter scaling."""
        param = CCParameter(cc=74, range=(0, 127), curve=CurveType.LINEAR)
        
        assert param.scale_value(0.0) == 0
        assert param.scale_value(0.5) == 63
        assert param.scale_value(1.0) == 127
    
    def test_cc_parameter_exponential_scaling(self):
        """Test exponential parameter scaling."""
        param = CCParameter(cc=74, range=(0, 127), curve=CurveType.EXPONENTIAL)
        
        assert param.scale_value(0.0) == 0
        assert param.scale_value(0.5) == 31  # 0.5^2 * 127 ≈ 31
        assert param.scale_value(1.0) == 127
    
    def test_cc_parameter_stepped_scaling(self):
        """Test stepped parameter scaling."""
        param = CCParameter(cc=70, range=(0, 127), curve=CurveType.STEPPED, steps=4)
        
        assert param.scale_value(0.0) == 0
        assert param.scale_value(0.33) == 0    # Step 0 of 4 (0.33 * 3 = 0.99 -> int(0) -> 0/3 = 0)
        assert param.scale_value(0.50) == 42   # Step 1 of 4 (0.5 * 3 = 1.5 -> int(1) -> 1/3 = 0.33 * 127 = 42)
        assert param.scale_value(0.75) == 84   # Step 2 of 4 (0.75 * 3 = 2.25 -> int(2) -> 2/3 = 0.67 * 127 = 85)
        assert param.scale_value(1.0) == 127   # Step 3 of 4
    
    def test_cc_parameter_range_clamping(self):
        """Test parameter value clamping."""
        param = CCParameter(cc=74, range=(20, 100), curve=CurveType.LINEAR)
        
        assert param.scale_value(0.0) == 20
        assert param.scale_value(0.5) == 60
        assert param.scale_value(1.0) == 100
    
    def test_cc_profile_parameter_mapping(self):
        """Test CC profile parameter mapping."""
        profile = CCProfile(
            name="Test Profile",
            parameters={
                "filter_cutoff": CCParameter(cc=74, range=(0, 127)),
                "filter_resonance": CCParameter(cc=71, range=(0, 127))
            }
        )
        
        result = profile.map_parameter("filter_cutoff", 0.5)
        assert result == (74, 63)
        
        result = profile.map_parameter("nonexistent", 0.5)
        assert result is None
    
    def test_cc_profile_registry(self):
        """Test CC profile registry functionality."""
        registry = CCProfileRegistry()
        
        # Test built-in profiles are loaded
        profiles = registry.list_profiles()
        assert "korg_nts1_mk2" in profiles
        assert "generic_analog" in profiles
        assert "fm_synth" in profiles
        
        # Test getting a profile
        nts1_profile = registry.get_profile("korg_nts1_mk2")
        assert nts1_profile is not None
        assert nts1_profile.name == "Korg NTS-1 MK2"
        assert "filter_cutoff" in nts1_profile.parameters


class TestMidiClock:
    """Test MIDI clock functionality."""
    
    def test_clock_initialization(self):
        """Test MIDI clock initialization."""
        mock_sender = Mock()
        clock = MidiClock(mock_sender)
        
        assert clock.status.bpm == 120.0
        assert not clock.status.running
        assert clock.status.position == 0
    
    def test_bpm_setting(self):
        """Test BPM setting and timing calculation."""
        mock_sender = Mock()
        clock = MidiClock(mock_sender)
        
        clock.set_bpm(140.0)
        assert clock.status.bpm == 140.0
        
        # At 140 BPM, 24 PPQN: interval = 60 / (140 * 24) ≈ 0.0178 seconds
        expected_interval = 60.0 / (140.0 * 24)
        assert abs(clock._clock_interval - expected_interval) < 0.0001
    
    def test_clock_start_stop(self):
        """Test clock start/stop functionality."""
        mock_sender = Mock()
        clock = MidiClock(mock_sender)
        
        # Test start
        clock.start()
        assert clock.status.running
        mock_sender.send_start.assert_called_once()
        
        # Test stop
        clock.stop()
        assert not clock.status.running
        mock_sender.send_stop.assert_called_once()
    
    def test_song_position_setting(self):
        """Test song position setting."""
        mock_sender = Mock()
        clock = MidiClock(mock_sender)
        
        clock.set_song_position(16)  # 16th notes
        assert clock.status.song_position == 16
        assert clock.status.position == 96  # 16 * 6 (24 PPQN / 4)
        mock_sender.send_song_position.assert_called_with(16)


class TestCCThrottler:
    """Test CC message throttling."""
    
    def test_throttling_behavior(self):
        """Test CC message throttling."""
        throttler = CCThrottler(throttle_ms=50)  # 50ms throttle
        
        # First message should pass
        assert throttler.should_send_cc(1, 74, 64) == True
        
        # Second message immediately should be throttled
        assert throttler.should_send_cc(1, 74, 65) == False
        
        # Different CC should not be throttled
        assert throttler.should_send_cc(1, 75, 64) == True
        
        # Different channel should not be throttled
        assert throttler.should_send_cc(2, 74, 64) == True
    
    def test_pending_messages(self):
        """Test pending message handling."""
        throttler = CCThrottler(throttle_ms=10)
        
        # Send initial message
        throttler.should_send_cc(1, 74, 64)
        
        # Throttle next message
        throttler.should_send_cc(1, 74, 65)
        
        # Wait for throttle period to pass
        time.sleep(0.02)  # 20ms
        
        # Get pending messages
        pending = throttler.get_pending_messages()
        assert len(pending) == 1
        assert pending[0] == (1, 74, 65)


class TestLatencyOptimizer:
    """Test latency optimization functionality."""
    
    def test_initialization(self):
        """Test latency optimizer initialization."""
        mock_output = Mock()
        optimizer = LatencyOptimizer(mock_output, throttle_ms=15)
        
        assert optimizer.cc_throttler.throttle_ms == 15
        assert optimizer.message_queue is not None
        assert optimizer.stats.total_messages == 0
    
    def test_immediate_message_sending(self):
        """Test immediate message sending."""
        mock_output = Mock()
        mock_output.send_note_on.return_value = True
        mock_output.send_control_change.return_value = True
        
        optimizer = LatencyOptimizer(mock_output)
        
        # Test immediate note on
        optimizer.send_immediate('note_on', note=60, velocity=100, channel=1)
        mock_output.send_note_on.assert_called_with(60, 100, 1)
        
        # Test immediate CC
        optimizer.send_immediate('cc', cc=74, value=64, channel=1)
        mock_output.send_control_change.assert_called_with(74, 64, 1)
    
    def test_scheduled_message_queueing(self):
        """Test scheduled message queueing."""
        mock_output = Mock()
        optimizer = LatencyOptimizer(mock_output)
        
        future_time = time.perf_counter() + 1.0  # 1 second in future
        
        optimizer.schedule_note_on(60, 100, 1, future_time)
        assert optimizer.message_queue.size() == 1
        
        # Message should not be ready yet
        ready = optimizer.message_queue.get_ready_messages(time.perf_counter())
        assert len(ready) == 0


class TestExternalHardwareManager:
    """Test external hardware manager integration."""
    
    def test_initialization(self):
        """Test external hardware manager initialization."""
        mock_output = Mock()
        mock_config = Mock()
        mock_config.midi.cc_profile.active_profile = "korg_nts1_mk2"
        mock_config.midi.cc_profile.cc_throttle_ms = 10
        mock_config.midi.clock.enabled = False
        mock_config.midi.output_channel = 1
        mock_config.model_dump.return_value = {}
        
        manager = ExternalHardwareManager(mock_output, mock_config)
        
        assert manager.status.active_profile == "korg_nts1_mk2"
        assert manager.latency_optimizer is not None
    
    def test_parameter_change_sending(self):
        """Test parameter change via CC profiles."""
        mock_output = Mock()
        mock_output.is_connected = True
        
        mock_config = Mock()
        mock_config.midi.cc_profile.active_profile = "korg_nts1_mk2"
        mock_config.midi.cc_profile.cc_throttle_ms = 10
        mock_config.midi.clock.enabled = False
        mock_config.midi.output_channel = 1
        mock_config.model_dump.return_value = {}
        
        manager = ExternalHardwareManager(mock_output, mock_config)
        
        # Test sending a known parameter
        result = manager.send_parameter_change("filter_cutoff", 0.75)
        assert result == True
        
        # Test sending unknown parameter
        result = manager.send_parameter_change("nonexistent_param", 0.5)
        assert result == False
    
    def test_profile_switching(self):
        """Test switching between CC profiles."""
        mock_output = Mock()
        mock_config = Mock()
        mock_config.midi.cc_profile.active_profile = "korg_nts1_mk2"
        mock_config.midi.cc_profile.cc_throttle_ms = 10
        mock_config.midi.clock.enabled = False
        mock_config.midi.output_channel = 1
        mock_config.model_dump.return_value = {}
        
        manager = ExternalHardwareManager(mock_output, mock_config)
        
        # Switch to generic analog profile
        result = manager.set_active_profile("generic_analog")
        assert result == True
        assert manager.status.active_profile == "generic_analog"
        
        # Try to switch to non-existent profile
        result = manager.set_active_profile("nonexistent")
        assert result == False
        assert manager.status.active_profile == "generic_analog"  # Should remain unchanged
    
    def test_available_profiles(self):
        """Test getting available profiles."""
        mock_output = Mock()
        mock_config = Mock()
        mock_config.midi.cc_profile.active_profile = "korg_nts1_mk2"
        mock_config.midi.cc_profile.cc_throttle_ms = 10
        mock_config.midi.clock.enabled = False
        mock_config.midi.output_channel = 1
        mock_config.model_dump.return_value = {}
        
        manager = ExternalHardwareManager(mock_output, mock_config)
        
        profiles = manager.get_available_profiles()
        assert "korg_nts1_mk2" in profiles
        assert "generic_analog" in profiles
        assert "fm_synth" in profiles
    
    def test_performance_metrics(self):
        """Test performance metrics collection."""
        mock_output = Mock()
        mock_config = Mock()
        mock_config.midi.cc_profile.active_profile = "korg_nts1_mk2"
        mock_config.midi.cc_profile.cc_throttle_ms = 10
        mock_config.midi.clock.enabled = False
        mock_config.midi.output_channel = 1
        mock_config.model_dump.return_value = {}
        
        manager = ExternalHardwareManager(mock_output, mock_config)
        
        metrics = manager.get_performance_metrics()
        
        assert "cc_profile" in metrics
        assert "midi_clock" in metrics
        assert "latency" in metrics
        
        assert metrics["cc_profile"]["active_profile"] == "korg_nts1_mk2"
        assert metrics["midi_clock"]["enabled"] == False


if __name__ == "__main__":
    pytest.main([__file__])
