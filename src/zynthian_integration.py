"""
Zynthian Integration Manager

This module integrates the Mystery Melody Machine with Zynthian v4 hardware,
providing physical control over key sequencer parameters.

Hardware Control Mapping:
- Encoder 0 (Layer): Sequencer steps (1-32) with select via button press
- Encoder 1 (Back): Scale selection with select via button press
- Encoder 2 (Select): Root note selection (C-B) with select via button press
- Encoder 3 (Learn): Direction pattern selection with select via button press
- Button S1: Select NTS-1 MK2 CC profile
- Button S2: Select Roland JX-08 CC profile
- Button S3: Select Waldorf Streichfett CC profile
- Button S4: Select Generic Analog CC profile

This allows real-time control of the sequencer without external MIDI controllers.
"""

import logging
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from state import State
    from sequencer import Sequencer
    from action_handler import ActionHandler
    from mutation import MutationEngine
    from idle import IdleManager
    from external_hardware import ExternalHardwareManager

try:
    from zynthian_hardware import (
        ZynthianHardwareInterface, ZynthianMidiInterface,
        ZynthianEncoder, ZynthianButton, EncoderEvent, ButtonEvent
    )
    ZYNTHIAN_AVAILABLE = True
except ImportError:
    ZYNTHIAN_AVAILABLE = False
    # Define dummy classes for type hints when hardware not available
    class ZynthianEncoder:
        pass
    class ZynthianButton:
        pass
    class EncoderEvent:
        pass
    class ButtonEvent:
        pass


@dataclass
class ZynthianConfig:
    """Configuration for Zynthian integration"""
    enabled: bool = True
    encoder_sensitivity: int = 1  # Steps per encoder click
    bpm_step: int = 5  # BPM change per encoder step
    min_bpm: int = 60
    max_bpm: int = 200
    display_updates: bool = True  # Enable display feedback


