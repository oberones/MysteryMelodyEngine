"""
Scale and note mapping utilities for the generative engine.

Provides functionality to map abstract pitch values to specific notes within
a defined musical scale.
"""

from __future__ import annotations
from typing import Dict, List, Optional

# Standard scale definitions (intervals in semitones from the root)
SCALES: Dict[str, List[int]] = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "locrian": [0, 1, 3, 5, 6, 8, 10],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "blues": [0, 3, 5, 6, 7, 10],
    "chromatic": list(range(12)),
}


class ScaleMapper:
    """Maps pitches to a specific musical scale and root note."""

    def __init__(self, scale_definitions: Optional[Dict[str, List[int]]] = None):
        self.scale_definitions = scale_definitions or SCALES
        self.current_scale_name: str = "major"
        self.current_scale_intervals: List[int] = self.scale_definitions["major"]
        self.root_note: int = 60  # C4

    def set_scale(self, scale_name: str, root_note: int = 60):
        """
        Set the current scale and root note.

        Args:
            scale_name: The name of the scale (e.g., "major", "pentatonic_minor").
            root_note: The MIDI note number for the root of the scale.
        """
        scale_name = scale_name.lower()
        if scale_name in self.scale_definitions:
            self.current_scale_name = scale_name
            self.current_scale_intervals = self.scale_definitions[scale_name]
            self.root_note = root_note
        else:
            raise ValueError(f"Scale '{scale_name}' not defined.")

    def get_note(self, degree: int, octave: int = 0) -> int:
        """
        Get a MIDI note for a given scale degree and octave.

        Args:
            degree: The 0-indexed degree of the scale (e.g., 0 for root, 1 for second).
            octave: The octave offset from the root note's octave.

        Returns:
            The MIDI note number.
        """
        if not self.current_scale_intervals:
            return self.root_note

        scale_len = len(self.current_scale_intervals)
        octave_offset = (degree // scale_len) * 12
        interval = self.current_scale_intervals[degree % scale_len]

        return self.root_note + interval + (octave * 12) + octave_offset

    def get_notes(self, num_notes: int, start_degree: int = 0, octave: int = 0) -> List[int]:
        """
        Get a sequence of notes from the current scale.

        Args:
            num_notes: The number of notes to generate.
            start_degree: The starting scale degree.
            octave: The starting octave.

        Returns:
            A list of MIDI note numbers.
        """
        return [self.get_note(start_degree + i, octave) for i in range(num_notes)]
