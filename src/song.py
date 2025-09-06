"""Song mode sequencer for structured compositions.

Generates complete songs using common song structures (intro-verse-chorus patterns)
with the configured number of voices, BPM, scale, and other sequencer settings.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import time
import random
import logging
from state import State
from scale_mapper import ScaleMapper
from note_utils import format_note_with_number, format_rest

log = logging.getLogger(__name__)


class SectionType(Enum):
    """Types of song sections."""
    INTRO = "intro"
    VERSE = "verse"
    CHORUS = "chorus"
    BRIDGE = "bridge"
    OUTRO = "outro"
    INSTRUMENTAL = "instrumental"


@dataclass
class SongSection:
    """Represents a section of a song."""
    section_type: SectionType
    bars: int  # Length in bars
    density: float  # Note density for this section (0.0-1.0)
    tempo_factor: float = 1.0  # Tempo multiplier relative to base BPM
    octave_shift: int = 0  # Octave shift for this section
    velocity_factor: float = 1.0  # Velocity multiplier
    step_pattern: Optional[str] = None  # Override step pattern for this section


@dataclass
class SongPattern:
    """Defines a complete song structure."""
    name: str
    sections: List[SongSection]
    estimated_duration_minutes: float


# Common song patterns used in popular music
SONG_PATTERNS = {
    "verse_chorus": SongPattern(
        name="Verse-Chorus",
        sections=[
            SongSection(SectionType.INTRO, bars=8, density=0.6, velocity_factor=0.8),
            SongSection(SectionType.VERSE, bars=16, density=0.7),
            SongSection(SectionType.CHORUS, bars=16, density=0.9, velocity_factor=1.2),
            SongSection(SectionType.VERSE, bars=16, density=0.7),
            SongSection(SectionType.CHORUS, bars=16, density=0.9, velocity_factor=1.2),
            SongSection(SectionType.OUTRO, bars=8, density=0.5, velocity_factor=0.7),
        ],
        estimated_duration_minutes=2.5
    ),
    
    "aaba": SongPattern(
        name="AABA (32-Bar Form)",
        sections=[
            SongSection(SectionType.INTRO, bars=4, density=0.5, velocity_factor=0.8),
            SongSection(SectionType.VERSE, bars=8, density=0.8, step_pattern="syncopated"),  # A
            SongSection(SectionType.VERSE, bars=8, density=0.8, octave_shift=0),  # A
            SongSection(SectionType.BRIDGE, bars=8, density=0.9, octave_shift=1, velocity_factor=1.3),  # B
            SongSection(SectionType.VERSE, bars=8, density=0.8, octave_shift=0),  # A
            SongSection(SectionType.OUTRO, bars=4, density=0.4, velocity_factor=0.6),
        ],
        estimated_duration_minutes=1.8
    ),
    
    "verse_chorus_bridge": SongPattern(
        name="Verse-Chorus-Bridge",
        sections=[
            SongSection(SectionType.INTRO, bars=8, density=0.5, velocity_factor=0.7),
            SongSection(SectionType.VERSE, bars=16, density=0.7),
            SongSection(SectionType.CHORUS, bars=16, density=0.9, velocity_factor=1.2),
            SongSection(SectionType.VERSE, bars=16, density=0.7, octave_shift=0),
            SongSection(SectionType.CHORUS, bars=16, density=0.9, velocity_factor=1.2),
            SongSection(SectionType.BRIDGE, bars=12, density=0.8, octave_shift=1, tempo_factor=0.9),
            SongSection(SectionType.CHORUS, bars=16, density=1.0, velocity_factor=1.3),
            SongSection(SectionType.OUTRO, bars=8, density=0.4, velocity_factor=0.6),
        ],
        estimated_duration_minutes=3.2
    ),
    
    "blues_twelve_bar": SongPattern(
        name="12-Bar Blues",
        sections=[
            SongSection(SectionType.INTRO, bars=4, density=0.6, velocity_factor=0.8),
            SongSection(SectionType.VERSE, bars=12, density=0.8, step_pattern="syncopated"),  # First 12-bar
            SongSection(SectionType.VERSE, bars=12, density=0.8, velocity_factor=1.1),  # Second 12-bar
            SongSection(SectionType.INSTRUMENTAL, bars=12, density=0.9, velocity_factor=1.2),  # Solo
            SongSection(SectionType.VERSE, bars=12, density=0.8, velocity_factor=1.0),  # Final 12-bar
            SongSection(SectionType.OUTRO, bars=4, density=0.5, velocity_factor=0.7),
        ],
        estimated_duration_minutes=2.1
    ),
    
    "pop_standard": SongPattern(
        name="Pop Standard",
        sections=[
            SongSection(SectionType.INTRO, bars=8, density=0.6, velocity_factor=0.8),
            SongSection(SectionType.VERSE, bars=16, density=0.7),
            SongSection(SectionType.CHORUS, bars=16, density=0.9, velocity_factor=1.2),
            SongSection(SectionType.VERSE, bars=16, density=0.7),
            SongSection(SectionType.CHORUS, bars=16, density=0.9, velocity_factor=1.2),
            SongSection(SectionType.BRIDGE, bars=8, density=0.8, octave_shift=1),
            SongSection(SectionType.CHORUS, bars=16, density=1.0, velocity_factor=1.3),
            SongSection(SectionType.CHORUS, bars=16, density=0.9, velocity_factor=1.1),  # Repeat chorus
            SongSection(SectionType.OUTRO, bars=8, density=0.4, velocity_factor=0.6),
        ],
        estimated_duration_minutes=3.5
    ),
    
    "minimalist": SongPattern(
        name="Minimalist",
        sections=[
            SongSection(SectionType.INTRO, bars=16, density=0.3, velocity_factor=0.7, step_pattern="sparse"),
            SongSection(SectionType.VERSE, bars=32, density=0.5, step_pattern="every_other"),
            SongSection(SectionType.BRIDGE, bars=16, density=0.7, octave_shift=1),
            SongSection(SectionType.VERSE, bars=32, density=0.6, velocity_factor=1.1),
            SongSection(SectionType.OUTRO, bars=16, density=0.2, velocity_factor=0.5, step_pattern="sparse"),
        ],
        estimated_duration_minutes=4.0
    )
}


class SongSequencer:
    """Manages song-structured compositions using common song patterns."""
    
    def __init__(self, state: State, scale_mapper: ScaleMapper):
        self.state = state
        self.scale_mapper = scale_mapper
        
        # Song state
        self._current_pattern: Optional[SongPattern] = None
        self._current_section_index = 0
        self._section_start_time = 0.0
        self._section_bar_count = 0
        self._song_start_time = 0.0
        self._between_songs = False
        self._between_songs_start = 0.0
        self._base_bpm = 120.0
        self._base_density = 0.8
        self._base_velocity = 80
        self._base_velocity_range = 40
        self._base_gate_length = 0.8
        self._base_gate_length_range = 0.3
        
        # Voice management for polyphonic compositions
        self._voice_patterns: Dict[int, List[int]] = {}  # voice_id -> note pattern
        self._voice_octave_shifts: Dict[int, int] = {}  # voice_id -> octave shift
        self._last_voice_notes: Dict[int, int] = {}  # voice_id -> last note played
        
        log.info("song_sequencer_initialized")
    
    def start_new_song(self):
        """Start a new song composition with a randomly selected pattern."""
        if self._between_songs:
            # Still in between-songs period
            return
        
        # Select a random pattern
        pattern_name = random.choice(list(SONG_PATTERNS.keys()))
        self._current_pattern = SONG_PATTERNS[pattern_name]
        self._current_section_index = 0
        self._section_start_time = time.perf_counter()
        self._section_bar_count = 0
        self._song_start_time = self._section_start_time
        self._between_songs = False
        
        # Store base values from current state
        self._base_bpm = self.state.get('bpm', 120.0)
        self._base_density = self.state.get('density', 0.8)
        self._base_velocity = self.state.get('base_velocity', 80)
        self._base_velocity_range = self.state.get('velocity_range', 40)
        self._base_gate_length = self.state.get('base_gate_length', 0.8)
        self._base_gate_length_range = self.state.get('gate_length_range', 0.3)
        
        # Initialize voice patterns
        self._initialize_voice_patterns()
        
        # Apply first section settings
        self._apply_section_settings()
        
        log.info(f"song_started pattern={pattern_name} estimated_duration={self._current_pattern.estimated_duration_minutes:.1f}min sections={len(self._current_pattern.sections)}")
    
    def _initialize_voice_patterns(self):
        """Initialize voice patterns and octave shifts for polyphonic composition."""
        num_voices = self.state.get('voices', 1)
        
        self._voice_patterns.clear()
        self._voice_octave_shifts.clear()
        self._last_voice_notes.clear()
        
        # Create different patterns for each voice to create harmonic interest
        base_patterns = [
            [0, 2, 4, 2],      # Voice 1: Root triad pattern
            [2, 4, 6, 4],      # Voice 2: Third-based pattern
            [4, 6, 1, 6],      # Voice 3: Fifth-based pattern
            [6, 1, 3, 1],      # Voice 4: Seventh-based pattern
        ]
        
        # Assign octave shifts for voice separation
        voice_octave_shifts = [0, 0, 1, -1]  # Spread voices across octaves
        
        for voice_id in range(num_voices):
            self._voice_patterns[voice_id] = base_patterns[voice_id % len(base_patterns)]
            self._voice_octave_shifts[voice_id] = voice_octave_shifts[voice_id % len(voice_octave_shifts)]
            self._last_voice_notes[voice_id] = -1
    
    def _apply_section_settings(self):
        """Apply the current section's settings to the sequencer state."""
        if not self._current_pattern or self._current_section_index >= len(self._current_pattern.sections):
            return
        
        section = self._current_pattern.sections[self._current_section_index]
        
        # Apply tempo changes
        new_bpm = self._base_bpm * section.tempo_factor
        self.state.set('bpm', new_bpm, source='song_mode')
        
        # Apply density changes
        new_density = min(1.0, max(0.1, section.density))
        self.state.set('density', new_density, source='song_mode')
        
        # Apply step pattern if specified
        if section.step_pattern:
            # Note: This requires the sequencer to have pattern preset support
            # For now, we'll store it in state and let the main sequencer apply it
            self.state.set('song_step_pattern', section.step_pattern, source='song_mode')
        
        # Log section change
        section_info = f"section={section.section_type.value} bars={section.bars} density={section.density:.2f} tempo_factor={section.tempo_factor:.2f}"
        if section.octave_shift != 0:
            section_info += f" octave_shift={section.octave_shift:+d}"
        if section.velocity_factor != 1.0:
            section_info += f" velocity_factor={section.velocity_factor:.2f}"
        
        log.info(f"song_section_started {section_info}")
    
    def get_next_step_notes(self, step: int) -> List[Tuple[int, int, float]]:
        """
        Generate notes for the next step in song mode.
        
        Args:
            step: Current step number
            
        Returns:
            List of (note, velocity, duration) tuples for this step
        """
        if self._between_songs:
            # Check if we should start a new song
            elapsed = time.perf_counter() - self._between_songs_start
            if elapsed >= 5.0:  # 5 second pause between songs
                self.start_new_song()
            return []  # No notes during between-songs period
        
        if not self._current_pattern:
            self.start_new_song()
            if not self._current_pattern:
                return []
        
        # Check if we need to advance to the next section
        self._check_section_advancement(step)
        
        if self._current_section_index >= len(self._current_pattern.sections):
            # Song is complete, start between-songs period
            self._start_between_songs()
            return []
        
        # Generate notes for current section
        return self._generate_section_notes(step)
    
    def _check_section_advancement(self, step: int):
        """Check if we should advance to the next section based on timing."""
        if not self._current_pattern or self._current_section_index >= len(self._current_pattern.sections):
            return
        
        current_section = self._current_pattern.sections[self._current_section_index]
        
        # Calculate beats per bar (assuming 4/4 time)
        beats_per_bar = 4
        bpm = self.state.get('bpm', 120.0)
        steps_per_beat = 4  # 16th notes
        
        # Calculate how many steps represent one bar
        steps_per_bar = beats_per_bar * steps_per_beat
        
        # Check if we've completed the required number of bars for this section
        bars_completed = self._section_bar_count
        
        # Increment bar count based on step progression
        if step % steps_per_bar == 0 and step > 0:
            self._section_bar_count += 1
            bars_completed = self._section_bar_count
        
        if bars_completed >= current_section.bars:
            # Move to next section
            self._current_section_index += 1
            self._section_start_time = time.perf_counter()
            self._section_bar_count = 0
            
            if self._current_section_index < len(self._current_pattern.sections):
                self._apply_section_settings()
            else:
                log.info(f"song_completed pattern={self._current_pattern.name}")
    
    def _start_between_songs(self):
        """Start the pause between songs."""
        self._between_songs = True
        self._between_songs_start = time.perf_counter()
        self._current_pattern = None
        self._current_section_index = 0
        
        # Reset state to base values
        self.state.set('bpm', self._base_bpm, source='song_mode')
        self.state.set('density', self._base_density, source='song_mode')
        
        log.info("song_between_songs_started duration=5.0s")
    
    def _generate_section_notes(self, step: int) -> List[Tuple[int, int, float]]:
        """Generate notes for the current section and step."""
        if not self._current_pattern or self._current_section_index >= len(self._current_pattern.sections):
            return []
        
        current_section = self._current_pattern.sections[self._current_section_index]
        
        # Get number of voices
        num_voices = self.state.get('voices', 1)
        
        # Generate notes for each voice
        notes = []
        for voice_id in range(num_voices):
            note_data = self._generate_voice_note(voice_id, step, current_section)
            if note_data:
                notes.append(note_data)
        
        return notes
    
    def _generate_voice_note(self, voice_id: int, step: int, section: SongSection) -> Optional[Tuple[int, int, float]]:
        """Generate a note for a specific voice."""
        # Check section density (acts as note probability for this voice)
        if random.random() > section.density:
            return None
        
        # Get the pattern for this voice
        if voice_id not in self._voice_patterns:
            return None
        
        voice_pattern = self._voice_patterns[voice_id]
        pattern_position = step % len(voice_pattern)
        scale_degree = voice_pattern[pattern_position]
        
        # Add some variation to prevent repetitive patterns
        if random.random() < 0.3:  # 30% chance of variation
            scale_degree += random.choice([-1, 1])  # Move to adjacent scale degree
        
        # Get base octave shift for this voice
        base_octave_shift = self._voice_octave_shifts.get(voice_id, 0)
        total_octave_shift = base_octave_shift + section.octave_shift
        
        # Generate the note
        try:
            note = self.scale_mapper.get_note(scale_degree, octave=total_octave_shift)
        except (ValueError, IndexError):
            # Fallback if scale degree is out of range
            note = self.scale_mapper.get_note(0, octave=total_octave_shift)
        
        # Apply voice leading (prefer smooth motion)
        last_note = self._last_voice_notes.get(voice_id, -1)
        if last_note != -1:
            # If the interval is too large, try to find a closer note
            interval = abs(note - last_note)
            if interval > 7:  # More than a fifth
                # Try the same scale degree in a different octave
                for octave_adj in [-1, 1]:
                    alt_note = self.scale_mapper.get_note(scale_degree, octave=total_octave_shift + octave_adj)
                    alt_interval = abs(alt_note - last_note)
                    if alt_interval < interval:
                        note = alt_note
                        break
        
        self._last_voice_notes[voice_id] = note
        
        # Calculate velocity with section factor
        base_velocity = self._base_velocity
        velocity_range = self._base_velocity_range
        velocity_factor = section.velocity_factor
        
        # Add some voice-based velocity variation
        voice_velocity_factors = [1.0, 0.9, 0.8, 0.7]  # Main melody louder
        voice_factor = voice_velocity_factors[voice_id % len(voice_velocity_factors)]
        
        final_velocity = int(base_velocity * velocity_factor * voice_factor)
        final_velocity = max(1, min(127, final_velocity))
        
        # Calculate duration
        bpm = self.state.get('bpm', 120.0)
        step_duration = 60.0 / (bpm * 4)  # Duration of one 16th note
        gate_length_factor = self._base_gate_length
        duration = step_duration * gate_length_factor
        
        return (note, final_velocity, duration)
    
    def get_current_song_info(self) -> Dict[str, Any]:
        """Get information about the current song state."""
        if self._between_songs:
            elapsed = time.perf_counter() - self._between_songs_start
            return {
                "status": "between_songs",
                "time_until_next_song": max(0, 5.0 - elapsed),
                "pattern": None,
                "section": None
            }
        
        if not self._current_pattern:
            return {
                "status": "no_song",
                "pattern": None,
                "section": None
            }
        
        current_section = None
        if self._current_section_index < len(self._current_pattern.sections):
            section = self._current_pattern.sections[self._current_section_index]
            current_section = {
                "type": section.section_type.value,
                "bars": section.bars,
                "bars_completed": self._section_bar_count,
                "density": section.density,
                "tempo_factor": section.tempo_factor,
                "octave_shift": section.octave_shift,
                "velocity_factor": section.velocity_factor
            }
        
        elapsed = time.perf_counter() - self._song_start_time
        
        return {
            "status": "playing",
            "pattern": self._current_pattern.name,
            "section": current_section,
            "section_index": self._current_section_index,
            "total_sections": len(self._current_pattern.sections),
            "elapsed_time": elapsed,
            "estimated_duration": self._current_pattern.estimated_duration_minutes * 60,
            "voices": len(self._voice_patterns)
        }
    
    def force_next_section(self):
        """Force advancement to the next section (for testing/debugging)."""
        if self._current_pattern and self._current_section_index < len(self._current_pattern.sections):
            self._current_section_index += 1
            self._section_start_time = time.perf_counter()
            self._section_bar_count = 0
            
            if self._current_section_index < len(self._current_pattern.sections):
                self._apply_section_settings()
                log.info(f"song_section_forced_advance index={self._current_section_index}")
            else:
                self._start_between_songs()
    
    def force_new_song(self):
        """Force start of a new song (for testing/debugging)."""
        self._between_songs = False
        self.start_new_song()


def create_song_sequencer(state: State, scale_mapper: ScaleMapper) -> SongSequencer:
    """Factory function to create a song sequencer instance."""
    return SongSequencer(state, scale_mapper)
