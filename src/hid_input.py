"""HID Input for arcade buttons and joystick with pygame/hidapi dual backend support."""

from __future__ import annotations
import logging
import time
import threading
from enum import Enum
from typing import Optional, Callable, Dict, Any, Union
from dataclasses import dataclass

# Try importing pygame first
try:
    import pygame
    pygame_available = True
except ImportError:
    pygame_available = False

# Try importing hidapi as fallback
try:
    from hidapi_input import HidapiInput
    hidapi_available = True
except ImportError:
    hidapi_available = False

from events import SemanticEvent

log = logging.getLogger(__name__)


class JoystickDirection(Enum):
    """Enumeration for joystick directions."""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class ButtonState:
    """Track button state with debouncing."""
    pressed: bool = False
    last_change_time: float = 0.0
    debounce_time: float = 0.05  # 50ms debounce


class HidInput:
    """HID input handler with pygame and hidapi fallback support."""
    
    def __init__(self, device_name: str, button_mapping: Dict[int, str], 
                 joystick_mapping: Dict[str, str], callback: Callable[[SemanticEvent], None]):
        """
        Initialize HID input with dual backend support.
        
        Args:
            device_name: Name of the HID device to find
            button_mapping: Map of button index -> semantic action
            joystick_mapping: Map of direction -> semantic action  
            callback: Function to call with semantic events
        """
        self.device_name = device_name
        self.button_mapping = button_mapping
        self.joystick_mapping = joystick_mapping
        self.callback = callback
        
        # Backend selection
        self._backend: Optional[Union['PygameHidInput', 'HidapiInput']] = None
        self._backend_type: Optional[str] = None
        
    def start(self):
        """Start HID input with automatic backend selection."""
        log.info("Starting HID input for device: %s", self.device_name)
        
        # Try pygame first
        if pygame_available:
            try:
                log.info("Attempting pygame HID backend")
                pygame_backend = PygameHidInput(
                    self.device_name, self.button_mapping, 
                    self.joystick_mapping, self.callback
                )
                pygame_backend.start()
                self._backend = pygame_backend
                self._backend_type = "pygame"
                log.info("Using pygame HID backend successfully")
                return
            except Exception as e:
                log.warning("pygame HID backend failed: %s", e)
                log.info("Falling back to hidapi backend")
                
        # Try hidapi fallback
        if hidapi_available:
            try:
                log.info("Attempting hidapi HID backend")
                hidapi_backend = HidapiInput(
                    self.device_name, self.button_mapping,
                    self.joystick_mapping, self.callback
                )
                hidapi_backend.start()
                self._backend = hidapi_backend
                self._backend_type = "hidapi"
                log.info("Using hidapi HID backend successfully")
                return
            except Exception as e:
                log.error("hidapi HID backend failed: %s", e)
                
        # No backend succeeded
        available_backends = []
        if pygame_available:
            available_backends.append("pygame")
        if hidapi_available:
            available_backends.append("hidapi")
            
        raise RuntimeError(
            f"No HID backend could initialize device '{self.device_name}'. "
            f"Available backends: {available_backends}. "
            f"Make sure the device is connected and accessible."
        )
        
    def stop(self):
        """Stop the HID input backend."""
        if self._backend:
            log.info("Stopping HID input (%s backend)", self._backend_type)
            self._backend.stop()
            self._backend = None
            self._backend_type = None


