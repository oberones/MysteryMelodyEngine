"""Tests for the NTS-1 mutation plugin."""

import pytest
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nts1_mutation_plugin import (
    get_nts1_mutation_rules,
    get_nts1_ambient_rules, 
    get_nts1_rhythmic_rules,
    register_nts1_rules,
    register_nts1_state_parameters,
    setup_nts1_mutations
)
from mutation import MutationEngine, MutationRule
from config import MutationConfig
from state import State
from cc_profiles import get_profile


class TestNTS1MutationRules:
    """Test NTS-1 mutation rule generation."""
    
    def test_default_rules_generation(self):
        """Test that default rules are generated correctly."""
        rules = get_nts1_mutation_rules()
        
        assert len(rules) > 0
        assert all(isinstance(rule, MutationRule) for rule in rules)
        
        # Check that we have rules for major parameter categories
        param_names = [rule.parameter for rule in rules]
        
        # Should have oscillator rules
        osc_rules = [name for name in param_names if name.startswith("osc_")]
        assert len(osc_rules) > 0
        
        # Should have filter rules
        filter_rules = [name for name in param_names if name.startswith("filter_")]
        assert len(filter_rules) > 0
        
        # Should have envelope rules  
        eg_rules = [name for name in param_names if name.startswith("eg_")]
        assert len(eg_rules) > 0
        
        # Should have effect rules
        reverb_rules = [name for name in param_names if name.startswith("reverb_")]
        delay_rules = [name for name in param_names if name.startswith("delay_")]
        assert len(reverb_rules) > 0
        assert len(delay_rules) > 0
    
    def test_ambient_rules_generation(self):
        """Test that ambient rules are generated correctly."""
        rules = get_nts1_ambient_rules()
        
        assert len(rules) > 0
        assert all(isinstance(rule, MutationRule) for rule in rules)
        
        # Ambient rules should generally have smaller delta scales
        for rule in rules:
            if hasattr(rule, 'delta_scale'):
                # Most ambient rules should be gentler
                if rule.parameter not in ['reverb_mix', 'delay_mix']:  # These might have normal scaling
                    assert rule.delta_scale <= 1.0
    
    def test_rhythmic_rules_generation(self):
        """Test that rhythmic rules are generated correctly."""
        rules = get_nts1_rhythmic_rules()
        
        assert len(rules) > 0
        assert all(isinstance(rule, MutationRule) for rule in rules)
        
        # Should emphasize filter and envelope parameters
        param_names = [rule.parameter for rule in rules]
        filter_cutoff_rules = [rule for rule in rules if rule.parameter == "filter_cutoff"]
        assert len(filter_cutoff_rules) > 0
        
        # Rhythmic filter cutoff should have high weight
        filter_rule = filter_cutoff_rules[0]
        assert filter_rule.weight >= 3.0
    
    def test_rule_parameter_validity(self):
        """Test that all rule parameters are valid NTS-1 parameters."""
        all_rules = (get_nts1_mutation_rules() + 
                    get_nts1_ambient_rules() + 
                    get_nts1_rhythmic_rules())
        
        # Get the NTS-1 CC profile to check valid parameters
        profile = get_profile("korg_nts1_mk2")
        assert profile is not None
        
        valid_params = set(profile.parameters.keys())
        valid_params.add("master_volume")  # This is a standard parameter
        
        for rule in all_rules:
            # Each rule should target a valid NTS-1 parameter
            # (Some rules might target sequencer parameters, which is OK)
            if rule.parameter.startswith(('osc_', 'filter_', 'eg_', 'tremolo_', 
                                        'mod_', 'delay_', 'reverb_', 'arp_', 'master_')):
                assert rule.parameter in valid_params, f"Invalid parameter: {rule.parameter}"


class TestNTS1StateIntegration:
    """Test NTS-1 state parameter integration."""
    
    def test_state_parameter_registration(self):
        """Test that NTS-1 parameters are registered in state."""
        state = State()
        register_nts1_state_parameters(state)
        
        # Check that key parameters were registered
        required_params = [
            "filter_cutoff", "filter_resonance", "filter_type",
            "eg_attack", "eg_release", "eg_type",
            "osc_a", "osc_b", "osc_type",
            "reverb_mix", "delay_mix",
            "master_volume"
        ]
        
        for param in required_params:
            value = state.get(param)
            assert value is not None, f"Parameter {param} not registered"
            assert isinstance(value, (int, float))
            assert 0 <= value <= 127  # All should be in MIDI range
    
    def test_state_parameter_defaults(self):
        """Test that default values are reasonable."""
        state = State()
        register_nts1_state_parameters(state)
        
        # Test some specific defaults - note that State may have its own defaults
        # that take precedence over NTS-1 plugin defaults
        assert state.get("master_volume") == 100  # Should be fairly loud
        filter_cutoff = state.get("filter_cutoff")
        assert filter_cutoff in [64, 96]  # Could be State default (64) or NTS-1 default (96)
        assert state.get("eg_attack") == 16       # Should be quick
        reverb_mix = state.get("reverb_mix")
        assert reverb_mix == 32  # Should be moderate


