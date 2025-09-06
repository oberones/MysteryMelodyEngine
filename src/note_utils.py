"""
Note utility functions for MIDI note handling and display.
"""


def note_to_name(note_number: int) -> str:
    """
    Convert MIDI note number to note name with octave.
    
    Args:
        note_number: MIDI note number (0-127)
        
    Returns:
        Note name with octave (e.g., "C4", "A#3", "Gb5")
        
    Examples:
        >>> note_to_name(60)
        'C4'
        >>> note_to_name(69)
        'A4' 
        >>> note_to_name(61)
        'C#4'
    """
    if note_number < 0 or note_number > 127:
        return f"Invalid({note_number})"
    
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = note_number // 12 - 1
    note_name = note_names[note_number % 12]
    return f"{note_name}{octave}"


def note_to_name_flat(note_number: int) -> str:
    """
    Convert MIDI note number to note name with octave using flat notation for black keys.
    
    Args:
        note_number: MIDI note number (0-127)
        
    Returns:
        Note name with octave using flats (e.g., "C4", "Bb3", "Db5")
        
    Examples:
        >>> note_to_name_flat(60)
        'C4'
        >>> note_to_name_flat(61)
        'Db4'
        >>> note_to_name_flat(70)
        'Bb4'
    """
    if note_number < 0 or note_number > 127:
        return f"Invalid({note_number})"
    
    note_names = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
    octave = note_number // 12 - 1
    note_name = note_names[note_number % 12]
    return f"{note_name}{octave}"


def format_note_with_number(note_number: int, use_flats: bool = False) -> str:
    """
    Format a MIDI note number with both name and number for logging.
    
    Args:
        note_number: MIDI note number (0-127)
        use_flats: If True, use flat notation for black keys
        
    Returns:
        Formatted string with note name and number (e.g., "C4(60)", "A#3(58)")
        
    Examples:
        >>> format_note_with_number(60)
        'C4(60)'
        >>> format_note_with_number(61, use_flats=True)
        'Db4(61)'
    """
    if note_number < 0 or note_number > 127:
        return f"Invalid({note_number})"
    
    if use_flats:
        note_name = note_to_name_flat(note_number)
    else:
        note_name = note_to_name(note_number)
    
    return f"{note_name}({note_number})"


def format_rest() -> str:
    """
    Format a rest for logging.
    
    Returns:
        Formatted string for rest events
    """
    return "REST(-1)"


__all__ = [
    "note_to_name", 
    "note_to_name_flat", 
    "format_note_with_number", 
    "format_rest"
]
