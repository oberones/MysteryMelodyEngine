# MIDI Input Debug Scripts

## Quick Test
```bash
python quick_midi_test.py
```
This quickly verifies:
- Available MIDI ports
- Configuration settings
- Basic connection test

## Full Debug Script
```bash
python debug_midi_input.py
```
This provides real-time MIDI message monitoring:
- Lists all available ports
- Connects to configured port (or auto-selects)
- Shows all incoming MIDI messages on ALL channels
- Provides detailed message formatting
- Press Ctrl+C to stop

## Specific Port Testing
```bash
python debug_midi_input.py "RK006 IN_ALL"
python debug_midi_input.py "auto"
```

## Troubleshooting Steps

1. **Run quick test first**: `python quick_midi_test.py`
2. **Check available ports**: Look for your MIDI device in the list
3. **Verify configuration**: Ensure `config.yaml` has the correct port name
4. **Run full debug**: `python debug_midi_input.py` and send some MIDI data
5. **Check channels**: The debug script monitors ALL channels, not just the configured one

## Expected Output
When MIDI data is received, you should see:
```
[  2.34s] Ch: 1    note_on      Note:C4  ( 60) Vel:100
[  2.89s] Ch: 1    note_off     Note:C4  ( 60) Vel:  0
[  3.12s] Ch: 1 control_change  CC: 24    Val: 64
```

## Common Issues
- **"No MIDI input ports found"**: Check USB connections and device power
- **"Connection failed"**: Port might be in use by another application
- **"No messages received"**: Check MIDI channel, cables, or device output settings
