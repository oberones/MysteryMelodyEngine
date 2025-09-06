# Enhanced Note Logging Documentation

This project now includes enhanced logging that displays MIDI note numbers alongside their musical note names (e.g., "C4(60)", "A#3(58)") for better musical understanding and debugging.

## Enhanced Logging Features

### Note Display Format
- **Standard notes**: `C4(60)`, `D4(62)`, `A4(69)`
- **Sharp notes**: `C#4(61)`, `F#3(54)`
- **Rest events**: `REST(-1)`

### Affected Log Messages

#### Main Note Events
```
note_event note=D4(62) velocity=96 step=0 duration=0.231
note_event note=REST(-1) velocity=0 step=1 duration=0.500
```

#### Sequencer Debug Logging
```
fugue_note_generated step=7 note=A4(69) velocity=96 duration=0.231
note_generated step=3 note=C4(60) velocity=80 gate_length=0.450 step_prob=0.85
```

#### MIDI Input/Output
```
Received MIDI note_on: note=C4(60) velocity=100 channel=1
Sent Note On: note=D4(62) velocity=96 channel=10
Sent Note Off: note=A4(69) velocity=0 channel=10
```

#### Scale and Root Note Configuration
```
sequencer_root_note=D4(62)
scale_set name='minor' root=D4(62)
```

#### Manual Trigger Events
```
manual_trigger step=5 note=F4(65) velocity=80
```

#### Error Messages
```
Failed to send note on: note=C4(60) error=Connection lost
Failed to send note off: note=G4(67) error=Device not found
```

## Configuration

The enhanced logging is enabled by default and works at all log levels. Note names are automatically calculated from MIDI note numbers using standard musical notation:

- **Octave calculation**: MIDI note 60 = C4 (middle C)
- **Sharp notation**: Uses sharps (#) by default
- **Flat notation**: Available via `note_to_name_flat()` function

## Testing

Run the test script to verify note name conversions:

```bash
source .venv/bin/activate
python test_note_logging.py
```

## Implementation Details

### Core Functions
- `note_to_name(note_number)`: Convert MIDI number to note name
- `format_note_with_number(note_number)`: Format for logging display
- `format_rest()`: Format rest events

### Enhanced Modules
- `src/main.py`: Main note event logging
- `src/sequencer.py`: Sequencer note generation
- `src/midi_in.py`: MIDI input message logging
- `src/midi_out.py`: MIDI output message logging
- `src/action_handler.py`: Manual trigger logging
- `src/external_hardware.py`: External hardware error logging

### Debug Scripts
- `debug_fugue_generation.py`: Enhanced with note names
- `debug_runtime_fugue.py`: Enhanced with note names

## Benefits

1. **Musical Understanding**: Easily see what notes are being played musically
2. **Debugging**: Quickly identify note patterns and ranges
3. **Configuration Verification**: Confirm root notes and scale changes
4. **MIDI Troubleshooting**: Better understand MIDI communication issues
5. **Educational**: Learn the relationship between MIDI numbers and musical notes

## Examples

### Button Mapping (60-69)
```
Button 1: C4(60)
Button 2: C#4(61) 
Button 3: D4(62)
Button 4: D#4(63)
Button 5: E4(64)
Button 6: F4(65)
Button 7: F#4(66)
Button 8: G4(67)
Button 9: G#4(68)
Button 10: A4(69)
```

### Common Scale Roots
```
C4(60) major scale
D4(62) major scale  
E4(64) major scale
F4(65) major scale
G4(67) major scale
A4(69) major scale
B4(71) major scale
```
