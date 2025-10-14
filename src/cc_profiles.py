"""CC Profile system for external hardware synths.

Phase 7: Provides configurable CC mappings for different synthesizer models.
Includes built-in profiles for common devices and custom profile support.
"""

from __future__ import annotations
from typing import Dict, Optional, Tuple, Literal, Any
from dataclasses import dataclass
from enum import Enum
import math
import logging

log = logging.getLogger(__name__)


class CurveType(str, Enum):
    """Parameter curve types for value scaling."""
    LINEAR = "linear"
    EXPONENTIAL = "exponential" 
    LOGARITHMIC = "logarithmic"
    STEPPED = "stepped"


@dataclass
class CCParameter:
    """Definition of a single CC parameter mapping."""
    cc: int                                    # MIDI CC number (0-127)
    range: Tuple[int, int] = (0, 127)         # Value range (min, max)
    curve: CurveType = CurveType.LINEAR       # Scaling curve
    steps: Optional[int] = None               # Number of steps for stepped parameters
    name: Optional[str] = None                # Human readable name
    
    def __post_init__(self):
        # Validate CC number
        if not 0 <= self.cc <= 127:
            raise ValueError(f"CC number must be 0-127, got {self.cc}")
        
        # Validate range
        if not (0 <= self.range[0] <= 127 and 0 <= self.range[1] <= 127):
            raise ValueError(f"CC range values must be 0-127, got {self.range}")
        
        if self.range[0] > self.range[1]:
            raise ValueError(f"CC range min must be <= max, got {self.range}")
        
        # Validate steps for stepped parameters
        if self.curve == CurveType.STEPPED:
            if self.steps is None or self.steps < 2:
                raise ValueError("Stepped parameters must specify steps >= 2")
    
    def scale_value(self, value: float) -> int:
        """Scale a 0.0-1.0 value to the CC range using the specified curve.
        
        Args:
            value: Input value in range 0.0-1.0
            
        Returns:
            Scaled CC value in the parameter's range
        """
        # Clamp input to valid range
        value = max(0.0, min(1.0, value))
        
        # Apply curve transformation
        if self.curve == CurveType.LINEAR:
            scaled = value
        elif self.curve == CurveType.EXPONENTIAL:
            # Exponential curve: y = x^2 for smoother control at low values
            scaled = value ** 2
        elif self.curve == CurveType.LOGARITHMIC:
            # Logarithmic curve: more precision at high values
            scaled = math.log10(value * 9 + 1)  # Maps 0-1 to 0-1 via log10(1) to log10(10)
        elif self.curve == CurveType.STEPPED:
            # Stepped/discrete values
            if self.steps:
                step_value = int(value * (self.steps - 1))
                scaled = step_value / (self.steps - 1)
            else:
                scaled = value
        else:
            scaled = value
        
        # Map to CC range
        range_span = self.range[1] - self.range[0]
        cc_value = int(self.range[0] + scaled * range_span)
        
        # Ensure within bounds
        return max(self.range[0], min(self.range[1], cc_value))


@dataclass 
class CCProfile:
    """Complete CC profile for a synthesizer model."""
    name: str
    description: Optional[str] = None
    parameters: Dict[str, CCParameter] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
    
    def map_parameter(self, param_name: str, value: float) -> Optional[Tuple[int, int]]:
        """Map a parameter name and 0.0-1.0 value to (CC_number, CC_value).
        
        Args:
            param_name: Name of the parameter to map
            value: Input value in range 0.0-1.0
            
        Returns:
            Tuple of (CC_number, CC_value) if parameter exists, None otherwise
        """
        if param_name not in self.parameters:
            log.warning(f"Parameter '{param_name}' not found in profile '{self.name}'")
            return None
        
        param = self.parameters[param_name]
        cc_value = param.scale_value(value)
        return (param.cc, cc_value)
    
    def get_parameter_names(self) -> list[str]:
        """Get list of available parameter names."""
        return list(self.parameters.keys())
    
    def has_parameter(self, param_name: str) -> bool:
        """Check if parameter exists in this profile."""
        return param_name in self.parameters