class PygameHidInput:
    """Original pygame-based HID input handler."""
    
    def __init__(self, device_name: str, button_mapping: Dict[int, str], 
                 joystick_mapping: Dict[str, str], callback: Callable[[SemanticEvent], None]):
        """
        Initialize pygame HID input handler.
        
        Args:
            device_name: Name of the joystick device to find
            button_mapping: Map of button index -> semantic action
            joystick_mapping: Map of direction -> semantic action  
            callback: Function to call with semantic events
        """
        if not pygame_available:
            raise ImportError("pygame not available")
            
        self.device_name = device_name
        self.button_mapping = button_mapping
        self.joystick_mapping = joystick_mapping
        self.callback = callback
        
        # State tracking
        self.button_states: Dict[int, ButtonState] = {}
        # Initialize button states
        for button_idx in self.button_mapping.keys():
            self.button_states[button_idx] = ButtonState()
            
        self.joystick_deadzone = 0.3
        self.joystick_last_direction: Optional[str] = None
        self.joystick_direction_time = 0.0
        self.joystick_repeat_delay = 0.3  # Prevent rapid fire joystick events
        
        # Threading and pygame state
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._joystick: Optional[Any] = None  # pygame.Joystick type annotation issues
        
    def start(self):
        """Start the pygame HID input thread."""
        if self._running:
            return
            
        log.info("Initializing pygame for HID input")
        pygame.init()
        pygame.joystick.init()
        
        # Find the joystick
        joystick_count = pygame.joystick.get_count()
        log.info("Found %d pygame joystick(s)", joystick_count)
        
        target_joystick = None
        for i in range(joystick_count):
            joystick = pygame.joystick.Joystick(i)
            if self.device_name.lower() in joystick.get_name().lower():
                target_joystick = joystick
                log.info("Selected pygame joystick: %s", joystick.get_name())
                break
                
        if not target_joystick:
            joystick_list = [pygame.joystick.Joystick(i).get_name() for i in range(joystick_count)]
            raise RuntimeError(f"pygame joystick '{self.device_name}' not found. Available joysticks: {joystick_list}")
            
        self._joystick = target_joystick
        self._joystick.init()
        
        # Log device capabilities
        log.info("pygame joystick capabilities:")
        log.info("  Name: %s", self._joystick.get_name())
        log.info("  Axes: %d", self._joystick.get_numaxes())
        log.info("  Buttons: %d", self._joystick.get_numbuttons())
        log.info("  Hats: %d", self._joystick.get_numhats())
        
        self._running = True
        self._thread = threading.Thread(target=self._input_thread, daemon=True)
        self._thread.start()
        log.info("pygame HID input thread started")
        
    def stop(self):
        """Stop the pygame HID input thread."""
        if not self._running:
            return
            
        log.info("Stopping pygame HID input")
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=1.0)
            
        if self._joystick:
            self._joystick.quit()
            
        pygame.joystick.quit()
        pygame.quit()
        log.info("pygame HID input stopped")
        
    def _input_thread(self):
        """Main input polling thread."""
        log.info("pygame HID input polling thread started")
        
        while self._running:
            try:
                pygame.event.pump()  # Process pygame events
                
                current_time = time.time()
                
                # Check buttons
                for button_idx in self.button_mapping:
                    if button_idx < self._joystick.get_numbuttons():
                        self._check_button(button_idx, current_time)
                
                # Check joystick axes and hats
                self._check_joystick(current_time)
                
                time.sleep(0.01)  # 100Hz polling
                
            except Exception as e:
                log.exception("Error in pygame HID input thread: %s", e)
                time.sleep(0.1)  # Longer sleep on error
                
        log.info("pygame HID input polling thread stopped")
        
    def _check_button(self, button_idx: int, current_time: float):
        """Check a button state and emit events on changes."""
        button_pressed = self._joystick.get_button(button_idx)
        button_state = self.button_states[button_idx]
        
        # Check if state changed and debounce period has passed
        if (button_pressed != button_state.pressed and 
            current_time - button_state.last_change_time >= button_state.debounce_time):
            
            button_state.pressed = button_pressed
            button_state.last_change_time = current_time
            
            if button_pressed:  # Button press (only emit on press, not release)
                action = self.button_mapping[button_idx]
                
                # Map to MIDI note (buttons 60-69 for trigger_step)
                if action == "trigger_step":
                    midi_note = 60 + button_idx  # Button 0 -> Note 60, etc.
                    evt = SemanticEvent(
                        type=action,
                        source="pygame_button",
                        value=100,  # Fixed velocity
                        raw_note=midi_note,
                        channel=1,
                    )
                    log.debug("pygame button %d pressed -> note %d", button_idx, midi_note)
                    self._emit_event(evt)
    
    def _check_joystick(self, current_time: float):
        """Check joystick axes and hats for direction events."""
        direction = None
        
        # Check hat (D-pad) first - more reliable for discrete directions
        if self._joystick.get_numhats() > 0:
            hat_x, hat_y = self._joystick.get_hat(0)
            direction = self._hat_to_direction(hat_x, hat_y)
        
        # Fallback to analog axes if no hat direction
        if direction is None:
            direction = self._axes_to_direction()
        
        # Only emit events on direction changes and respect repeat delay
        if (direction != self.joystick_last_direction and 
            direction is not None and
            current_time - self.joystick_direction_time >= self.joystick_repeat_delay):
            
            action = self.joystick_mapping.get(direction)
            if action:
                # Map to MIDI CC (CC 50-53 for up/down/left/right)
                cc_map = {"up": 50, "down": 51, "left": 52, "right": 53}
                cc_num = cc_map.get(direction)
                
                if cc_num:
                    evt = SemanticEvent(
                        type=action,
                        source="pygame_joystick", 
                        value=127,  # Pulse value like original joystick
                        raw_cc=cc_num,
                        channel=1,
                    )
                    log.debug("pygame joystick %s -> CC %d", direction, cc_num)
                    self._emit_event(evt)
                    
            self.joystick_last_direction = direction
            self.joystick_direction_time = current_time
            
        # Reset direction tracking when joystick returns to center
        elif direction is None:
            self.joystick_last_direction = None
            
    def _hat_to_direction(self, hat_x: int, hat_y: int) -> Optional[str]:
        """Convert hat values to direction string."""
        if hat_y == 1:
            return "up"
        elif hat_y == -1:
            return "down"
        elif hat_x == -1:
            return "left"
        elif hat_x == 1:
            return "right"
        return None
        
    def _axes_to_direction(self) -> Optional[str]:
        """Convert axis values to direction string using deadzone."""
        if not self._joystick or self._joystick.get_numaxes() < 2:
            return None
            
        x_axis = self._joystick.get_axis(0)  # Usually left/right
        y_axis = self._joystick.get_axis(1)  # Usually up/down
        
        # Apply deadzone
        if abs(x_axis) > self.joystick_deadzone:
            return "right" if x_axis > 0 else "left"
        elif abs(y_axis) > self.joystick_deadzone:
            return "down" if y_axis > 0 else "up"  # Y often inverted
            
        return None
    
    def _emit_event(self, event: SemanticEvent):
        """Emit a semantic event via callback."""
        try:
            self.callback(event)
        except Exception as e:
            log.exception("Error emitting pygame event: %s", e)


def create_hid_input(device_name: str, button_mapping: Dict[int, str], 
                     joystick_mapping: Dict[str, str], 
                     callback: Callable[[SemanticEvent], None]) -> HidInput:
    """Factory function to create and configure HID input."""
    return HidInput(device_name, button_mapping, joystick_mapping, callback)
