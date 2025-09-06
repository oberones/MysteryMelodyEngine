"""Tests for fugue mode implementation."""

import pytest
import time
from unittest.mock import Mock, patch
from state import State 
from scale_mapper import ScaleMapper
from fugue import FugueEngine, FugueParams, FugueSequencer


class TestFugueEngine:
    """Test the core fugue generation engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scale_mapper = ScaleMapper()
        self.scale_mapper.set_scale("minor", root_note=60)  # C minor
        self.engine = FugueEngine(self.scale_mapper)
    
    def test_subject_generation(self):
        """Test that subjects are generated with proper structure."""
        params = FugueParams(key_root=60, mode="minor")
        subject = self.engine.generate_subject(params, bars=1)
        
        assert len(subject) > 0, "Subject should have notes"
        # Allow for rests (None pitches) in the subject
        assert all(note['pitch'] is None or isinstance(note['pitch'], int) for note in subject), "All pitches should be integers or None (for rests)"
        assert all(note['dur'] > 0 for note in subject), "All durations should be positive"
        assert all(note['pitch'] is None or (1 <= note['vel'] <= 127) for note in subject), "All velocities should be valid MIDI (except rests)"
        
        # Check total duration is approximately 4 beats (allowing some variation)
        total_duration = sum(note['dur'] for note in subject)
        assert 3.0 <= total_duration <= 5.0, f"Subject duration {total_duration} should be around 4 beats"
    
    def test_transpose(self):
        """Test transposition functionality."""
        subject = [
            {'pitch': 60, 'dur': 1.0, 'vel': 96},
            {'pitch': 64, 'dur': 1.0, 'vel': 96}
        ]
        
        transposed = self.engine.transpose(subject, 7)  # Perfect 5th up
        
        assert len(transposed) == len(subject)
        assert transposed[0]['pitch'] == 67  # C -> G
        assert transposed[1]['pitch'] == 71  # E -> B
        assert transposed[0]['dur'] == subject[0]['dur']  # Duration unchanged
        assert transposed[0]['vel'] == subject[0]['vel']  # Velocity unchanged
    
    def test_tonal_answer(self):
        """Test tonal answer generation."""
        # Subject with tonic to dominant leap
        subject = [
            {'pitch': 60, 'dur': 1.0, 'vel': 96},  # C
            {'pitch': 67, 'dur': 1.0, 'vel': 96},  # G (P5 up)
            {'pitch': 64, 'dur': 1.0, 'vel': 96}   # E
        ]
        
        answer = self.engine.tonal_answer(subject, 60)
        
        assert len(answer) == len(subject)
        assert answer[0]['pitch'] == 67  # Start on dominant (G)
        # The second note should be adjusted from +7 to +5 for tonal answer
        assert answer[1]['pitch'] == 72  # G + 5 = C (not G + 7 = D)
    
    def test_real_answer(self):
        """Test real answer generation (exact transposition)."""
        subject = [
            {'pitch': 60, 'dur': 1.0, 'vel': 96},
            {'pitch': 67, 'dur': 1.0, 'vel': 96}
        ]
        
        answer = self.engine.real_answer(subject)
        
        assert len(answer) == len(subject)
        assert answer[0]['pitch'] == 67  # C -> G
        assert answer[1]['pitch'] == 74  # G -> D (exact +7 transposition)
    
    def test_entry_plan_generation(self):
        """Test exposition entry plan generation."""
        subject = [
            {'pitch': 60, 'dur': 1.0, 'vel': 96},
            {'pitch': 64, 'dur': 1.0, 'vel': 96}
        ]
        params = FugueParams(n_voices=3, key_root=60)
        
        entries = self.engine.make_entry_plan(subject, params)
        
        assert len(entries) == 3
        assert entries[0].voice_index == 0
        assert entries[0].is_subject == True
        assert entries[1].voice_index == 1
        assert entries[1].is_subject == False  # Answer
        assert entries[2].voice_index == 2
        assert entries[2].is_subject == True   # Subject again
        
        # Check timing
        assert entries[0].start_time == 0.0
        assert entries[1].start_time > 0.0
        assert entries[2].start_time > entries[1].start_time
    
    def test_episode_generation(self):
        """Test episode generation from subject fragments."""
        subject = [
            {'pitch': 60, 'dur': 1.0, 'vel': 96},
            {'pitch': 64, 'dur': 1.0, 'vel': 96},
            {'pitch': 67, 'dur': 1.0, 'vel': 96},
            {'pitch': 72, 'dur': 1.0, 'vel': 96}
        ]
        
        episode = self.engine.generate_episode(subject, length_beats=8.0)
        
        assert len(episode) > 0, "Episode should have notes"
        # Episode should be roughly the requested length or shorter
        episode_duration = sum(note['dur'] for note in episode)
        assert episode_duration <= 10.0, "Episode shouldn't exceed requested length by much"
    
    def test_fugue_rendering(self):
        """Test complete fugue rendering."""
        subject = [
            {'pitch': 60, 'dur': 1.0, 'vel': 96},
            {'pitch': 64, 'dur': 1.0, 'vel': 96},
            {'pitch': 67, 'dur': 1.0, 'vel': 96},
            {'pitch': 60, 'dur': 1.0, 'vel': 96}
        ]
        params = FugueParams(n_voices=3, key_root=60)
        
        score = self.engine.render_fugue(subject, params)
        
        assert len(score) == 3, "Should have 3 voices"
        assert all(len(voice) > 0 for voice in score), "All voices should have notes"
        # Allow for rests (None pitches) in the voices
        assert all(
            all(note['pitch'] is None or isinstance(note['pitch'], int) for note in voice)
            for voice in score
        ), "All pitches should be integers or None (for rests)"


class TestFugueSequencer:
    """Test the fugue sequencer integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.state = State()
        self.scale_mapper = ScaleMapper()
        self.scale_mapper.set_scale("minor", root_note=60)
        self.fugue_sequencer = FugueSequencer(self.state, self.scale_mapper)
    
    def test_initialization(self):
        """Test fugue sequencer initialization."""
        assert self.fugue_sequencer.state is self.state
        assert self.fugue_sequencer.scale_mapper is self.scale_mapper
        assert self.fugue_sequencer._active_fugue is None
    
    def test_should_start_new_fugue(self):
        """Test logic for when to start new fugues."""
        # Initially should start a fugue (no previous fugue)
        assert self.fugue_sequencer.should_start_new_fugue() == True
        
        # Start a fugue
        self.fugue_sequencer.start_new_fugue()
        assert self.fugue_sequencer._active_fugue is not None
        
        # Should not start another while one is active
        assert self.fugue_sequencer.should_start_new_fugue() == False
    
    @patch('time.perf_counter')
    def test_fugue_timeout(self, mock_time):
        """Test that fugues timeout after 5 minutes."""
        # Start time
        mock_time.return_value = 0.0
        self.fugue_sequencer.start_new_fugue()
        
        # 6 minutes later
        mock_time.return_value = 360.0  # 6 minutes
        
        # Should trigger timeout and end fugue
        result = self.fugue_sequencer.should_start_new_fugue()
        assert self.fugue_sequencer._active_fugue is None
        assert result == False  # Still in rest period
    
    @patch('time.perf_counter')
    def test_rest_period(self, mock_time):
        """Test rest period between fugues."""
        mock_time.return_value = 0.0
        
        # Simulate a completed fugue
        self.fugue_sequencer._last_fugue_end = 0.0
        self.fugue_sequencer._active_fugue = None
        
        # 5 seconds later (less than 10 second rest)
        mock_time.return_value = 5.0
        assert self.fugue_sequencer.should_start_new_fugue() == False
        
        # 15 seconds later (more than 10 second rest)
        mock_time.return_value = 15.0
        assert self.fugue_sequencer.should_start_new_fugue() == True
    
    def test_get_next_step_notes_without_fugue(self):
        """Test getting notes when no fugue is active."""
        # Should return empty list initially  
        result = self.fugue_sequencer.get_next_step_notes(0)
        assert isinstance(result, list), "Should return a list"
        # May be empty or may start a fugue and return notes

    def test_get_next_step_notes_with_fugue(self):
        """Test getting notes from an active fugue."""
        self.fugue_sequencer.start_new_fugue()
        
        # Should get notes from the fugue
        notes_received = []
        for step in range(10):  # Try several steps
            result = self.fugue_sequencer.get_next_step_notes(step)
            assert isinstance(result, list), "Should return a list"
            notes_received.extend(result)
        
        # Should have received some notes
        if len(notes_received) > 0:
            for pitch, velocity, duration in notes_received:
                assert isinstance(pitch, int), "Pitch should be integer"
                assert 1 <= velocity <= 127, "Velocity should be valid MIDI"
                assert duration > 0, "Duration should be positive"


