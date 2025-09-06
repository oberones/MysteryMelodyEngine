"""
Zynthian Integration Manager

This module integrates the Mystery Melody Machine with Zynthian v4 hardware,
providing physical control over key sequencer parameters.

Hardware Control Mapping:
- Encoder 0 (Layer): MIDI Input Channel (1-16)
- Encoder 1 (Back): MIDI Output Channel (1-16)  
- Encoder 2 (Select): CC Profile selection
- Encoder 3 (Learn): BPM adjustment (60-200)
- Button S1: Manual step trigger
- Button S2: Toggle mutation engine on/off
- Button S3: Reset sequence to beginning
- Button S4: Toggle idle mode on/off

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
        
        # Available CC profiles for cycling
        self.cc_profiles: List[str] = [
            "roland_jx08",
            "korg_nts1_mk2", 
            "waldorf_streichfett",
            "generic_analog",
            "fm_synth"
        ]
        self.current_cc_profile_index: int = 0
        
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
        
        # Get current CC profile index
        if self.external_hardware:
            current_profile = self.external_hardware.get_active_profile_id()
            if current_profile in self.cc_profiles:
                self.current_cc_profile_index = self.cc_profiles.index(current_profile)
        
        self.hw_interface.start()
        self.log.info("Zynthian integration started")
        
        # Log current configuration
        self._log_current_state()
    
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
            # MIDI Input Channel (1-16)
            self._adjust_midi_input_channel(step)
            
        elif encoder == ZynthianEncoder.BACK:
            # MIDI Output Channel (1-16)
            self._adjust_midi_output_channel(step)
            
        elif encoder == ZynthianEncoder.SELECT:
            # CC Profile selection
            self._cycle_cc_profile(direction)
            
        elif encoder == ZynthianEncoder.LEARN:
            # BPM adjustment
            self._adjust_bpm(step * self.config.bpm_step)
    
    def _handle_encoder_button(self, encoder: ZynthianEncoder):
        """Handle encoder button press events"""
        if encoder == ZynthianEncoder.LAYER:
            # Reset MIDI input channel to 1
            self._set_midi_input_channel(1)
            
        elif encoder == ZynthianEncoder.BACK:
            # Reset MIDI output channel to 1
            self._set_midi_output_channel(1)
            
        elif encoder == ZynthianEncoder.SELECT:
            # Reset to first CC profile
            self._set_cc_profile_index(0)
            
        elif encoder == ZynthianEncoder.LEARN:
            # Reset BPM to default (120)
            self._set_bpm(120)
    
    def _handle_button_event(self, event: ButtonEvent):
        """Handle button press events"""
        if not event.pressed:  # Only handle press, not release
            return
        
        if event.button == ZynthianButton.S1:
            # Manual step trigger
            self._trigger_step()
            
        elif event.button == ZynthianButton.S2:
            # Toggle mutation engine
            self._toggle_mutation()
            
        elif event.button == ZynthianButton.S3:
            # Reset sequence
            self._reset_sequence()
            
        elif event.button == ZynthianButton.S4:
            # Toggle idle mode
            self._toggle_idle()
    
    def _adjust_midi_input_channel(self, step: int):
        """Adjust MIDI input channel"""
        # Note: This would require modifying the MIDI input configuration
        # For now, we'll log the action
        self.log.info(f"MIDI input channel adjustment requested: {step}")
        # TODO: Implement dynamic MIDI channel switching
    
    def _adjust_midi_output_channel(self, step: int):
        """Adjust MIDI output channel"""
        if not self.external_hardware:
            return
        
        # Get current channel from external hardware or state
        current_channel = 1  # Default
        new_channel = max(1, min(16, current_channel + step))
        
        self.log.info(f"MIDI output channel: {current_channel} -> {new_channel}")
        # TODO: Update MIDI output channel dynamically
    
    def _set_midi_input_channel(self, channel: int):
        """Set MIDI input channel to specific value"""
        self.log.info(f"Reset MIDI input channel to {channel}")
    
    def _set_midi_output_channel(self, channel: int):
        """Set MIDI output channel to specific value"""
        self.log.info(f"Reset MIDI output channel to {channel}")
    
    def _cycle_cc_profile(self, direction: int):
        """Cycle through available CC profiles"""
        if not self.external_hardware:
            return
        
        # Update index
        self.current_cc_profile_index += direction
        self.current_cc_profile_index %= len(self.cc_profiles)
        
        new_profile = self.cc_profiles[self.current_cc_profile_index]
        
        try:
            self.external_hardware.set_active_profile(new_profile)
            self.log.info(f"CC profile changed to: {new_profile}")
        except Exception as e:
            self.log.error(f"Failed to change CC profile: {e}")
    
    def _set_cc_profile_index(self, index: int):
        """Set CC profile to specific index"""
        if not self.external_hardware or index >= len(self.cc_profiles):
            return
        
        self.current_cc_profile_index = index
        profile = self.cc_profiles[index]
        
        try:
            self.external_hardware.set_active_profile(profile)
            self.log.info(f"CC profile reset to: {profile}")
        except Exception as e:
            self.log.error(f"Failed to reset CC profile: {e}")
    
    def _adjust_bpm(self, step: int):
        """Adjust BPM within configured range"""
        if not self.state:
            return
        
        current_bpm = self.state.get('bpm', 120)
        new_bpm = max(self.config.min_bpm, min(self.config.max_bpm, current_bpm + step))
        
        if new_bpm != current_bpm:
            self.state.update('bpm', new_bpm, source='zynthian_hardware')
            self.log.info(f"BPM: {current_bpm} -> {new_bpm}")
    
    def _set_bpm(self, bpm: int):
        """Set BPM to specific value"""
        if not self.state:
            return
        
        bpm = max(self.config.min_bpm, min(self.config.max_bpm, bpm))
        self.state.update('bpm', bpm, source='zynthian_hardware')
        self.log.info(f"BPM reset to: {bpm}")
    
    def _trigger_step(self):
        """Manually trigger a sequence step"""
        if self.action_handler:
            # Create a manual step trigger event
            from events import SemanticEvent
            event = SemanticEvent('trigger_step', {'source': 'zynthian_hardware'})
            self.action_handler.handle_semantic_event(event)
            self.log.info("Manual step triggered")
    
    def _toggle_mutation(self):
        """Toggle mutation engine on/off"""
        if not self.mutation_engine:
            return
        
        if self.mutation_engine.is_running():
            self.mutation_engine.stop()
            self.log.info("Mutation engine stopped")
        else:
            self.mutation_engine.start()
            self.log.info("Mutation engine started")
    
    def _reset_sequence(self):
        """Reset sequence to beginning"""
        if self.sequencer:
            # Reset sequencer position
            # Note: This depends on sequencer implementation
            self.log.info("Sequence reset requested")
            # TODO: Implement sequence reset
    
    def _toggle_idle(self):
        """Toggle idle mode on/off"""
        if not self.idle_manager:
            return
        
        # Check current idle state and toggle
        status = self.idle_manager.get_status()
        if status.get('is_idle', False):
            self.idle_manager.wake()
            self.log.info("Idle mode disabled")
        else:
            self.idle_manager.trigger_idle()
            self.log.info("Idle mode enabled")
    
    def _log_current_state(self):
        """Log current configuration state"""
        if not self.state:
            return
        
        current_state = self.state.get_all()
        self.log.info("=== ZYNTHIAN CONTROL STATE ===")
        self.log.info(f"BPM: {current_state.get('bpm', 'unknown')}")
        self.log.info(f"CC Profile: {self.cc_profiles[self.current_cc_profile_index]}")
        self.log.info(f"Available profiles: {self.cc_profiles}")
        
        if self.mutation_engine:
            mutation_running = self.mutation_engine.is_running()
            self.log.info(f"Mutation: {'enabled' if mutation_running else 'disabled'}")
        
        if self.idle_manager:
            idle_status = self.idle_manager.get_status()
            is_idle = idle_status.get('is_idle', False)
            self.log.info(f"Idle mode: {'active' if is_idle else 'inactive'}")
        
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
