from router import Router
from config import load_config
from events import SemanticEvent
import mido


def collect_events(cfg_path="tests/test.yaml"):
    cfg = load_config(cfg_path)
    events = []
    r = Router(cfg, lambda e: events.append(e))
    return r, events, cfg


def test_note_mapping_triggers_event():
    router, events, cfg = collect_events()
    msg = mido.Message("note_on", note=60, velocity=100, channel=cfg.midi.input_channel - 1)
    router.route(msg)
    assert len(events) == 1
    evt = events[0]
    assert isinstance(evt, SemanticEvent)
    assert evt.type == "trigger_step"
    assert evt.raw_note == 60
    assert evt.value == 100


def test_cc_mapping_triggers_event():
    router, events, cfg = collect_events()
    msg = mido.Message("control_change", control=24, value=64, channel=cfg.midi.input_channel - 1)
    router.route(msg)
    assert len(events) == 1
    evt = events[0]
    assert evt.type == "density"
    assert evt.raw_cc == 24
    assert evt.value == 64


def test_channel_filter():
    router, events, cfg = collect_events()
    other_channel = (cfg.midi.input_channel % 16)  # different 0-based channel
    msg = mido.Message("note_on", note=60, velocity=100, channel=other_channel)
    router.route(msg)
    assert events == []


def test_note_off_ignored_phase1():
    router, events, cfg = collect_events()
    msg_on = mido.Message("note_on", note=60, velocity=100, channel=cfg.midi.input_channel - 1)
    router.route(msg_on)
    msg_off = mido.Message("note_off", note=60, velocity=0, channel=cfg.midi.input_channel - 1)
    router.route(msg_off)
    assert len(events) == 1
