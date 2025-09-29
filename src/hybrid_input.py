"""Hybrid input manager for both HID and MIDI inputs."""

from __future__ import annotations
import logging
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

from midi_in import MidiInput
from hid_input import HidInput
from events import SemanticEvent

log = logging.getLogger(__name__)


@dataclass
class HybridInputConfig:
    """Configuration for hybrid input system."""
    # MIDI configuration (for Teensy potentiometers + switches)
    midi_port: str
    midi_channel: int
    
    # HID configuration (for arcade buttons + joystick)
    hid_device_name: str
    hid_button_mapping: Dict[int, str]  # button index -> semantic action
    hid_joystick_mapping: Dict[str, str]  # direction -> semantic action


class HybridInput:
    """Manages both HID and MIDI inputs, routing all events through a single callback."""
    
    def __init__(self, config: HybridInputConfig, router_callback: Callable):
        """
        Initialize hybrid input system.
        
        Args:
            config: Hybrid input configuration
            router_callback: Callback function that handles semantic events (from router)
        """
        self.config = config
        self.router_callback = router_callback
        
        # Input handlers
        self.midi_input: Optional[MidiInput] = None
        self.hid_input: Optional[HidInput] = None
        
    def start(self):
        """Start both HID and MIDI input systems."""
        log.info("Starting hybrid input system")
        
        # Start MIDI input for Teensy (potentiometers + switches)
        try:
            self.midi_input = MidiInput.create(self.config.midi_port, self._handle_midi_message)
            log.info("MIDI input started for Teensy controls")
        except Exception as e:
            log.error("Failed to start MIDI input: %s", e)
            raise
            
        # Start HID input for arcade buttons + joystick
        try:
            self.hid_input = HidInput(
                device_name=self.config.hid_device_name,
                button_mapping=self.config.hid_button_mapping,
                joystick_mapping=self.config.hid_joystick_mapping,
                callback=self._handle_hid_event
            )
            self.hid_input.start()
            log.info("HID input started for arcade controls")
        except Exception as e:
            log.error("Failed to start HID input: %s", e)
            # Don't raise here - allow system to continue with just MIDI
            
    def stop(self):
        """Stop both input systems."""
        log.info("Stopping hybrid input system")
        
        if self.hid_input:
            self.hid_input.stop()
            
        if self.midi_input:
            self.midi_input.close()
            
    def _handle_midi_message(self, msg):
        """Handle MIDI messages from Teensy and route them through the existing router."""
        # This gets routed through the existing router.route() method
        # The router will convert MIDI to SemanticEvent and call router_callback
        self.router_callback(msg)
        
    def _handle_hid_event(self, event: SemanticEvent):
        """Handle HID events directly as SemanticEvents."""
        # HID events are already SemanticEvents, so we can handle them directly
        # This bypasses the router since we've already done the HID->semantic conversion
        log.info("hybrid_hid_event %s", event.log_str())
        
        # We need to call the action handler directly here since we're bypassing the router
        # We'll pass this to the main loop to handle
        self._handle_semantic_event(event)
        
    def set_semantic_handler(self, handler: Callable[[SemanticEvent], None]):
        """Set the semantic event handler (action_handler.handle_semantic_event)."""
        self._handle_semantic_event = handler
        
    @staticmethod
    def create_from_config(cfg, router_callback: Callable, semantic_handler: Callable[[SemanticEvent], None]) -> 'HybridInput':
        """Create HybridInput from main config with default HID mappings."""
        
        # Extract HID configuration from config
        hid_config = getattr(cfg, 'hid', None)
        if not hid_config:
            # Use defaults for backward compatibility
            hid_device_name = "Generic USB Joystick"
            hid_button_mapping = {i: "trigger_step" for i in range(10)}  # 10 arcade buttons
            hid_joystick_mapping = {
                "up": "osc_a",
                "down": "osc_b", 
                "left": "mod_a",
                "right": "mod_b"
            }
        else:
            hid_device_name = hid_config.device_name
            hid_button_mapping = hid_config.button_mapping
            hid_joystick_mapping = hid_config.joystick_mapping
            
        hybrid_config = HybridInputConfig(
            midi_port=cfg.midi.input_port,
            midi_channel=cfg.midi.input_channel,
            hid_device_name=hid_device_name,
            hid_button_mapping=hid_button_mapping,
            hid_joystick_mapping=hid_joystick_mapping
        )
        
        hybrid = HybridInput(hybrid_config, router_callback)
        hybrid.set_semantic_handler(semantic_handler)
        return hybrid
