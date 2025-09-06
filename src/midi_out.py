"""MIDI Output module for the generative engine.

Phase 3: Optional MIDI output allows for messages to be sent to attached MIDI devices.
Provides note on/off and control change message transmission.
"""

from __future__ import annotations
from typing import Optional, Protocol
import logging
import mido
import time
from note_utils import format_note_with_number

log = logging.getLogger(__name__)


class MidiMessageSender(Protocol):
    """Protocol for MIDI message sending."""
    
    def send_note_on(self, note: int, velocity: int, channel: int = 1) -> None:
        """Send a MIDI Note On message."""
        ...
    
    def send_note_off(self, note: int, velocity: int, channel: int = 1) -> None:
        """Send a MIDI Note Off message."""
        ...
    
    def send_control_change(self, control: int, value: int, channel: int = 1) -> None:
        """Send a MIDI Control Change message."""
        ...
    
    def close(self) -> None:
        """Close the MIDI output port."""
        ...


class MidiOutput:
    """MIDI output handler with connection management and message sending."""
    
    def __init__(self, port_name: Optional[str] = None, channel: int = 1):
        self.port_name = port_name
        self.channel = channel
        self.port: Optional[mido.ports.BaseOutput] = None
        self._is_connected = False
        
        if port_name:
            self._connect()
    
    def _connect(self) -> bool:
        """Attempt to connect to the MIDI output port."""
        if not self.port_name:
            return False
        
        try:
            # Handle auto port selection
            if self.port_name == "auto":
                available_ports = mido.get_output_names()
                if not available_ports:
                    log.warning("No MIDI output ports available")
                    return False
                
                # Prefer ports that aren't virtual or loopback
                preferred_ports = [p for p in available_ports 
                                 if not any(keyword in p.lower() 
                                          for keyword in ['virtual', 'loopback', 'through'])]
                
                if preferred_ports:
                    self.port_name = preferred_ports[0]
                else:
                    self.port_name = available_ports[0]
                
                log.info(f"Auto-selected MIDI output port: {self.port_name}")
            
            self.port = mido.open_output(self.port_name)
            self._is_connected = True
            log.info(f"Connected to MIDI output port: {self.port_name}")
            return True
            
        except Exception as e:
            log.error(f"Failed to connect to MIDI output port '{self.port_name}': {e}")
            self.port = None
            self._is_connected = False
            return False
    
    def _ensure_connected(self) -> bool:
        """Ensure MIDI port is connected, attempt reconnection if needed."""
        if self._is_connected and self.port:
            return True
        
        if self.port_name:
            return self._connect()
        
        return False
    
    def send_note_on(self, note: int, velocity: int, channel: Optional[int] = None) -> bool:
        """Send a MIDI Note On message.
        
        Args:
            note: MIDI note number (0-127)
            velocity: Note velocity (1-127, 0 is treated as Note Off)
            channel: MIDI channel (1-16), uses default if None
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self._ensure_connected():
            return False
        
        if velocity <= 0:
            return self.send_note_off(note, 0, channel)
        
        try:
            ch = (channel or self.channel) - 1  # Convert to 0-based
            msg = mido.Message('note_on', channel=ch, note=note, velocity=velocity)
            self.port.send(msg)
            log.debug(f"Sent Note On: note={format_note_with_number(note)} velocity={velocity} channel={channel or self.channel}")
            return True
            
        except Exception as e:
            log.error(f"Failed to send Note On message: {e}")
            self._is_connected = False
            return False
    
    def send_note_off(self, note: int, velocity: int = 0, channel: Optional[int] = None) -> bool:
        """Send a MIDI Note Off message.
        
        Args:
            note: MIDI note number (0-127)
            velocity: Release velocity (0-127)
            channel: MIDI channel (1-16), uses default if None
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self._ensure_connected():
            return False
        
        try:
            ch = (channel or self.channel) - 1  # Convert to 0-based
            msg = mido.Message('note_off', channel=ch, note=note, velocity=velocity)
            self.port.send(msg)
            log.debug(f"Sent Note Off: note={format_note_with_number(note)} velocity={velocity} channel={channel or self.channel}")
            return True
            
        except Exception as e:
            log.error(f"Failed to send Note Off message: {e}")
            self._is_connected = False
            return False
    
    def send_control_change(self, control: int, value: int, channel: Optional[int] = None) -> bool:
        """Send a MIDI Control Change message.
        
        Args:
            control: Controller number (0-127)
            value: Controller value (0-127)
            channel: MIDI channel (1-16), uses default if None
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self._ensure_connected():
            return False
        
        try:
            ch = (channel or self.channel) - 1  # Convert to 0-based
            msg = mido.Message('control_change', channel=ch, control=control, value=value)
            self.port.send(msg)
            log.debug(f"Sent CC: control={control} value={value} channel={channel or self.channel}")
            return True
            
        except Exception as e:
            log.error(f"Failed to send Control Change message: {e}")
            self._is_connected = False
            return False
    
    def send_all_notes_off(self, channel: Optional[int] = None) -> bool:
        """Send All Notes Off control change message.
        
        Args:
            channel: MIDI channel (1-16), uses default if None
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        return self.send_control_change(123, 0, channel)
    
    def close(self) -> None:
        """Close the MIDI output port."""
        if self.port:
            try:
                # Send all notes off before closing
                self.send_all_notes_off()
                self.port.close()
                log.info(f"Closed MIDI output port: {self.port_name}")
            except Exception as e:
                log.error(f"Error closing MIDI output port: {e}")
            finally:
                self.port = None
                self._is_connected = False
    
    @property
    def is_connected(self) -> bool:
        """Check if MIDI output is connected."""
        return self._is_connected
    
    @classmethod
    def create(cls, port_name: Optional[str], channel: int = 1) -> Optional[MidiOutput]:
        """Factory method to create a MIDI output instance.
        
        Args:
            port_name: Name of MIDI port, "auto" for auto-selection, or None to disable
            channel: Default MIDI channel (1-16)
            
        Returns:
            MidiOutput instance if successful, None if disabled or failed
        """
        if not port_name:
            log.info("MIDI output disabled (no port specified)")
            return None
        
        try:
            output = cls(port_name, channel)
            if output.is_connected:
                return output
            else:
                log.warning("MIDI output creation failed - port not connected")
                return None
                
        except Exception as e:
            log.error(f"Failed to create MIDI output: {e}")
            return None


class NullMidiOutput:
    """Null MIDI output for when MIDI output is disabled."""
    
    def send_note_on(self, note: int, velocity: int, channel: int = 1) -> bool:
        return True
    
    def send_note_off(self, note: int, velocity: int = 0, channel: int = 1) -> bool:
        return True
    
    def send_control_change(self, control: int, value: int, channel: int = 1) -> bool:
        return True
    
    def send_all_notes_off(self, channel: int = 1) -> bool:
        return True
    
    def close(self) -> None:
        pass
    
    @property
    def is_connected(self) -> bool:
        return False


def get_available_output_ports() -> list[str]:
    """Get list of available MIDI output ports."""
    try:
        return mido.get_output_names()
    except Exception as e:
        log.error(f"Failed to get MIDI output ports: {e}")
        return []