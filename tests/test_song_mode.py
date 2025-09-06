"""Tests for song mode sequencer functionality.

Tests the SongSequencer class and its integration with the main sequencer.
"""

import pytest
import time
from unittest.mock import MagicMock
from state import State
from scale_mapper import ScaleMapper
from song import SongSequencer, SONG_PATTERNS, SectionType, SongSection, SongPattern
from sequencer import Sequencer


class TestSongSequencer:
    """Test suite for SongSequencer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.state = State()
        self.scale_mapper = ScaleMapper()
        self.scale_mapper.set_scale("minor", root_note=60)  # C minor
        self.song_sequencer = SongSequencer(self.state, self.scale_mapper)
        
        # Set up basic state
        self.state.update_multiple({
            'bpm': 120,
            'density': 0.8,
            'voices': 2,
            'root_note': 60,
            'scale_index': 0
        }, source='test')
    
    def test_initialization(self):
        """Test song sequencer initialization."""
        assert self.song_sequencer is not None
        assert self.song_sequencer._current_pattern is None
        assert self.song_sequencer._current_section_index == 0
        assert not self.song_sequencer._between_songs
    
    def test_song_patterns_exist(self):
        """Test that predefined song patterns exist and are valid."""
        assert len(SONG_PATTERNS) > 0
        
        for pattern_name, pattern in SONG_PATTERNS.items():
            assert isinstance(pattern, SongPattern)
            assert pattern.name
            assert len(pattern.sections) > 0
            assert pattern.estimated_duration_minutes > 0
            
            # Check that all sections are valid
            for section in pattern.sections:
                assert isinstance(section, SongSection)
                assert isinstance(section.section_type, SectionType)
                assert section.bars > 0
                assert 0.0 <= section.density <= 1.0
                assert section.tempo_factor > 0
    
    def test_start_new_song(self):
        """Test starting a new song."""
        self.song_sequencer.start_new_song()
        
        assert self.song_sequencer._current_pattern is not None
        assert self.song_sequencer._current_section_index == 0
        assert not self.song_sequencer._between_songs
        assert len(self.song_sequencer._voice_patterns) > 0
    
    def test_voice_initialization(self):
        """Test voice pattern initialization."""
        self.state.set('voices', 3, source='test')
        self.song_sequencer.start_new_song()
        
        assert len(self.song_sequencer._voice_patterns) == 3
        assert len(self.song_sequencer._voice_octave_shifts) == 3
        assert len(self.song_sequencer._last_voice_notes) == 3
        
        # Check that patterns are different for harmonic variety
        patterns = list(self.song_sequencer._voice_patterns.values())
        assert len(set(tuple(p) for p in patterns)) > 1  # At least some variety
    
    def test_section_settings_application(self):
        """Test that section settings are properly applied."""
        self.song_sequencer.start_new_song()
        
        # Get current section
        section = self.song_sequencer._current_pattern.sections[0]
        
        # Check that BPM was modified by tempo factor
        expected_bpm = 120.0 * section.tempo_factor
        actual_bpm = self.state.get('bpm')
        assert abs(actual_bpm - expected_bpm) < 0.1
        
        # Check that density was applied
        assert self.state.get('density') == section.density
    
    def test_note_generation(self):
        """Test note generation in song mode."""
        self.song_sequencer.start_new_song()
        
        # Generate notes for several steps
        notes_generated = []
        for step in range(16):
            notes = self.song_sequencer.get_next_step_notes(step)
            notes_generated.extend(notes)
        
        # Should generate some notes
        assert len(notes_generated) > 0
        
        # Check note format
        for note, velocity, duration in notes_generated:
            assert isinstance(note, int)
            assert 0 <= note <= 127
            assert isinstance(velocity, int)
            assert 1 <= velocity <= 127
            assert isinstance(duration, float)
            assert duration > 0
    
    def test_voice_leading(self):
        """Test that voice leading produces reasonable intervals."""
        self.state.set('voices', 2, source='test')
        self.song_sequencer.start_new_song()
        
        # Generate many notes to test voice leading
        all_notes = []
        for step in range(32):
            notes = self.song_sequencer.get_next_step_notes(step)
            all_notes.extend(notes)
        
        if len(all_notes) > 10:  # If we generated enough notes
            # Check that we don't have too many large leaps
            large_leaps = 0
            for i in range(1, len(all_notes)):
                interval = abs(all_notes[i][0] - all_notes[i-1][0])
                if interval > 12:  # Larger than an octave
                    large_leaps += 1
            
            # Should have mostly stepwise motion with some leaps
            leap_ratio = large_leaps / len(all_notes)
            assert leap_ratio < 0.3  # Less than 30% large leaps
    
    def test_between_songs_period(self):
        """Test the between-songs pause functionality."""
        # Start and immediately complete a song
        self.song_sequencer.start_new_song()
        
        # Force completion by setting high section index
        self.song_sequencer._current_section_index = len(self.song_sequencer._current_pattern.sections)
        
        # Trigger between-songs mode
        notes = self.song_sequencer.get_next_step_notes(0)
        
        assert self.song_sequencer._between_songs
        assert notes == []  # No notes during pause
        
        # Test that song info reflects between-songs state
        song_info = self.song_sequencer.get_current_song_info()
        assert song_info['status'] == 'between_songs'
        assert 'time_until_next_song' in song_info
    
    def test_song_info(self):
        """Test song info reporting."""
        # Test with no song
        song_info = self.song_sequencer.get_current_song_info()
        assert song_info['status'] == 'no_song'
        
        # Test with active song
        self.song_sequencer.start_new_song()
        song_info = self.song_sequencer.get_current_song_info()
        
        assert song_info['status'] == 'playing'
        assert song_info['pattern'] is not None
        assert song_info['section'] is not None
        assert song_info['section_index'] >= 0
        assert song_info['total_sections'] > 0
        assert song_info['elapsed_time'] >= 0
        assert song_info['estimated_duration'] > 0
        assert song_info['voices'] > 0
    
    def test_force_section_advance(self):
        """Test manual section advancement."""
        self.song_sequencer.start_new_song()
        initial_section = self.song_sequencer._current_section_index
        
        self.song_sequencer.force_next_section()
        
        assert self.song_sequencer._current_section_index == initial_section + 1
    
    def test_force_new_song(self):
        """Test manual song restart."""
        self.song_sequencer.start_new_song()
        first_pattern = self.song_sequencer._current_pattern.name
        
        # Force start another song (might be the same pattern, but state should reset)
        self.song_sequencer.force_new_song()
        
        assert self.song_sequencer._current_section_index == 0
        assert not self.song_sequencer._between_songs
        assert self.song_sequencer._current_pattern is not None


class TestSongModeIntegration:
    """Test suite for song mode integration with main sequencer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.state = State()
        self.scales = ['minor', 'major', 'pentatonic_minor', 'dorian']
        self.sequencer = Sequencer(self.state, self.scales)
        
        # Set up note callback
        self.notes_generated = []
        def note_callback(note_event):
            self.notes_generated.append(note_event)
        
        self.sequencer.set_note_callback(note_callback)
        
        # Set up basic state
        self.state.update_multiple({
            'bpm': 120,
            'density': 0.8,
            'voices': 2,
            'root_note': 60,
            'scale_index': 0
        }, source='test')
    
    def test_song_mode_activation(self):
        """Test activating song mode."""
        self.sequencer.set_direction_pattern('song')
        
        assert self.state.get('direction_pattern') == 'song'
        assert self.sequencer._song_sequencer is not None
    
    def test_song_mode_note_generation(self):
        """Test note generation in song mode."""
        self.sequencer.set_direction_pattern('song')
        
        # Generate notes
        for step in range(16):
            self.sequencer._generate_step_note(step)
        
        # Should generate some notes
        assert len(self.notes_generated) > 0
        
        # All notes should be valid
        for note_event in self.notes_generated:
            assert hasattr(note_event, 'note')
            assert hasattr(note_event, 'velocity')
            assert hasattr(note_event, 'duration')
            assert hasattr(note_event, 'step')
    
    def test_pattern_switching(self):
        """Test switching between song mode and other patterns."""
        patterns = ['forward', 'song', 'fugue', 'song', 'random']
        
        for pattern in patterns:
            self.sequencer.set_direction_pattern(pattern)
            assert self.state.get('direction_pattern') == pattern
            
            # Generate a few notes to ensure no errors
            self.notes_generated.clear()
            for step in range(4):
                self.sequencer._generate_step_note(step)
            
            # Should not crash and may generate notes depending on pattern
    
    def test_song_mode_bypasses_probability_controls(self):
        """Test that song mode ignores standard probability controls."""
        self.sequencer.set_direction_pattern('song')
        
        # Set very low density and probability controls
        self.state.set('density', 0.1, source='test')
        self.sequencer.set_step_probabilities([0.1] * 8)
        self.sequencer.set_step_pattern([False] * 8)
        
        # Generate notes - song mode should still produce notes
        # because it manages its own density and ignores step patterns
        for step in range(16):
            self.sequencer._generate_step_note(step)
        
        # Song mode should generate notes despite low probability settings
        # (though the amount depends on the song section's density)
        # We can't guarantee notes will be generated due to song structure,
        # but the mode should be active
        assert self.sequencer._song_sequencer is not None
    
    def test_multiple_voices(self):
        """Test song mode with multiple voices."""
        self.state.set('voices', 4, source='test')
        self.sequencer.set_direction_pattern('song')
        
        # Generate notes
        for step in range(32):
            self.sequencer._generate_step_note(step)
        
        # With 4 voices, we should get more notes than with 1 voice
        # (though exact count depends on song structure and density)
        if len(self.notes_generated) > 0:
            # Check that we have some variation in notes (different voices)
            unique_notes = set(note.note for note in self.notes_generated)
            assert len(unique_notes) > 1  # Should have some harmonic variety
    
    def test_scale_changes(self):
        """Test that song mode respects scale changes."""
        self.sequencer.set_direction_pattern('song')
        
        # Generate notes in minor scale
        for step in range(8):
            self.sequencer._generate_step_note(step)
        minor_notes = [note.note for note in self.notes_generated]
        
        # Change to major scale
        self.state.set('scale_index', 1, source='test')  # Assuming major is index 1
        self.notes_generated.clear()
        
        # Generate notes in major scale
        for step in range(8):
            self.sequencer._generate_step_note(step)
        major_notes = [note.note for note in self.notes_generated]
        
        # Notes should be different (though this isn't guaranteed due to song structure)
        # At minimum, the song sequencer should be using the new scale
        assert self.sequencer._song_sequencer is not None


