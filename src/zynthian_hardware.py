"""
Zynthian v4 Hardware Interface

This module provides direct access to Zynthian v4 hardware components:
- 4 rotary encoders with push buttons
- 4 additional push buttons
- TFT display (optional)
- Built-in MIDI DIN connectors

Hardware mapping for Zynthian v4:
- Encoder 0 (Layer): GPIO pins for rotation + button
- Encoder 1 (Back): GPIO pins for rotation + button  
- Encoder 2 (Select): GPIO pins for rotation + button
- Encoder 3 (Learn): GPIO pins for rotation + button
- Button S1-S4: Additional pushbuttons

For the Mystery Melody Machine, we'll map:
- Encoder 0: Sequencer steps (1-32) selection with apply via button
- Encoder 1: Scale selection with apply via button
- Encoder 2: Root note selection (C-B) with apply via button
- Encoder 3: Direction pattern selection with apply via button
- Button S1: Select NTS-1 MK2 CC profile
- Button S2: Select Roland JX-08 CC profile
- Button S3: Select Waldorf Streichfett CC profile
- Button S4: Select Generic Analog CC profile
"""

import logging
import threading
import time
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import IntEnum

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("RPi.GPIO not available - Zynthian hardware interface disabled")


class ZynthianEncoder(IntEnum):
    """Zynthian v4 encoder assignments"""
    LAYER = 0    # Top-left encoder (Sequencer Steps 1-32)
    BACK = 1     # Top-right encoder (Scale Selection)
    SELECT = 2   # Bottom-left encoder (Root Note C-B)
    LEARN = 3    # Bottom-right encoder (Direction Pattern)


class ZynthianButton(IntEnum):
    """Zynthian v4 button assignments"""
    S1 = 0  # Select NTS-1 MK2 CC profile
    S2 = 1  # Select Roland JX-08 CC profile
    S3 = 2  # Select Waldorf Streichfett CC profile  
    S4 = 3  # Select Generic Analog CC profile


@dataclass
class EncoderEvent:
    """Represents an encoder rotation or button press event"""
    encoder: ZynthianEncoder
    direction: int  # -1 for counter-clockwise, +1 for clockwise, 0 for button press
    is_button: bool = False


@dataclass 
class ButtonEvent:
    """Represents a button press event"""
    button: ZynthianButton
    pressed: bool  # True for press, False for release


