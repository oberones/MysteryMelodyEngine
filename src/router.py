from __future__ import annotations
from typing import Dict, Callable
import logging
from mido import Message
from config import RootConfig
from events import SemanticEvent

log = logging.getLogger(__name__)


class Router:
    """Map raw MIDI messages to semantic events according to config.

    Config schema (mapping section):
      buttons: {"60-69": "trigger_step"}
      ccs: {"24": "density"}

    Ranges allowed only for buttons (notes). Unknown inputs ignored.
    """

    def __init__(self, cfg: RootConfig, emit: Callable[[SemanticEvent], None]):
        self.cfg = cfg
        self.emit = emit
        self.note_map: Dict[int, str] = {}
        self.cc_map: Dict[int, str] = {}
        self._build_maps()

    def _build_maps(self):
        buttons = self.cfg.mapping.get("buttons", {})
        for k, action in buttons.items():
            if "-" in k:
                start, end = k.split("-", 1)
                try:
                    s = int(start)
                    e = int(end)
                except ValueError:
                    raise ValueError(f"Invalid note range '{k}' in mapping.buttons")
                if s > e:
                    raise ValueError(f"Reversed range '{k}' in mapping.buttons")
                for n in range(s, e + 1):
                    self.note_map[n] = action
            else:
                self.note_map[int(k)] = action

        ccs = self.cfg.mapping.get("ccs", {})
        for k, action in ccs.items():
            self.cc_map[int(k)] = action

        log.debug(
            "Router maps built note_map=%s cc_map=%s", self.note_map, self.cc_map
        )

    def route(self, msg: Message):
        """Route a raw mido Message to semantic events.

        Config input_channel is 1-based; mido uses 0-based.
        """
        channel_conf = self.cfg.midi.input_channel - 1
        if hasattr(msg, "channel") and msg.channel != channel_conf:
            return

        if msg.type in ("note_on", "note_off"):
            note = msg.note
            action = self.note_map.get(note)
            if not action:
                return
            if msg.type == "note_off" or msg.velocity == 0:
                # Phase 1 ignores releases.
                return
            evt = SemanticEvent(
                type=action,
                source="button",
                value=msg.velocity,
                raw_note=note,
                channel=msg.channel + 1,
            )
            self.emit(evt)
            return

        if msg.type == "control_change":
            cc = msg.control
            action = self.cc_map.get(cc)
            if not action:
                return
            evt = SemanticEvent(
                type=action,
                source="cc",
                value=msg.value,
                raw_cc=cc,
                channel=msg.channel + 1,
            )
            self.emit(evt)
