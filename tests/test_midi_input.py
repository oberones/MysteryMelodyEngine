import mido
import pytest
from midi_in import MidiInput


def test_auto_select_prefers_teensy(monkeypatch):
    monkeypatch.setattr(mido, "get_input_names", lambda: ["Other Device", "Teensy MIDI"])
    name = MidiInput.auto_select()
    assert name == "Teensy MIDI"


def test_auto_select_none(monkeypatch):
    monkeypatch.setattr(mido, "get_input_names", lambda: [])
    assert MidiInput.auto_select() is None


def test_create_no_ports(monkeypatch):
    monkeypatch.setattr(mido, "get_input_names", lambda: [])
    with pytest.raises(RuntimeError):
        MidiInput.create("auto", lambda m: None)
