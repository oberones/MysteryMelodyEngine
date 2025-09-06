from config import load_config, RootConfig


def test_load_config():
    cfg = load_config("tests/test.yaml")
    assert isinstance(cfg, RootConfig)
    assert cfg.sequencer.steps == 8
    assert cfg.synth.backend == "supercollider"
    assert cfg.idle.fade_in_ms == 4000