class ZynthianHardwareInterface:
    """
    Direct interface to Zynthian v4 hardware components.
    
    This class provides access to the physical controls without requiring
    the full Zynthian OS stack.
    """
    
    # GPIO pin mappings for Zynthian v4
    # These are the actual pin assignments from Zynthian v4 hardware
    ENCODER_PINS = {
        ZynthianEncoder.LAYER: {'a': 27, 'b': 25, 'btn': 23},
        ZynthianEncoder.BACK: {'a': 21, 'b': 26, 'btn': 7},
        ZynthianEncoder.SELECT: {'a': 4, 'b': 0, 'btn': 2},
        ZynthianEncoder.LEARN: {'a': 3, 'b': 1, 'btn': 12}
    }
    
    BUTTON_PINS = {
        ZynthianButton.S1: 107,  # Switch 1
        ZynthianButton.S2: 23,   # Switch 2  
        ZynthianButton.S3: 106,  # Switch 3
        ZynthianButton.S4: 105   # Switch 4
    }
    
    def __init__(self):
        self.log = logging.getLogger("zynthian_hw")
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # Event callbacks
        self.encoder_callback: Optional[Callable[[EncoderEvent], None]] = None
        self.button_callback: Optional[Callable[[ButtonEvent], None]] = None
        
        # State tracking
        self._encoder_states: Dict[ZynthianEncoder, Dict[str, Any]] = {}
        self._button_states: Dict[ZynthianButton, bool] = {}
        
        # Initialize GPIO if available
        if not GPIO_AVAILABLE:
            self.log.error("Cannot initialize Zynthian hardware - RPi.GPIO not available")
            return
            
        try:
            self._setup_gpio()
            self.log.info("Zynthian v4 hardware interface initialized")
        except Exception as e:
            self.log.error(f"Failed to initialize Zynthian hardware: {e}")
    
    def _setup_gpio(self):
        """Initialize GPIO pins for encoders and buttons"""
        if not GPIO_AVAILABLE:
            return
            
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup encoder pins
        for encoder, pins in self.ENCODER_PINS.items():
            # Encoder rotation pins
            GPIO.setup(pins['a'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(pins['b'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            # Encoder button pin
            GPIO.setup(pins['btn'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Initialize encoder state
            self._encoder_states[encoder] = {
                'last_a': GPIO.input(pins['a']),
                'last_b': GPIO.input(pins['b']),
                'last_btn': GPIO.input(pins['btn'])
            }
        
        # Setup button pins
        for button, pin in self.BUTTON_PINS.items():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self._button_states[button] = GPIO.input(pin)
    
    def start(self):
        """Start the hardware monitoring thread"""
        if not GPIO_AVAILABLE or self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._monitor_hardware, daemon=True)
        self._thread.start()
        self.log.info("Zynthian hardware monitoring started")
    
    def stop(self):
        """Stop the hardware monitoring"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
            except:
                pass
        
        self.log.info("Zynthian hardware monitoring stopped")
    
    def set_encoder_callback(self, callback: Callable[[EncoderEvent], None]):
        """Set callback for encoder events"""
        self.encoder_callback = callback
    
    def set_button_callback(self, callback: Callable[[ButtonEvent], None]):
        """Set callback for button events"""
        self.button_callback = callback
    
    def _monitor_hardware(self):
        """Main hardware monitoring loop"""
        while self._running:
            try:
                self._check_encoders()
                self._check_buttons()
                time.sleep(0.001)  # 1ms polling rate
            except Exception as e:
                self.log.error(f"Hardware monitoring error: {e}")
                time.sleep(0.1)
    
    def _check_encoders(self):
        """Check for encoder rotation and button presses"""
        if not GPIO_AVAILABLE:
            return
            
        for encoder, pins in self.ENCODER_PINS.items():
            state = self._encoder_states[encoder]
            
            # Check encoder rotation
            current_a = GPIO.input(pins['a'])
            current_b = GPIO.input(pins['b'])
            
            if current_a != state['last_a']:
                # Determine rotation direction
                if current_a != current_b:
                    direction = 1  # Clockwise
                else:
                    direction = -1  # Counter-clockwise
                
                # Fire encoder event
                if self.encoder_callback:
                    event = EncoderEvent(encoder, direction, False)
                    self.encoder_callback(event)
                
                state['last_a'] = current_a
            
            state['last_b'] = current_b
            
            # Check encoder button
            current_btn = GPIO.input(pins['btn'])
            if current_btn != state['last_btn'] and current_btn == 0:  # Button press (active low)
                if self.encoder_callback:
                    event = EncoderEvent(encoder, 0, True)
                    self.encoder_callback(event)
                
                state['last_btn'] = current_btn
    
    def _check_buttons(self):
        """Check for button presses"""
        if not GPIO_AVAILABLE:
            return
            
        for button, pin in self.BUTTON_PINS.items():
            current_state = GPIO.input(pin) == 0  # Active low
            last_state = self._button_states[button]
            
            if current_state != last_state:
                if self.button_callback:
                    event = ButtonEvent(button, current_state)
                    self.button_callback(event)
                
                self._button_states[button] = current_state


class ZynthianMidiInterface:
    """
    Interface to Zynthian's built-in MIDI hardware.
    
    This provides access to the DIN MIDI connectors without needing USB.
    The Zynthian v4 has native MIDI DIN connectors that appear as ALSA
    sequencer ports.
    """
    
    def __init__(self):
        self.log = logging.getLogger("zynthian_midi")
    
    def get_available_ports(self) -> Dict[str, str]:
        """
        Get available MIDI ports on Zynthian hardware.
        
        Returns:
            Dictionary mapping port names to descriptions
        """
        import mido
        
        ports = {}
        
        # Input ports
        for port_name in mido.get_input_names():
            if self._is_zynthian_port(port_name):
                ports[f"input:{port_name}"] = f"Zynthian MIDI Input: {port_name}"
        
        # Output ports  
        for port_name in mido.get_output_names():
            if self._is_zynthian_port(port_name):
                ports[f"output:{port_name}"] = f"Zynthian MIDI Output: {port_name}"
        
        return ports
    
    def _is_zynthian_port(self, port_name: str) -> bool:
        """Check if a MIDI port belongs to Zynthian hardware"""
        # Zynthian typically uses these MIDI interface names
        zynthian_identifiers = [
            "pisound",
            "audiophonics",
            "hifiberry", 
            "iqaudio",
            "fe-pi",
            "midi"
        ]
        
        port_lower = port_name.lower()
        return any(identifier in port_lower for identifier in zynthian_identifiers)
    
    def get_recommended_ports(self) -> Dict[str, str]:
        """
        Get recommended MIDI port configuration for Zynthian.
        
        Returns:
            Dictionary with 'input' and 'output' port recommendations
        """
        available = self.get_available_ports()
        
        # Look for DIN MIDI ports first
        input_port = None
        output_port = None
        
        for port_id, description in available.items():
            port_type, port_name = port_id.split(":", 1)
            
            if port_type == "input" and input_port is None:
                if "midi" in port_name.lower():
                    input_port = port_name
            
            if port_type == "output" and output_port is None:
                if "midi" in port_name.lower():
                    output_port = port_name
        
        return {
            "input": input_port or "auto",
            "output": output_port or "auto"
        }
