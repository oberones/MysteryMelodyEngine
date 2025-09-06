"""MIDI Clock synchronization for external hardware.

Phase 7: Provides MIDI clock output to synchronize external devices 
with the sequencer tempo and timing.
"""

from __future__ import annotations
from typing import Optional, Protocol, Callable
import threading
import time
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class ClockStatus:
    """Status information for MIDI clock."""
    running: bool = False
    bpm: float = 120.0
    position: int = 0  # MIDI beat clock position (24 PPQN)
    song_position: int = 0  # Song position in 16th notes
    
    
class MidiClockSender(Protocol):
    """Protocol for MIDI clock message sending."""
    
    def send_clock(self) -> None:
        """Send MIDI clock tick (0xF8)."""
        ...
    
    def send_start(self) -> None:
        """Send MIDI start message (0xFA)."""
        ...
    
    def send_stop(self) -> None:
        """Send MIDI stop message (0xFC)."""
        ...
    
    def send_continue(self) -> None:
        """Send MIDI continue message (0xFB)."""
        ...
    
    def send_song_position(self, position: int) -> None:
        """Send MIDI song position pointer (0xF2)."""
        ...


class MidiClock:
    """MIDI clock generator with precise timing.
    
    Generates MIDI clock messages at 24 PPQN (pulses per quarter note)
    synchronized to the sequencer BPM.
    """
    
    def __init__(self, midi_sender: Optional[MidiClockSender] = None):
        self.midi_sender = midi_sender
        self.status = ClockStatus()
        
        # Threading
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Timing
        self._clock_interval = 0.0  # Seconds between clock ticks
        self._next_tick_time = 0.0
        self._start_time = 0.0
        
        # Callbacks
        self._tick_callback: Optional[Callable[[int], None]] = None
        
        self._update_timing()
    
    def set_bpm(self, bpm: float) -> None:
        """Set the BPM and update timing.
        
        Args:
            bpm: Beats per minute (typically 60-200)
        """
        if bpm <= 0:
            log.warning(f"Invalid BPM value: {bpm}")
            return
        
        self.status.bpm = bpm
        self._update_timing()
        log.debug(f"MIDI clock BPM set to {bpm}")
    
    def _update_timing(self) -> None:
        """Update internal timing calculations based on current BPM."""
        # MIDI clock runs at 24 PPQN (24 ticks per quarter note)
        # So interval = 60 / (BPM * 24) seconds
        self._clock_interval = 60.0 / (self.status.bpm * 24)
    
    def start(self) -> None:
        """Start the MIDI clock.
        
        Sends MIDI Start message and begins clock output.
        """
        if self.status.running:
            log.warning("MIDI clock already running")
            return
        
        if not self.midi_sender:
            log.warning("No MIDI sender configured for clock")
            return
        
        self.status.running = True
        self.status.position = 0
        self.status.song_position = 0
        
        # Send MIDI start message
        self.midi_sender.send_start()
        
        # Initialize timing
        self._start_time = time.perf_counter()
        self._next_tick_time = self._start_time + self._clock_interval
        
        # Start clock thread
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._clock_loop, daemon=True)
        self._thread.start()
        
        log.info(f"MIDI clock started at {self.status.bpm} BPM")
    
    def stop(self) -> None:
        """Stop the MIDI clock.
        
        Sends MIDI Stop message and halts clock output.
        """
        if not self.status.running:
            return
        
        self.status.running = False
        
        # Stop thread
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        
        # Send MIDI stop message
        if self.midi_sender:
            self.midi_sender.send_stop()
        
        log.info("MIDI clock stopped")
    
    def pause(self) -> None:
        """Pause the MIDI clock without resetting position."""
        if not self.status.running:
            return
        
        self.status.running = False
        self._stop_event.set()
        
        if self.midi_sender:
            self.midi_sender.send_stop()
        
        log.info("MIDI clock paused")
    
    def resume(self) -> None:
        """Resume the MIDI clock from current position."""
        if self.status.running:
            return
        
        if not self.midi_sender:
            log.warning("No MIDI sender configured for clock")
            return
        
        self.status.running = True
        
        # Send MIDI continue message
        self.midi_sender.send_continue()
        
        # Restart timing from current position
        current_time = time.perf_counter()
        self._next_tick_time = current_time + self._clock_interval
        
        # Restart thread
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._clock_loop, daemon=True)
        self._thread.start()
        
        log.info("MIDI clock resumed")
    
    def reset_position(self) -> None:
        """Reset song position to 0."""
        was_running = self.status.running
        
        if was_running:
            self.stop()
        
        self.status.position = 0
        self.status.song_position = 0
        
        if self.midi_sender:
            self.midi_sender.send_song_position(0)
        
        if was_running:
            self.start()
        
        log.debug("MIDI clock position reset")
    
    def set_song_position(self, position: int) -> None:
        """Set song position in 16th notes.
        
        Args:
            position: Song position in 16th note increments
        """
        self.status.song_position = position
        
        # Convert to 24 PPQN position
        # 16th note = 6 MIDI clocks (24 PPQN / 4)
        self.status.position = position * 6
        
        if self.midi_sender:
            self.midi_sender.send_song_position(position)
        
        log.debug(f"MIDI clock song position set to {position}")
    
    def set_tick_callback(self, callback: Optional[Callable[[int], None]]) -> None:
        """Set callback function called on each clock tick.
        
        Args:
            callback: Function called with current position (24 PPQN)
        """
        self._tick_callback = callback
    
    def _clock_loop(self) -> None:
        """Main clock loop running in separate thread."""
        log.debug("MIDI clock thread started")
        
        while not self._stop_event.is_set():
            current_time = time.perf_counter()
            
            # Check if it's time for next tick
            if current_time >= self._next_tick_time:
                self._send_tick()
                
                # Schedule next tick with drift correction
                self._next_tick_time += self._clock_interval
                
                # Prevent runaway catch-up if we fall too far behind
                if self._next_tick_time < current_time:
                    missed_ticks = int((current_time - self._next_tick_time) / self._clock_interval)
                    if missed_ticks > 5:  # Allow small catch-up but prevent spiral
                        log.warning(f"MIDI clock fell behind by {missed_ticks} ticks, resetting timing")
                        self._next_tick_time = current_time + self._clock_interval
            
            # Sleep until next tick (but not too long to maintain responsiveness)
            sleep_time = min(self._next_tick_time - current_time, 0.001)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        log.debug("MIDI clock thread stopped")
    
    def _send_tick(self) -> None:
        """Send a single MIDI clock tick."""
        if not self.midi_sender:
            return
        
        try:
            # Send MIDI clock message
            self.midi_sender.send_clock()
            
            # Update position
            self.status.position += 1
            
            # Update song position every 6 ticks (16th note boundary)
            if self.status.position % 6 == 0:
                self.status.song_position = self.status.position // 6
            
            # Call tick callback if set
            if self._tick_callback:
                self._tick_callback(self.status.position)
        
        except Exception as e:
            log.error(f"Error sending MIDI clock tick: {e}")


