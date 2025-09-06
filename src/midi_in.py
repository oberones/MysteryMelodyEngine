from __future__ import annotations
import logging
from typing import Optional, Callable
import mido
from mido import Message
from note_utils import format_note_with_number

log = logging.getLogger(__name__)


class MidiInput:
    """Open a MIDI input port and dispatch messages via callback."""

    def __init__(self, port_name: str, callback: Callable[[Message], None]):
        self.port_name = port_name
        self.callback = callback
        self._port = None

    @staticmethod
    def auto_select() -> Optional[str]:
        names = mido.get_input_names()
        if not names:
            return None
        for n in names:
            if "teensy" in n.lower():
                return n
        return names[0]

    @classmethod
    def create(cls, desired: str, callback: Callable[[Message], None]):
        if desired == "auto":
            name = cls.auto_select()
            if not name:
                raise RuntimeError("No MIDI input ports available")
            log.info("Auto-selected MIDI port: %s", name)
        else:
            name = desired
        inst = cls(name, callback)
        inst.open()
        return inst

    def open(self):
        log.info("Opening MIDI input port '%s'", self.port_name)
        self._port = mido.open_input(self.port_name, callback=self._on_msg)

    def close(self):
        if self._port:
            log.info("Closing MIDI input port '%s'", self.port_name)
            self._port.close()
            self._port = None

    def _on_msg(self, msg: Message):  # mido background thread
        # Enhanced logging for note messages with note names
        if msg.type in ('note_on', 'note_off'):
            note_info = format_note_with_number(msg.note)
            log.debug(f"Received MIDI {msg.type}: note={note_info} velocity={msg.velocity} channel={msg.channel + 1}")
        else:
            log.debug("Received MIDI message: %s", msg)
        
        try:
            self.callback(msg)
        except Exception:  # noqa: broad-except
            log.exception("Error handling MIDI message: %s", msg)