class CCProfileRegistry:
    """Registry for managing CC profiles."""
    
    def __init__(self):
        self.profiles: Dict[str, CCProfile] = {}
        self._load_builtin_profiles()
    
    def register_profile(self, profile_id: str, profile: CCProfile) -> None:
        """Register a CC profile."""
        self.profiles[profile_id] = profile
        log.info(f"Registered CC profile: {profile_id} ({profile.name})")
    
    def get_profile(self, profile_id: str) -> Optional[CCProfile]:
        """Get a CC profile by ID."""
        return self.profiles.get(profile_id)
    
    def list_profiles(self) -> Dict[str, str]:
        """Get dictionary of profile_id -> profile_name."""
        return {pid: profile.name for pid, profile in self.profiles.items()}
    
    def _load_builtin_profiles(self) -> None:
        """Load built-in CC profiles for common devices."""
        
        # Korg NTS-1 MK2 - Complete parameter mapping based on official MIDI implementation
        korg_nts1_mk2 = CCProfile(
            name="Korg NTS-1 MK2",
            description="Complete parameter mapping for Korg NTS-1 MK2 digital synthesizer (corrected per official MIDI implementation)",
            parameters={
                # Master Volume
                "master_volume": CCParameter(cc=7, range=(0, 127), curve=CurveType.LINEAR, name="Master Volume"),
                
                # Envelope Generator
                "eg_type": CCParameter(cc=14, range=(0, 127), curve=CurveType.STEPPED, steps=5, name="EG Type"),
                "eg_attack": CCParameter(cc=16, range=(0, 127), curve=CurveType.EXPONENTIAL, name="EG Attack"),
                "eg_release": CCParameter(cc=19, range=(0, 127), curve=CurveType.EXPONENTIAL, name="EG Release"),
                
                # Tremolo
                "tremolo_depth": CCParameter(cc=20, range=(0, 127), curve=CurveType.LINEAR, name="Tremolo Depth"),
                "tremolo_rate": CCParameter(cc=21, range=(0, 127), curve=CurveType.LOGARITHMIC, name="Tremolo Rate"),
                
                # Oscillator LFO
                "osc_lfo_rate": CCParameter(cc=24, range=(0, 127), curve=CurveType.LOGARITHMIC, name="OSC LFO Rate"),
                "osc_lfo_depth": CCParameter(cc=26, range=(0, 127), curve=CurveType.LINEAR, name="OSC LFO Depth"),
                
                # Modulation Effects
                "mod_a": CCParameter(cc=28, range=(0, 127), curve=CurveType.LINEAR, name="MOD A"),
                "mod_b": CCParameter(cc=29, range=(0, 127), curve=CurveType.LINEAR, name="MOD B"),
                
                # Delay Effects
                "delay_a": CCParameter(cc=30, range=(0, 127), curve=CurveType.LINEAR, name="DELAY A"),
                "delay_b": CCParameter(cc=31, range=(0, 127), curve=CurveType.LINEAR, name="DELAY B"),
                "delay_mix": CCParameter(cc=33, range=(0, 127), curve=CurveType.LINEAR, name="DELAY MIX"),
                
                # Reverb Effects
                "reverb_a": CCParameter(cc=34, range=(0, 127), curve=CurveType.LINEAR, name="REVERB A"),
                "reverb_b": CCParameter(cc=35, range=(0, 127), curve=CurveType.LINEAR, name="REVERB B"),
                "reverb_mix": CCParameter(cc=36, range=(0, 127), curve=CurveType.LINEAR, name="REVERB MIX"),
                
                # Filter Section
                "filter_type": CCParameter(cc=42, range=(0, 127), curve=CurveType.STEPPED, steps=7, name="Filter Type"),
                "filter_cutoff": CCParameter(cc=43, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Filter Cutoff"),
                "filter_resonance": CCParameter(cc=44, range=(0, 127), curve=CurveType.LINEAR, name="Filter Resonance"),
                "filter_sweep_depth": CCParameter(cc=45, range=(0, 127), curve=CurveType.LINEAR, name="Filter Sweep Depth"),
                "filter_sweep_rate": CCParameter(cc=46, range=(0, 127), curve=CurveType.LOGARITHMIC, name="Filter Sweep Rate"),
                
                # Oscillator Section  
                "osc_type": CCParameter(cc=53, range=(0, 127), curve=CurveType.STEPPED, steps=7, name="OSC Type"),
                "osc_a": CCParameter(cc=54, range=(0, 127), curve=CurveType.LINEAR, name="OSC A"),
                "osc_b": CCParameter(cc=55, range=(0, 127), curve=CurveType.LINEAR, name="OSC B"),
                
                # Effect Types (stepped parameters with specific values)
                "mod_type": CCParameter(cc=88, range=(0, 127), curve=CurveType.STEPPED, steps=9, name="MOD Type"),
                "delay_type": CCParameter(cc=89, range=(0, 127), curve=CurveType.STEPPED, steps=13, name="DELAY Type"),
                "reverb_type": CCParameter(cc=90, range=(0, 127), curve=CurveType.STEPPED, steps=11, name="REVERB Type"),
                
                # Arpeggiator
                "arp_pattern": CCParameter(cc=117, range=(0, 127), curve=CurveType.STEPPED, steps=10, name="ARP Pattern"),
                "arp_intervals": CCParameter(cc=118, range=(0, 127), curve=CurveType.STEPPED, steps=6, name="ARP Intervals"),
                "arp_length": CCParameter(cc=119, range=(0, 127), curve=CurveType.LINEAR, name="ARP Length"),
                
                # Standard MIDI
                "sustain_pedal": CCParameter(cc=64, range=(0, 127), curve=CurveType.STEPPED, steps=2, name="Sustain Pedal"),
            }
        )
        self.register_profile("korg_nts1_mk2", korg_nts1_mk2)
        
        # Generic Analog Synth - Standard subtractive synthesis
        generic_analog = CCProfile(
            name="Generic Analog Synth",
            description="Standard analog subtractive synthesis parameters",
            parameters={
                # Filter
                "filter_cutoff": CCParameter(cc=74, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Filter Cutoff"),
                "filter_resonance": CCParameter(cc=71, range=(0, 127), curve=CurveType.LINEAR, name="Filter Resonance"),
                
                # Envelope
                "envelope_attack": CCParameter(cc=73, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Envelope Attack"),
                "envelope_decay": CCParameter(cc=75, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Envelope Decay"),
                "envelope_sustain": CCParameter(cc=70, range=(0, 127), curve=CurveType.LINEAR, name="Envelope Sustain"),
                "envelope_release": CCParameter(cc=72, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Envelope Release"),
                
                # LFO
                "lfo_rate": CCParameter(cc=76, range=(0, 127), curve=CurveType.LOGARITHMIC, name="LFO Rate"),
                "lfo_amount": CCParameter(cc=77, range=(0, 127), curve=CurveType.LINEAR, name="LFO Amount"),
                
                # Oscillator
                "osc_detune": CCParameter(cc=78, range=(0, 127), curve=CurveType.LINEAR, name="Oscillator Detune"),
                "pulse_width": CCParameter(cc=79, range=(0, 127), curve=CurveType.LINEAR, name="Pulse Width"),
                
                # Master
                "master_volume": CCParameter(cc=7, range=(0, 127), curve=CurveType.LINEAR, name="Master Volume"),
                "sustain_pedal": CCParameter(cc=64, range=(0, 127), curve=CurveType.STEPPED, steps=2, name="Sustain Pedal"),
            }
        )
        self.register_profile("generic_analog", generic_analog)
        
        # FM Synth - Operator-based synthesis
        fm_synth = CCProfile(
            name="FM Synthesizer",
            description="FM synthesis with operator controls",
            parameters={
                # Operator 1
                "op1_ratio": CCParameter(cc=20, range=(0, 127), curve=CurveType.STEPPED, steps=32, name="Op1 Ratio"),
                "op1_level": CCParameter(cc=21, range=(0, 127), curve=CurveType.LINEAR, name="Op1 Level"),
                "op1_attack": CCParameter(cc=22, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Op1 Attack"),
                "op1_decay": CCParameter(cc=23, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Op1 Decay"),
                
                # Operator 2  
                "op2_ratio": CCParameter(cc=24, range=(0, 127), curve=CurveType.STEPPED, steps=32, name="Op2 Ratio"),
                "op2_level": CCParameter(cc=25, range=(0, 127), curve=CurveType.LINEAR, name="Op2 Level"),
                "op2_attack": CCParameter(cc=26, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Op2 Attack"),
                "op2_decay": CCParameter(cc=27, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Op2 Decay"),
                
                # Modulation
                "mod_index": CCParameter(cc=28, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Modulation Index"),
                "feedback": CCParameter(cc=29, range=(0, 127), curve=CurveType.LINEAR, name="Feedback"),
                
                # Global
                "master_volume": CCParameter(cc=7, range=(0, 127), curve=CurveType.LINEAR, name="Master Volume"),
                "sustain_pedal": CCParameter(cc=64, range=(0, 127), curve=CurveType.STEPPED, steps=2, name="Sustain Pedal"),
            }
        )
        self.register_profile("fm_synth", fm_synth)
        
        # Waldorf Streichfett - Dual engine string synthesizer
        waldorf_streichfett = CCProfile(
            name="Waldorf Streichfett",
            description="Dual engine string synthesizer with string, solo, and effects sections",
            parameters={
                # String Engine
                "string_registration": CCParameter(cc=70, range=(0, 2), curve=CurveType.STEPPED, steps=3, name="String Registration"),
                "string_octaves": CCParameter(cc=71, range=(0, 127), curve=CurveType.LINEAR, name="String Octaves"),
                "string_release": CCParameter(cc=72, range=(0, 127), curve=CurveType.EXPONENTIAL, name="String Release"),
                "string_crescendo": CCParameter(cc=73, range=(0, 127), curve=CurveType.LINEAR, name="String Crescendo"),
                "string_ensemble": CCParameter(cc=74, range=(0, 127), curve=CurveType.LINEAR, name="String Ensemble"),
                "string_ensemble_type": CCParameter(cc=75, range=(0, 2), curve=CurveType.STEPPED, steps=3, name="String Ensemble Type"),
                
                # Solo Engine
                "solo_tone": CCParameter(cc=76, range=(0, 127), curve=CurveType.LINEAR, name="Solo Tone"),
                "solo_tremolo": CCParameter(cc=77, range=(0, 127), curve=CurveType.LINEAR, name="Solo Tremolo"),
                "solo_split": CCParameter(cc=78, range=(0, 2), curve=CurveType.STEPPED, steps=3, name="Solo Split"),
                "solo_sustain": CCParameter(cc=79, range=(0, 1), curve=CurveType.STEPPED, steps=2, name="Solo Sustain"),
                "solo_attack": CCParameter(cc=80, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Solo Attack"),
                "solo_decay": CCParameter(cc=81, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Solo Decay"),
                
                # Mix
                "balance": CCParameter(cc=82, range=(0, 127), curve=CurveType.LINEAR, name="String/Solo Balance"),
                
                # Effects
                "fx_type": CCParameter(cc=91, range=(0, 2), curve=CurveType.STEPPED, steps=3, name="FX Type"),
                "fx_animate_amount": CCParameter(cc=92, range=(0, 127), curve=CurveType.LINEAR, name="FX Animate Amount"),
                "fx_phaser_amount": CCParameter(cc=93, range=(0, 127), curve=CurveType.LINEAR, name="FX Phaser Amount"),
                "fx_reverb_amount": CCParameter(cc=94, range=(0, 127), curve=CurveType.LINEAR, name="FX Reverb Amount"),
                
                # Standard MIDI
                "sustain_pedal": CCParameter(cc=64, range=(0, 127), curve=CurveType.STEPPED, steps=2, name="Sustain Pedal"),
            }
        )
        self.register_profile("waldorf_streichfett", waldorf_streichfett)

        # Roland JX-08 - Virtual analog boutique synth
        roland_jx08 = CCProfile(
            name="Roland JX-08",
            description="Roland JX-08 virtual analog boutique synthesizer with dual DCO, VCF, and dual envelope sections",
            parameters={
                # Standard MIDI Controls
                "modulation_wheel": CCParameter(cc=1, range=(0, 127), curve=CurveType.LINEAR, name="Modulation Wheel"),
                # "portamento_time": CCParameter(cc=5, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Portamento Time"),
                # "portamento_time_alt": CCParameter(cc=117, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Portamento Time Alt"),
                "hold_pedal": CCParameter(cc=64, range=(0, 127), curve=CurveType.STEPPED, steps=2, name="Hold Pedal"),
                "reverb_send": CCParameter(cc=91, range=(0, 127), curve=CurveType.LINEAR, name="Reverb Send Level"),
                
                # VCF (Filter) Section
                "vcf_cutoff": CCParameter(cc=3, range=(0, 127), curve=CurveType.EXPONENTIAL, name="VCF Cutoff"),
                "vcf_resonance": CCParameter(cc=9, range=(0, 127), curve=CurveType.LINEAR, name="VCF Resonance"),
                "vcf_envelope": CCParameter(cc=81, range=(0, 127), curve=CurveType.LINEAR, name="VCF Envelope Amount"),
                "vcf_key_follow": CCParameter(cc=82, range=(0, 127), curve=CurveType.LINEAR, name="VCF Key Follow"),
                "vcf_lfo_depth": CCParameter(cc=28, range=(0, 127), curve=CurveType.LINEAR, name="VCF LFO Depth"),
                "filter_hpf": CCParameter(cc=79, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Filter HPF"),
                
                # DCO (Oscillator) Section
                "dco1_range": CCParameter(cc=20, range=(0, 127), curve=CurveType.STEPPED, steps=8, name="DCO-1 Range"),
                # "dco1_range_alt": CCParameter(cc=47, range=(0, 127), curve=CurveType.STEPPED, steps=8, name="DCO-1 Range Alt"),
                "dco1_waveform": CCParameter(cc=46, range=(0, 127), curve=CurveType.STEPPED, steps=4, name="DCO-1 Waveform"),
                "dco1_lfo": CCParameter(cc=26, range=(0, 127), curve=CurveType.LINEAR, name="DCO-1 LFO Amount"),
                "dco_envelope_mode": CCParameter(cc=60, range=(0, 127), curve=CurveType.STEPPED, steps=3, name="DCO Envelope Mode"),
                
                "dco2_waveform": CCParameter(cc=61, range=(0, 127), curve=CurveType.STEPPED, steps=4, name="DCO-2 Waveform"),
                # "dco2_range": CCParameter(cc=62, range=(0, 127), curve=CurveType.STEPPED, steps=8, name="DCO-2 Range"),
                "dco2_lfo": CCParameter(cc=25, range=(0, 127), curve=CurveType.LINEAR, name="DCO-2 LFO Amount"),
                "dco2_envelope": CCParameter(cc=63, range=(0, 127), curve=CurveType.LINEAR, name="DCO-2 Envelope Amount"),
                
                # LFO Section
                "lfo_rate": CCParameter(cc=29, range=(0, 127), curve=CurveType.LOGARITHMIC, name="LFO Rate"),
                "lfo_waveform": CCParameter(cc=35, range=(0, 127), curve=CurveType.STEPPED, steps=6, name="LFO Waveform"),
                
                # Envelope 1 (Primary)
                "envelope1_attack": CCParameter(cc=83, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Envelope 1 Attack"),
                "envelope1_decay": CCParameter(cc=80, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Envelope 1 Decay"),
                "envelope1_sustain": CCParameter(cc=85, range=(0, 127), curve=CurveType.LINEAR, name="Envelope 1 Sustain"),
                "envelope1_release": CCParameter(cc=86, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Envelope 1 Release"),
                "envelope1_key_follow": CCParameter(cc=104, range=(0, 127), curve=CurveType.LINEAR, name="Envelope 1 Key Follow"),
                
                # Envelope 2 (Secondary)
                "envelope2_attack": CCParameter(cc=89, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Envelope 2 Attack"),
                "envelope2_decay": CCParameter(cc=90, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Envelope 2 Decay"),
                "envelope2_sustain": CCParameter(cc=102, range=(0, 127), curve=CurveType.LINEAR, name="Envelope 2 Sustain"),
                "envelope2_release": CCParameter(cc=103, range=(0, 127), curve=CurveType.EXPONENTIAL, name="Envelope 2 Release"),
                "envelope2_key_follow": CCParameter(cc=105, range=(0, 127), curve=CurveType.LINEAR, name="Envelope 2 Key Follow"),
                
                # Amplifier Section
                # "amp_envelope_mode": CCParameter(cc=109, range=(0, 127), curve=CurveType.STEPPED, steps=3, name="Amp Envelope Mode"),
                # "amp_level": CCParameter(cc=110, range=(0, 127), curve=CurveType.LINEAR, name="Amp Level"),
                
                # Performance Controls
                "bend_pitch": CCParameter(cc=41, range=(0, 127), curve=CurveType.LINEAR, name="Pitch Bend Range"),
                "portamento_switch": CCParameter(cc=118, range=(0, 127), curve=CurveType.STEPPED, steps=2, name="Portamento Switch"),
                "solo_poly_unison": CCParameter(cc=119, range=(0, 127), curve=CurveType.STEPPED, steps=3, name="Solo/Poly/Unison Mode"),
            }
        )
        self.register_profile("roland_jx08", roland_jx08)


# Global registry instance
cc_registry = CCProfileRegistry()


def load_custom_profiles(config_data: Dict[str, Any]) -> None:
    """Load custom CC profiles from configuration data.
    
    Args:
        config_data: Dictionary containing CC profile definitions
    """
    if "cc_profiles" not in config_data:
        return
    
    for profile_id, profile_config in config_data["cc_profiles"].items():
        try:
            # Skip built-in profiles
            if profile_id in ["korg_nts1_mk2", "generic_analog", "fm_synth"]:
                log.info(f"Skipping built-in profile override: {profile_id}")
                continue
            
            # Create parameters
            parameters = {}
            if "parameters" in profile_config:
                for param_name, param_config in profile_config["parameters"].items():
                    cc = param_config["cc"]
                    range_val = param_config.get("range", [0, 127])
                    curve = CurveType(param_config.get("curve", "linear"))
                    steps = param_config.get("steps")
                    name = param_config.get("name", param_name)
                    
                    parameters[param_name] = CCParameter(
                        cc=cc,
                        range=(range_val[0], range_val[1]),
                        curve=curve,
                        steps=steps,
                        name=name
                    )
            
            # Create profile
            profile = CCProfile(
                name=profile_config.get("name", profile_id),
                description=profile_config.get("description"),
                parameters=parameters
            )
            
            cc_registry.register_profile(profile_id, profile)
            
        except Exception as e:
            log.error(f"Failed to load custom CC profile '{profile_id}': {e}")


def get_profile(profile_id: str) -> Optional[CCProfile]:
    """Get a CC profile by ID."""
    return cc_registry.get_profile(profile_id)


def list_available_profiles() -> Dict[str, str]:
    """Get list of available CC profiles."""
    return cc_registry.list_profiles()