class MidiClockAdapter:
    """Adapter to connect MIDI clock to MIDI output."""
    
    def __init__(self, midi_output):
        """Initialize with a MIDI output instance.
        
        Args:
            midi_output: MIDI output instance with send methods
        """
        self.midi_output = midi_output
    
    def send_clock(self) -> None:
        """Send MIDI clock tick (0xF8)."""
        if hasattr(self.midi_output, 'port') and self.midi_output.port:
            try:
                import mido
                msg = mido.Message('clock')
                self.midi_output.port.send(msg)
            except Exception as e:
                log.error(f"Failed to send MIDI clock: {e}")
    
    def send_start(self) -> None:
        """Send MIDI start message (0xFA)."""
        if hasattr(self.midi_output, 'port') and self.midi_output.port:
            try:
                import mido
                msg = mido.Message('start')
                self.midi_output.port.send(msg)
            except Exception as e:
                log.error(f"Failed to send MIDI start: {e}")
    
    def send_stop(self) -> None:
        """Send MIDI stop message (0xFC)."""
        if hasattr(self.midi_output, 'port') and self.midi_output.port:
            try:
                import mido
                msg = mido.Message('stop')
                self.midi_output.port.send(msg)
            except Exception as e:
                log.error(f"Failed to send MIDI stop: {e}")
    
    def send_continue(self) -> None:
        """Send MIDI continue message (0xFB)."""
        if hasattr(self.midi_output, 'port') and self.midi_output.port:
            try:
                import mido
                msg = mido.Message('continue')
                self.midi_output.port.send(msg)
            except Exception as e:
                log.error(f"Failed to send MIDI continue: {e}")
    
    def send_song_position(self, position: int) -> None:
        """Send MIDI song position pointer (0xF2).
        
        Args:
            position: Song position in 16th notes
        """
        if hasattr(self.midi_output, 'port') and self.midi_output.port:
            try:
                import mido
                msg = mido.Message('songpos', pos=position)
                self.midi_output.port.send(msg)
            except Exception as e:
                log.error(f"Failed to send MIDI song position: {e}")


class NullMidiClockSender:
    """Null MIDI clock sender for when clock is disabled."""
    
    def send_clock(self) -> None:
        pass
    
    def send_start(self) -> None:
        pass
    
    def send_stop(self) -> None:
        pass
    
    def send_continue(self) -> None:
        pass
    
    def send_song_position(self, position: int) -> None:
        pass
