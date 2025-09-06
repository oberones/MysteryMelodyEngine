from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SemanticEvent:
    """High-level semantic action derived from raw MIDI.

    Phase 1 keeps this minimal; future phases can extend with more fields.
    """

    type: str  # e.g., 'trigger_step', 'tempo', 'density'
    source: str  # 'button' | 'cc'
    value: Optional[int] = None  # velocity for notes, CC value for params
    raw_note: Optional[int] = None
    raw_cc: Optional[int] = None
    channel: Optional[int] = None  # 1-based channel

    def log_str(self) -> str:
        parts = [f"type={self.type}", f"source={self.source}"]
        if self.value is not None:
            parts.append(f"value={self.value}")
        if self.raw_note is not None:
            parts.append(f"note={self.raw_note}")
        if self.raw_cc is not None:
            parts.append(f"cc={self.raw_cc}")
        if self.channel is not None:
            parts.append(f"ch={self.channel}")
        return " ".join(parts)