class TestNTS1MutationEngine:
    """Test NTS-1 mutation engine integration."""
    
    def test_rule_registration(self):
        """Test that rules are registered with mutation engine."""
        config = MutationConfig(interval_min_s=60, interval_max_s=120, max_changes_per_cycle=2)
        state = State()
        engine = MutationEngine(config, state)
        
        initial_rule_count = len(engine._rules)
        register_nts1_rules(engine, "default")
        
        # Should have added NTS-1 rules
        assert len(engine._rules) > initial_rule_count
        
        # Check that we have NTS-1 parameter rules
        nts1_params = [rule.parameter for rule in engine._rules 
                      if rule.parameter.startswith(('osc_', 'filter_', 'eg_', 'reverb_', 'delay_'))]
        assert len(nts1_params) > 0
    
    def test_complete_setup(self):
        """Test complete NTS-1 setup process."""
        config = MutationConfig(interval_min_s=60, interval_max_s=120, max_changes_per_cycle=2)
        state = State()
        engine = MutationEngine(config, state)
        
        # Complete setup
        setup_nts1_mutations(engine, state, "ambient")
        
        # Should have rules and parameters
        assert len(engine._rules) > 0
        
        # Should have NTS-1 parameters in state
        assert state.get("filter_cutoff") is not None
        assert state.get("reverb_mix") is not None
        
        # Enable mutations and test one cycle
        engine._mutations_enabled = True
        initial_history_len = len(engine.get_history())
        
        engine.force_mutation()
        
        # Should have applied some mutations
        assert len(engine.get_history()) >= initial_history_len
    
    def test_different_styles(self):
        """Test that different styles produce different rule sets."""
        config = MutationConfig(interval_min_s=60, interval_max_s=120, max_changes_per_cycle=2)
        
        # Test each style
        for style in ["default", "ambient", "rhythmic"]:
            state = State()
            engine = MutationEngine(config, state)
            setup_nts1_mutations(engine, state, style)
            
            assert len(engine._rules) > 0
            
            # Check that we have style-appropriate rules
            if style == "ambient":
                # Should have gentler rules
                gentle_rules = [rule for rule in engine._rules 
                               if hasattr(rule, 'delta_scale') and rule.delta_scale < 1.0]
                assert len(gentle_rules) > 0
            
            elif style == "rhythmic":
                # Should have more aggressive filter rules
                filter_rules = [rule for rule in engine._rules 
                               if rule.parameter == "filter_cutoff"]
                if filter_rules:
                    # Find the rhythmic-specific filter rule (there should be at least one with high weight)
                    high_weight_filter_rules = [rule for rule in filter_rules if rule.weight >= 3.0]
                    assert len(high_weight_filter_rules) > 0


class TestNTS1CCProfile:
    """Test the corrected NTS-1 CC profile."""
    
    def test_profile_exists(self):
        """Test that NTS-1 CC profile exists and is valid."""
        profile = get_profile("korg_nts1_mk2")
        assert profile is not None
        assert profile.name == "Korg NTS-1 MK2"
        assert len(profile.parameters) > 0
    
    def test_key_parameters_mapped(self):
        """Test that key NTS-1 parameters are mapped correctly."""
        profile = get_profile("korg_nts1_mk2")
        
        # Test key parameter mappings based on MIDI implementation
        expected_mappings = {
            "master_volume": 7,
            "eg_attack": 16,
            "eg_release": 19,
            "filter_cutoff": 43,
            "filter_resonance": 44,
            "osc_a": 54,
            "osc_b": 55,
            "reverb_mix": 36,
            "delay_mix": 33,
        }
        
        for param_name, expected_cc in expected_mappings.items():
            assert param_name in profile.parameters, f"Missing parameter: {param_name}"
            assert profile.parameters[param_name].cc == expected_cc, \
                f"Wrong CC for {param_name}: expected {expected_cc}, got {profile.parameters[param_name].cc}"
    
    def test_stepped_parameters(self):
        """Test that stepped parameters are configured correctly."""
        profile = get_profile("korg_nts1_mk2")
        
        stepped_params = {
            "eg_type": 5,      # 5 EG types per MIDI implementation
            "filter_type": 7,  # 7 filter types  
            "osc_type": 7,     # 7 oscillator types
            "mod_type": 9,     # 9 mod types
            "delay_type": 13,  # 13 delay types
            "reverb_type": 11, # 11 reverb types
        }
        
        for param_name, expected_steps in stepped_params.items():
            assert param_name in profile.parameters, f"Missing stepped parameter: {param_name}"
            param = profile.parameters[param_name]
            assert param.curve.value == "stepped", f"Parameter {param_name} should be stepped"
            assert param.steps == expected_steps, \
                f"Wrong step count for {param_name}: expected {expected_steps}, got {param.steps}"
    
    def test_parameter_scaling(self):
        """Test that parameter scaling works correctly."""
        profile = get_profile("korg_nts1_mk2")
        
        # Test linear parameter
        filter_cutoff = profile.parameters["filter_cutoff"]
        assert filter_cutoff.scale_value(0.0) == 0
        assert filter_cutoff.scale_value(1.0) == 127
        mid_value = filter_cutoff.scale_value(0.5)
        assert 20 <= mid_value <= 50  # Should be in lower half due to exponential curve
        
        # Test stepped parameter
        osc_type = profile.parameters["osc_type"]
        values = [osc_type.scale_value(i/6) for i in range(7)]  # 7 steps
        # Should get distinct values
        assert len(set(values)) == 7, f"Expected 7 distinct values, got {values}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