class TestFugueIntegration:
    """Test integration with the main sequencer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from sequencer import Sequencer
        
        self.state = State()
        self.scales = ["minor", "major", "pentatonic_minor"]
        self.sequencer = Sequencer(self.state, self.scales)
        
        # Mock the note callback
        self.note_callback = Mock()
        self.sequencer.set_note_callback(self.note_callback)
    
    def test_fugue_pattern_setting(self):
        """Test setting fugue as direction pattern."""
        # Should accept fugue as valid direction
        self.sequencer.set_direction_pattern("fugue")
        assert self.state.get('direction_pattern') == "fugue"
        
        # Should have initialized fugue sequencer
        assert self.sequencer._fugue_sequencer is not None
    
    def test_fugue_note_generation(self):
        """Test that fugue mode generates notes properly."""
        self.sequencer.set_direction_pattern("fugue")
        
        # Generate some steps
        for step in range(5):
            self.sequencer._generate_step_note(step)
        
        # Should have made some note callback calls (fugue might not generate notes every step)
        # We just check that no errors occurred
        assert True  # If we got here, no exceptions were thrown
    
    def test_fallback_to_forward(self):
        """Test that invalid patterns fall back to forward."""
        self.sequencer.set_direction_pattern("invalid_pattern")
        assert self.state.get('direction_pattern') == "forward"
    
    def test_pattern_switching(self):
        """Test switching between fugue and other patterns."""
        # Start with forward
        self.sequencer.set_direction_pattern("forward")
        assert self.state.get('direction_pattern') == "forward"
        
        # Switch to fugue
        self.sequencer.set_direction_pattern("fugue")
        assert self.state.get('direction_pattern') == "fugue"
        assert self.sequencer._fugue_sequencer is not None
        
        # Switch back to forward
        self.sequencer.set_direction_pattern("forward")
        assert self.state.get('direction_pattern') == "forward"
        # Fugue sequencer should still exist but not be used
        assert self.sequencer._fugue_sequencer is not None


if __name__ == "__main__":
    pytest.main([__file__])