class ZynthianIntegrationManager:
    """
    Manages integration between Mystery Melody Machine and Zynthian v4 hardware.
    
    This class bridges the hardware controls to the sequencer's internal state
    and provides real-time feedback via the display.
    """
    
    def __init__(self, config: ZynthianConfig):
        self.log = logging.getLogger("zynthian_integration")
        self.config = config
        
        # Component references (injected)
        self.state: Optional['State'] = None
        self.sequencer: Optional['Sequencer'] = None  
        self.action_handler: Optional['ActionHandler'] = None
        self.mutation_engine: Optional['MutationEngine'] = None
        self.idle_manager: Optional['IdleManager'] = None
        self.external_hardware: Optional['ExternalHardwareManager'] = None
        
        # Hardware interfaces
        self.hw_interface: Optional[ZynthianHardwareInterface] = None
        self.midi_interface: Optional[ZynthianMidiInterface] = None
        
        # Available options for selection
        self.cc_profiles: List[str] = [
            "korg_nts1_mk2",
            "roland_jx08", 
            "waldorf_streichfett",
            "generic_analog"
        ]
        
        # Available scales (will be populated from sequencer)
        self.available_scales: List[str] = []
        
        # Available direction patterns
        self.direction_patterns: List[str] = [
            "forward",
            "backward", 
            "ping_pong",
            "random",
            "fugue",
            "song"
        ]
        
        # Root notes (C=0, C#=1, D=2, etc.)
        self.root_notes: List[Dict[str, Any]] = [
            {"name": "C", "midi": 60},
            {"name": "C#", "midi": 61},
            {"name": "D", "midi": 62},
            {"name": "D#", "midi": 63},
            {"name": "E", "midi": 64},
            {"name": "F", "midi": 65},
            {"name": "F#", "midi": 66},
            {"name": "G", "midi": 67},
            {"name": "G#", "midi": 68},
            {"name": "A", "midi": 69},
            {"name": "A#", "midi": 70},
            {"name": "B", "midi": 71}
        ]
        
        # Current selection indices (for browsing)
        self.current_steps_selection = 4  # 1-32, default to 4
        self.current_scale_selection = 0  # Index into available_scales
        self.current_root_selection = 0   # Index into root_notes (C)
        self.current_direction_selection = 0  # Index into direction_patterns
        
        if not ZYNTHIAN_AVAILABLE:
            self.log.warning("Zynthian hardware not available")
            return
        
        # Initialize hardware interfaces
        try:
            self.hw_interface = ZynthianHardwareInterface()
            self.midi_interface = ZynthianMidiInterface()
            
            # Set up event handlers
            if self.hw_interface:
                self.hw_interface.set_encoder_callback(self._handle_encoder_event)
                self.hw_interface.set_button_callback(self._handle_button_event)
                
            self.log.info("Zynthian integration manager initialized")
            
        except Exception as e:
            self.log.error(f"Failed to initialize Zynthian integration: {e}")
    
    def set_components(self, **components):
        """Inject component references"""
        for name, component in components.items():
            if hasattr(self, name):
                setattr(self, name, component)
                self.log.debug(f"Injected component: {name}")
    
    def start(self):
        """Start the Zynthian integration"""
        if not ZYNTHIAN_AVAILABLE or not self.hw_interface:
            self.log.warning("Cannot start Zynthian integration - hardware not available")
            return
        
        # Initialize current selections from state
        self._initialize_current_selections()
        
        self.hw_interface.start()
        self.log.info("Zynthian integration started")
        
        # Log current configuration
        self._log_current_state()
    
    def _initialize_current_selections(self):
        """Initialize current selection indices from sequencer state"""
        if not self.state:
            return
        
        # Get available scales from sequencer
        if hasattr(self.sequencer, 'available_scales'):
            self.available_scales = self.sequencer.available_scales
        else:
            # Default scales if not available
            self.available_scales = ["major", "minor", "pentatonic_major", "pentatonic_minor", 
                                   "dorian", "mixolydian", "blues", "chromatic"]
        
        # Initialize current selections from state
        current_state = self.state.get_all()
        
        # Steps (default 4, range 1-32)
        self.current_steps_selection = current_state.get('steps', 4)
        
        # Scale selection
        current_scale = current_state.get('scale', 'major')
        if current_scale in self.available_scales:
            self.current_scale_selection = self.available_scales.index(current_scale)
        
        # Root note selection  
        current_root = current_state.get('root_note', 60)  # Default C4
        # Find matching root note
        for i, note_info in enumerate(self.root_notes):
            if note_info['midi'] == current_root:
                self.current_root_selection = i
                break
        
        # Direction pattern selection
        current_direction = current_state.get('direction_pattern', 'forward')
        if current_direction in self.direction_patterns:
            self.current_direction_selection = self.direction_patterns.index(current_direction)
    
    def stop(self):
        """Stop the Zynthian integration"""
        if self.hw_interface:
            self.hw_interface.stop()
        self.log.info("Zynthian integration stopped")
    
    def get_recommended_midi_config(self) -> Dict[str, str]:
        """Get recommended MIDI configuration for Zynthian hardware"""
        if not self.midi_interface:
            return {"input_port": "auto", "output_port": "auto"}
        
        return self.midi_interface.get_recommended_ports()
    
    def _handle_encoder_event(self, event: EncoderEvent):
        """Handle encoder rotation and button press events"""
        if event.is_button:
            self._handle_encoder_button(event.encoder)
        else:
            self._handle_encoder_rotation(event.encoder, event.direction)
    
    def _handle_encoder_rotation(self, encoder: ZynthianEncoder, direction: int):
        """Handle encoder rotation events"""
        step = direction * self.config.encoder_sensitivity
        
        if encoder == ZynthianEncoder.LAYER:
            # Sequencer steps (1-32)
            self._adjust_steps_selection(step)
            
        elif encoder == ZynthianEncoder.BACK:
            # Scale selection
            self._adjust_scale_selection(step)
            
        elif encoder == ZynthianEncoder.SELECT:
            # Root note selection (C-B)
            self._adjust_root_selection(step)
            
        elif encoder == ZynthianEncoder.LEARN:
            # Direction pattern selection
            self._adjust_direction_selection(step)
    
    def _handle_encoder_button(self, encoder: ZynthianEncoder):
        """Handle encoder button press events"""
        if encoder == ZynthianEncoder.LAYER:
            # Apply selected steps value
            self._apply_steps_selection()
            
        elif encoder == ZynthianEncoder.BACK:
            # Apply selected scale
            self._apply_scale_selection()
            
        elif encoder == ZynthianEncoder.SELECT:
            # Apply selected root note
            self._apply_root_selection()
            
        elif encoder == ZynthianEncoder.LEARN:
            # Apply selected direction pattern
            self._apply_direction_selection()
    
    def _handle_button_event(self, event: ButtonEvent):
        """Handle button press events"""
        if not event.pressed:  # Only handle press, not release
            return
        
        if event.button == ZynthianButton.S1:
            # Select NTS-1 MK2 CC profile
            self._select_cc_profile("korg_nts1_mk2")
            
        elif event.button == ZynthianButton.S2:
            # Select Roland JX-08 CC profile
            self._select_cc_profile("roland_jx08")
            
        elif event.button == ZynthianButton.S3:
            # Select Waldorf Streichfett CC profile
            self._select_cc_profile("waldorf_streichfett")
            
        elif event.button == ZynthianButton.S4:
            # Select Generic Analog CC profile
            self._select_cc_profile("generic_analog")
    
    # Encoder 0: Steps (1-32)
    def _adjust_steps_selection(self, step: int):
        """Adjust selected steps value"""
        self.current_steps_selection = max(1, min(32, self.current_steps_selection + step))
        self.log.info(f"Steps selection: {self.current_steps_selection}")
    
    def _apply_steps_selection(self):
        """Apply the selected steps value to sequencer"""
        if not self.state:
            return
        
        self.state.set('steps', self.current_steps_selection, source='zynthian_hardware')
        self.log.info(f"Applied steps: {self.current_steps_selection}")
    
    # Encoder 1: Scale selection
    def _adjust_scale_selection(self, step: int):
        """Adjust selected scale"""
        if not self.available_scales:
            return
        
        self.current_scale_selection = (self.current_scale_selection + step) % len(self.available_scales)
        scale_name = self.available_scales[self.current_scale_selection]
        self.log.info(f"Scale selection: {scale_name}")
    
    def _apply_scale_selection(self):
        """Apply the selected scale to sequencer"""
        if not self.state or not self.available_scales:
            return
        
        scale_name = self.available_scales[self.current_scale_selection]
        self.state.set('scale', scale_name, source='zynthian_hardware')
        self.log.info(f"Applied scale: {scale_name}")
    
    # Encoder 2: Root note selection 
    def _adjust_root_selection(self, step: int):
        """Adjust selected root note"""
        self.current_root_selection = (self.current_root_selection + step) % len(self.root_notes)
        note_info = self.root_notes[self.current_root_selection]
        self.log.info(f"Root note selection: {note_info['name']} (MIDI {note_info['midi']})")
    
    def _apply_root_selection(self):
        """Apply the selected root note to sequencer"""
        if not self.state:
            return
        
        note_info = self.root_notes[self.current_root_selection]
        self.state.set('root_note', note_info['midi'], source='zynthian_hardware')
        self.log.info(f"Applied root note: {note_info['name']} (MIDI {note_info['midi']})")
    
    # Encoder 3: Direction pattern selection
    def _adjust_direction_selection(self, step: int):
        """Adjust selected direction pattern"""
        self.current_direction_selection = (self.current_direction_selection + step) % len(self.direction_patterns)
        pattern_name = self.direction_patterns[self.current_direction_selection]
        self.log.info(f"Direction pattern selection: {pattern_name}")
    
    def _apply_direction_selection(self):
        """Apply the selected direction pattern to sequencer"""
        if not self.sequencer:
            return
        
        pattern_name = self.direction_patterns[self.current_direction_selection]
        self.sequencer.set_direction_pattern(pattern_name)
        self.log.info(f"Applied direction pattern: {pattern_name}")
    
    # Button CC profile selection
    def _select_cc_profile(self, profile_name: str):
        """Select a specific CC profile"""
        if not self.external_hardware:
            self.log.warning("External hardware manager not available")
            return
        
        try:
            self.external_hardware.set_active_profile(profile_name)
            self.log.info(f"Selected CC profile: {profile_name}")
        except Exception as e:
            self.log.error(f"Failed to select CC profile {profile_name}: {e}")
    
    def _log_current_state(self):
        """Log current configuration state"""
        if not self.state:
            return
        
        current_state = self.state.get_all()
        self.log.info("=== ZYNTHIAN CONTROL STATE ===")
        self.log.info(f"Steps: {self.current_steps_selection} (applied: {current_state.get('steps', 'unknown')})")
        
        if self.available_scales and self.current_scale_selection < len(self.available_scales):
            current_scale_name = self.available_scales[self.current_scale_selection]
            self.log.info(f"Scale: {current_scale_name} (applied: {current_state.get('scale', 'unknown')})")
        
        current_root_note = self.root_notes[self.current_root_selection]
        self.log.info(f"Root Note: {current_root_note['name']} (applied: {current_state.get('root_note', 'unknown')})")
        
        current_direction = self.direction_patterns[self.current_direction_selection]
        self.log.info(f"Direction: {current_direction} (applied: {current_state.get('direction_pattern', 'unknown')})")
        
        if self.external_hardware:
            try:
                active_profile = self.external_hardware.get_active_profile_id()
                self.log.info(f"Active CC Profile: {active_profile}")
            except:
                self.log.info("CC Profile: unknown")
        
        self.log.info(f"Available CC Profiles: {self.cc_profiles}")
        self.log.info("=== END ZYNTHIAN STATE ===")


def create_zynthian_integration(config_dict: Dict[str, Any]) -> Optional[ZynthianIntegrationManager]:
    """
    Factory function to create Zynthian integration from configuration.
    
    Args:
        config_dict: Configuration dictionary
        
    Returns:
        ZynthianIntegrationManager instance or None if disabled/unavailable
    """
    # Check if Zynthian integration is enabled in config
    zynthian_config = config_dict.get('zynthian', {})
    if not zynthian_config.get('enabled', True):
        return None
    
    # Create configuration
    config = ZynthianConfig(
        enabled=zynthian_config.get('enabled', True),
        encoder_sensitivity=zynthian_config.get('encoder_sensitivity', 1),
        bpm_step=zynthian_config.get('bpm_step', 5),
        min_bpm=zynthian_config.get('min_bpm', 60),
        max_bpm=zynthian_config.get('max_bpm', 200),
        display_updates=zynthian_config.get('display_updates', True)
    )
    
    return ZynthianIntegrationManager(config)
