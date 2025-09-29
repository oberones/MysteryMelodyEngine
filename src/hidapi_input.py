"""HID Input using hidapi library (fallback for pygame compatibility issues)."""

from __future__ import annotations
import logging
import time
import threading
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

try:
    import hid
except ImportError:
    hid = None

from events import SemanticEvent

log = logging.getLogger(__name__)


@dataclass
class ButtonState:
    """Track button state with debouncing."""
    pressed: bool = False
    last_change_time: float = 0.0
    debounce_time: float = 0.05  # 50ms debounce


class HidapiInput:
    """HID input using hidapi library (fallback implementation)."""
    
    def __init__(self, device_name: str, button_mapping: Dict[int, str], 
                 joystick_mapping: Dict[str, str], callback: Callable[[SemanticEvent], None]):
        """
        Initialize hidapi-based HID input handler.
        
        Args:
            device_name: Name of the HID device to find
            button_mapping: Map of button index -> semantic action
            joystick_mapping: Map of direction -> semantic action  
            callback: Function to call with semantic events
        """
        if not hid:
            raise ImportError("hidapi library not available")
            
        self.device_name = device_name
        self.button_mapping = button_mapping
        self.joystick_mapping = joystick_mapping
        self.callback = callback
        
        # State tracking
        self.button_states: Dict[int, ButtonState] = {}
        # Initialize button states
        for button_idx in self.button_mapping.keys():
            self.button_states[button_idx] = ButtonState()
            
        self.joystick_deadzone = 20  # Deadzone for joystick axes (hidapi uses different scale)
        self.joystick_last_direction: Optional[str] = None
        self.joystick_direction_time = 0.0
        self.joystick_repeat_delay = 0.3  # Prevent rapid fire joystick events
        
        # Threading and device
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._device: Optional[Any] = None  # hid.device type annotation causes issues
        self._device_info: Optional[Dict] = None
        
    def start(self):
        """Start the hidapi HID input thread."""
        if self._running:
            return
            
        log.info("Initializing hidapi HID input for device: %s", self.device_name)
        
        # Find the device
        devices = hid.enumerate()
        target_device = None
        
        log.info("Found %d hidapi HID devices", len(devices))
        for device in devices:
            product = device['product_string'] or 'Unknown'
            # More flexible matching - normalize whitespace and case
            device_name_normalized = ' '.join(self.device_name.lower().split())
            product_normalized = ' '.join(product.lower().split())
            
            if device_name_normalized in product_normalized:
                target_device = device
                log.info("Selected hidapi HID device: %s", product)
                break
                
        if not target_device:
            device_list = [d['product_string'] for d in devices if d['product_string']]
            raise RuntimeError(f"hidapi HID device '{self.device_name}' not found. Available devices: {device_list}")
            
        self._device_info = target_device
        
        # Open the device
        try:
            self._device = hid.device()
            self._device.open(target_device['vendor_id'], target_device['product_id'])
            self._device.set_nonblocking(True)
        except Exception as e:
            log.error("Failed to open hidapi device: %s", e)
            log.error("Device info: VID=0x%04x, PID=0x%04x, Path=%s", 
                     target_device['vendor_id'], target_device['product_id'], target_device.get('path', 'N/A'))
            raise
        
        # Log device capabilities
        log.info("hidapi HID device capabilities:")
        log.info("  Product: %s", self._device.get_product_string())
        log.info("  Manufacturer: %s", self._device.get_manufacturer_string())
        log.info("  VID: 0x%04x, PID: 0x%04x", target_device['vendor_id'], target_device['product_id'])
        
        self._running = True
        self._thread = threading.Thread(target=self._input_thread, daemon=True)
        self._thread.start()
        log.info("hidapi HID input thread started")
        
    def stop(self):
        """Stop the hidapi HID input thread."""
        if not self._running:
            return
            
        log.info("Stopping hidapi HID input")
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=1.0)
            
        if self._device:
            self._device.close()
            
        log.info("hidapi HID input stopped")
        
    def _input_thread(self):
        """Main input polling thread."""
        log.info("hidapi HID input polling thread started")
        
        # Previous state for change detection
        prev_data = None
        
        while self._running:
            try:
                # Read HID report  
                data = self._device.read(64)  # Read up to 64 bytes
                
                if data and data != prev_data:
                    # Log raw data for debugging
                    if len(data) >= 6:
                        log.debug("hidapi raw data: %s", ' '.join(f'{b:02x}' for b in data[:8]))
                    
                    self._process_hid_report(data)
                    prev_data = data[:] # Copy to avoid reference issues
                
                time.sleep(0.001)  # 1ms = 1000Hz polling
                
            except OSError as e:
                if "Operation timed out" not in str(e) and "Resource temporarily unavailable" not in str(e):
                    log.warning("hidapi read error: %s", e)
                time.sleep(0.001)  # Short sleep on timeout
            except Exception as e:
                log.exception("Error in hidapi HID input thread: %s", e)
                time.sleep(0.1)  # Longer sleep on serious error
                
        log.info("hidapi HID input polling thread stopped")
        
    def _process_hid_report(self, data: bytes):
        """Process a HID input report and generate events."""
        if len(data) < 8:
            return
            
        # Based on analysis of the Generic USB Joystick:
        # Byte 0: X-axis (7f center, 00=left, ff=right)  
        # Byte 1: Y-axis (7f center, 00=up, ff=down)
        # Byte 2: Z-axis or other axis
        # Byte 5: Button bits (bit pattern)
        
        x_axis = data[0]
        y_axis = data[1] 
        button_data = data[5] if len(data) > 5 else 0
        
        current_time = time.time()
        
        # Process joystick axes
        self._check_joystick_axes(x_axis, y_axis, current_time)
        
        # Process buttons - decode button bits
        self._check_button_bits(button_data, current_time)
        
    def _check_joystick_axes(self, x_axis: int, y_axis: int, current_time: float):
        """Check joystick axes and generate direction events."""
        # Convert from 0-255 to centered values (127 = center)
        x_centered = x_axis - 0x7f  # -127 to +128
        y_centered = y_axis - 0x7f  # -127 to +128
        
        direction = None
        
        # Check for direction with deadzone
        if abs(x_centered) > self.joystick_deadzone:
            direction = "right" if x_centered > 0 else "left"
        elif abs(y_centered) > self.joystick_deadzone:
            direction = "up" if y_centered < 0 else "down"  # Y often inverted
            
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
                        source="hidapi_joystick", 
                        value=127,  # Pulse value like original joystick
                        raw_cc=cc_num,
                        channel=1,
                    )
                    log.debug("hidapi joystick %s -> CC %d", direction, cc_num)
                    self._emit_event(evt)
                    
            self.joystick_last_direction = direction
            self.joystick_direction_time = current_time
            
        # Reset direction tracking when joystick returns to center
        elif direction is None:
            self.joystick_last_direction = None
            
    def _check_button_bits(self, button_data: int, current_time: float):
        """Check button bits and generate button events."""
        # The button data appears to be a bit field
        # We need to check each bit for button states
        
        # Based on observed data, buttons seem to be in bits of button_data
        # We'll check up to 10 buttons (bits 0-9) as we have 10 arcade buttons mapped
        for button_idx in range(min(10, len(self.button_mapping))):
            if button_idx not in self.button_mapping:
                continue
                
            # Check if this button bit is set
            # From our testing, button presses change the button_data byte
            # Let's try different bit positions to see which works
            button_pressed = bool(button_data & (1 << button_idx))
            
            # Debug logging for first few button checks
            if button_idx < 3:
                log.debug("hidapi button %d: data=0x%02x, bit_%d=%s", 
                         button_idx, button_data, button_idx, button_pressed)
            
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
                            source="hidapi_button",
                            value=100,  # Fixed velocity
                            raw_note=midi_note,
                            channel=1,
                        )
                        log.info("hidapi button %d pressed -> note %d", button_idx, midi_note)
                        self._emit_event(evt)
                        
    def _emit_event(self, event: SemanticEvent):
        """Emit a semantic event via callback."""
        try:
            self.callback(event)
        except Exception as e:
            log.exception("Error emitting hidapi event: %s", e)


def create_hidapi_input(device_name: str, button_mapping: Dict[int, str], 
                        joystick_mapping: Dict[str, str], 
                        callback: Callable[[SemanticEvent], None]) -> HidapiInput:
    """Factory function to create and configure hidapi HID input."""
    return HidapiInput(device_name, button_mapping, joystick_mapping, callback)
