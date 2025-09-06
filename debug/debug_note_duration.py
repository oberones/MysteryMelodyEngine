#!/usr/bin/env python3
"""Debug script to verify note duration and note-off events are working correctly."""

import time
import logging
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import load_config
from state import get_state
from sequencer import create_sequencer, NoteEvent
from midi_out import MidiOutput, NullMidiOutput
from external_hardware import ExternalHardwareManager

# Set up logging to see what's happening
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log = logging.getLogger("note_debug")

class DebugMidiOutput:
    """Debug MIDI output that logs all note events."""
    
    def __init__(self):
        self.note_on_events = []
        self.note_off_events = []
        self.active_notes = set()
    
    def send_note_on(self, note, velocity, channel=1):
        timestamp = time.perf_counter()
        self.note_on_events.append((timestamp, note, velocity, channel))
        self.active_notes.add(note)
        print(f"[{timestamp:.3f}] NOTE ON: note={note} velocity={velocity} channel={channel}")
        print(f"  Active notes: {sorted(self.active_notes)}")
        return True
    
    def send_note_off(self, note, velocity=0, channel=1):
        timestamp = time.perf_counter()
        self.note_off_events.append((timestamp, note, velocity, channel))
        self.active_notes.discard(note)
        print(f"[{timestamp:.3f}] NOTE OFF: note={note} velocity={velocity} channel={channel}")
        print(f"  Active notes: {sorted(self.active_notes)}")
        return True
    
    def send_control_change(self, control, value, channel=1):
        return True
    
    def close(self):
        pass
    
    @property
    def is_connected(self):
        return True
    
    def get_note_durations(self):
        """Calculate actual note durations based on note on/off events."""
        durations = []
        note_on_times = {}
        
        # Record note on times
        for timestamp, note, velocity, channel in self.note_on_events:
            note_on_times[note] = timestamp
        
        # Calculate durations for note offs
        for timestamp, note, velocity, channel in self.note_off_events:
            if note in note_on_times:
                duration = timestamp - note_on_times[note]
                durations.append((note, duration))
                print(f"Note {note} duration: {duration:.3f}s")
        
        return durations

class DebugNoteScheduler:
    """Debug version of note scheduler that logs scheduling."""
    
    def __init__(self, midi_output):
        self.midi_output = midi_output
        self.scheduled_notes = []
        self._running = False
    
    def start(self):
        self._running = True
        print("Note scheduler started")
    
    def stop(self):
        self._running = False
        print("Note scheduler stopped")
    
    def schedule_note_off(self, note, channel, delay):
        timestamp = time.perf_counter() + delay
        self.scheduled_notes.append((timestamp, note, channel, delay))
        print(f"SCHEDULED NOTE OFF: note={note} channel={channel} delay={delay:.3f}s at_time={timestamp:.3f}")
        
        # For debugging, send the note off immediately after the delay
        import threading
        def delayed_note_off():
            time.sleep(delay)
            self.midi_output.send_note_off(note, 0, channel)
        
        thread = threading.Thread(target=delayed_note_off, daemon=True)
        thread.start()

def main():
    print("=== Note Duration Debug Test ===")
    
    # Load config
    cfg = load_config("config.yaml")
    
    # Initialize state
    state = get_state()
    state.update_multiple({
        'bpm': 120.0,  # Moderate tempo
        'swing': 0.0,
        'density': 1.0,  # Always generate notes
        'sequence_length': 4,
        'note_probability': 1.0,  # Always generate notes when active
    }, source='debug')
    
    # Create debug MIDI output
    debug_midi = DebugMidiOutput()
    
    # Create sequencer
    sequencer = create_sequencer(state, cfg.scales)
    
    # Create debug note scheduler
    note_scheduler = DebugNoteScheduler(debug_midi)
    note_scheduler.start()
    
    # Set up note callback to use debug scheduler
    note_events = []
    
    def handle_note_event(note_event: NoteEvent):
        note_events.append(note_event)
        print(f"\n=== NOTE EVENT ===")
        print(f"Note: {note_event.note}")
        print(f"Velocity: {note_event.velocity}")
        print(f"Step: {note_event.step}")
        print(f"Duration: {note_event.duration:.3f}s")
        print(f"Timestamp: {note_event.timestamp:.3f}")
        
        # Send note on immediately
        debug_midi.send_note_on(note_event.note, note_event.velocity)
        
        # Schedule note off after duration
        note_scheduler.schedule_note_off(note_event.note, 1, note_event.duration)
    
    sequencer.set_note_callback(handle_note_event)
    
    print(f"Starting sequencer with BPM: {state.get('bpm')}")
    print(f"Sequence length: {state.get('sequence_length')}")
    print(f"Note probability: {state.get('note_probability')}")
    print(f"Density: {state.get('density')}")
    
    # Start sequencer
    sequencer.start()
    
    try:
        print("\nRunning for 3 seconds... Listen for note overlaps")
        time.sleep(3.0)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        sequencer.stop()
        note_scheduler.stop()
    
    print("\n=== SUMMARY ===")
    print(f"Total note events generated: {len(note_events)}")
    print(f"Note ON events: {len(debug_midi.note_on_events)}")
    print(f"Note OFF events: {len(debug_midi.note_off_events)}")
    print(f"Scheduled note offs: {len(note_scheduler.scheduled_notes)}")
    
    if debug_midi.active_notes:
        print(f"WARNING: Notes still active: {sorted(debug_midi.active_notes)}")
    else:
        print("✓ All notes properly released")
    
    # Calculate and display note durations
    durations = debug_midi.get_note_durations()
    if durations:
        avg_duration = sum(d[1] for d in durations) / len(durations)
        print(f"Average note duration: {avg_duration:.3f}s")
        
        # Compare with expected duration from last note event
        if note_events:
            expected_duration = note_events[-1].duration
            print(f"Expected duration: {expected_duration:.3f}s")
            print(f"Difference: {abs(avg_duration - expected_duration):.3f}s")
    
    return 0

if __name__ == "__main__":
    exit(main())