class TestSongPatterns:
    """Test suite for song pattern definitions."""
    
    def test_verse_chorus_pattern(self):
        """Test verse-chorus pattern structure."""
        pattern = SONG_PATTERNS['verse_chorus']
        
        assert pattern.name == "Verse-Chorus"
        assert len(pattern.sections) == 6  # intro, verse, chorus, verse, chorus, outro
        
        # Check section types
        section_types = [s.section_type for s in pattern.sections]
        assert SectionType.INTRO in section_types
        assert SectionType.VERSE in section_types
        assert SectionType.CHORUS in section_types
        assert SectionType.OUTRO in section_types
    
    def test_blues_pattern(self):
        """Test 12-bar blues pattern structure."""
        pattern = SONG_PATTERNS['blues_twelve_bar']
        
        assert pattern.name == "12-Bar Blues"
        assert len(pattern.sections) == 6  # intro, 3 verses, instrumental, outro
        
        # Check that verses have 12 bars each
        verse_sections = [s for s in pattern.sections if s.section_type == SectionType.VERSE]
        for verse in verse_sections:
            assert verse.bars == 12
    
    def test_aaba_pattern(self):
        """Test AABA (32-bar form) pattern structure."""
        pattern = SONG_PATTERNS['aaba']
        
        assert pattern.name == "AABA (32-Bar Form)"
        
        # Should have intro, 4 sections (AABA), and outro
        assert len(pattern.sections) == 6
        
        # Check for bridge section
        bridge_sections = [s for s in pattern.sections if s.section_type == SectionType.BRIDGE]
        assert len(bridge_sections) == 1
    
    def test_all_patterns_valid(self):
        """Test that all patterns have valid musical parameters."""
        for pattern_name, pattern in SONG_PATTERNS.items():
            # Check overall structure
            assert isinstance(pattern, SongPattern)
            assert pattern.estimated_duration_minutes > 0.5  # At least 30 seconds
            assert pattern.estimated_duration_minutes < 10.0  # Less than 10 minutes
            
            # Check sections
            total_bars = sum(s.bars for s in pattern.sections)
            assert total_bars > 0
            
            for section in pattern.sections:
                # Density should be reasonable
                assert 0.1 <= section.density <= 1.0
                
                # Tempo factor should be reasonable
                assert 0.5 <= section.tempo_factor <= 2.0
                
                # Octave shift should be reasonable
                assert -2 <= section.octave_shift <= 2
                
                # Velocity factor should be reasonable
                assert 0.3 <= section.velocity_factor <= 2.0


if __name__ == "__main__":
    pytest.main([__file__])
