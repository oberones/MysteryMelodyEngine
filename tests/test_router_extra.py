from router import Router
from config import load_config
import mido
import pytest


def test_unmapped_note_ignored():
    cfg = load_config("tests/test.yaml")
    events = []
    r = Router(cfg, events.append)
    msg = mido.Message("note_on", note=12, velocity=100, channel=cfg.midi.input_channel - 1)
    r.route(msg)
    assert events == []


def test_unmapped_cc_ignored():
    cfg = load_config("tests/test.yaml")
    events = []
    r = Router(cfg, events.append)
    msg = mido.Message(
        "control_change", control=5, value=10, channel=cfg.midi.input_channel - 1
    )
    r.route(msg)
    assert events == []


def test_invalid_range_in_mapping_raises(tmp_path):
    bad_cfg = tmp_path / "bad.yaml"
    bad_cfg.write_text(
        """
midi:
  input_port: auto
  channel: 1
mapping:
  buttons:
    "69-60": trigger_step
""",
        encoding="utf-8",
    )
    from config import load_config as load_bad

    cfg = load_bad(str(bad_cfg))
    with pytest.raises(ValueError):
        Router(cfg, lambda e: None)
