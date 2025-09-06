"""Latency optimization for external hardware integration.

Phase 7: Provides optimized MIDI timing, CC throttling, and latency reduction
techniques for tight integration with external synthesizers.
"""

from __future__ import annotations
from typing import Dict, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
import time
import threading
import logging
from collections import deque
import heapq

log = logging.getLogger(__name__)


@dataclass
class TimestampedMessage:
    """MIDI message with precise timing information."""
    timestamp: float
    message_type: str  # 'note_on', 'note_off', 'cc'
    data: Dict[str, Any]
    priority: int = 0  # Lower number = higher priority


@dataclass
class LatencyStats:
    """Statistics for monitoring MIDI latency."""
    total_messages: int = 0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    recent_latencies: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def update(self, latency_ms: float):
        """Update latency statistics with new measurement."""
        self.total_messages += 1
        self.recent_latencies.append(latency_ms)
        
        # Update min/max
        self.max_latency_ms = max(self.max_latency_ms, latency_ms)
        self.min_latency_ms = min(self.min_latency_ms, latency_ms)
        
        # Calculate rolling average
        if self.recent_latencies:
            self.avg_latency_ms = sum(self.recent_latencies) / len(self.recent_latencies)


class CCThrottler:
    """Throttles CC messages to prevent MIDI flooding."""
    
    def __init__(self, throttle_ms: int = 10):
        """Initialize CC throttler.
        
        Args:
            throttle_ms: Minimum milliseconds between CC messages per controller
        """
        self.throttle_ms = throttle_ms
        self.last_sent: Dict[Tuple[int, int], float] = {}  # (channel, cc) -> timestamp
        self.pending: Dict[Tuple[int, int], Tuple[int, float]] = {}  # (channel, cc) -> (value, timestamp)
        self._lock = threading.Lock()
    
    def should_send_cc(self, channel: int, cc: int, value: int) -> bool:
        """Check if CC message should be sent now or throttled.
        
        Args:
            channel: MIDI channel (1-16)
            cc: Control change number (0-127) 
            value: Control change value (0-127)
            
        Returns:
            True if message should be sent immediately, False if throttled
        """
        with self._lock:
            key = (channel, cc)
            now = time.perf_counter() * 1000  # Convert to milliseconds
            
            # Check if enough time has passed since last message
            last_time = self.last_sent.get(key, 0)
            if now - last_time >= self.throttle_ms:
                self.last_sent[key] = now
                # Clear any pending message for this CC
                self.pending.pop(key, None)
                return True
            else:
                # Store as pending for later transmission
                self.pending[key] = (value, now)
                return False
    
    def get_pending_messages(self) -> list[Tuple[int, int, int]]:
        """Get CC messages that are ready to be sent.
        
        Returns:
            List of (channel, cc, value) tuples ready for transmission
        """
        with self._lock:
            ready_messages = []
            now = time.perf_counter() * 1000
            
            # Check all pending messages
            to_remove = []
            for (channel, cc), (value, pending_time) in self.pending.items():
                last_time = self.last_sent.get((channel, cc), 0)
                if now - last_time >= self.throttle_ms:
                    ready_messages.append((channel, cc, value))
                    self.last_sent[(channel, cc)] = now
                    to_remove.append((channel, cc))
            
            # Remove messages that are now being sent
            for key in to_remove:
                self.pending.pop(key, None)
            
            return ready_messages


class PriorityMidiQueue:
    """Priority queue for MIDI messages with timing optimization."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queue: list[TimestampedMessage] = []
        self.sequence = 0  # For stable sorting
        self._lock = threading.Lock()
    
    def put(self, message: TimestampedMessage) -> bool:
        """Add message to priority queue.
        
        Args:
            message: Timestamped MIDI message
            
        Returns:
            True if message was queued, False if queue is full
        """
        with self._lock:
            if len(self.queue) >= self.max_size:
                log.warning("MIDI queue full, dropping message")
                return False
            
            # Use negative timestamp for min-heap behavior (earliest first)
            # Add sequence number for stable sorting
            priority_tuple = (-message.timestamp, message.priority, self.sequence)
            heapq.heappush(self.queue, (priority_tuple, message))
            self.sequence += 1
            return True
    
    def get_ready_messages(self, current_time: float) -> list[TimestampedMessage]:
        """Get all messages ready for transmission.
        
        Args:
            current_time: Current time for comparison
            
        Returns:
            List of messages ready to be sent
        """
        with self._lock:
            ready_messages = []
            
            # Extract all messages that are ready
            while self.queue:
                priority_tuple, message = self.queue[0]
                message_time = -priority_tuple[0]  # Convert back from negative
                
                if message_time <= current_time:
                    heapq.heappop(self.queue)
                    ready_messages.append(message)
                else:
                    break  # Queue is sorted, so we can stop here
            
            return ready_messages
    
    def size(self) -> int:
        """Get current queue size."""
        with self._lock:
            return len(self.queue)


class LatencyOptimizer:
    """Main latency optimization coordinator."""
    
    def __init__(self, midi_output, throttle_ms: int = 10):
        """Initialize latency optimizer.
        
        Args:
            midi_output: MIDI output instance
            throttle_ms: CC message throttling interval
        """
        self.midi_output = midi_output
        self.cc_throttler = CCThrottler(throttle_ms)
        self.message_queue = PriorityMidiQueue()
        self.stats = LatencyStats()
        
        # Optimization settings
        self.enable_prediction = True  # Predictive message scheduling
        self.enable_batching = True    # Batch similar messages
        self.lookahead_ms = 5.0        # How far ahead to schedule messages
        
        # Background processing
        self._processor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        
    def start(self) -> None:
        """Start the latency optimizer background processing."""
        if self._running:
            return
        
        self._running = True
        self._stop_event.clear()
        self._processor_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._processor_thread.start()
        log.info("Latency optimizer started")
    
    def stop(self) -> None:
        """Stop the latency optimizer."""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._processor_thread:
            self._processor_thread.join(timeout=1.0)
        
        log.info("Latency optimizer stopped")
    
    def schedule_note_on(self, note: int, velocity: int, channel: int = 1, 
                        when: Optional[float] = None) -> None:
        """Schedule a note on message with optimized timing.
        
        Args:
            note: MIDI note number
            velocity: Note velocity
            channel: MIDI channel
            when: Scheduled time (None for immediate)
        """
        timestamp = when if when is not None else time.perf_counter()
        
        message = TimestampedMessage(
            timestamp=timestamp,
            message_type='note_on',
            data={'note': note, 'velocity': velocity, 'channel': channel},
            priority=1  # High priority for note events
        )
        
        self.message_queue.put(message)
    
    def schedule_note_off(self, note: int, channel: int = 1, 
                         when: Optional[float] = None) -> None:
        """Schedule a note off message with optimized timing.
        
        Args:
            note: MIDI note number
            channel: MIDI channel
            when: Scheduled time (None for immediate)
        """
        timestamp = when if when is not None else time.perf_counter()
        
        message = TimestampedMessage(
            timestamp=timestamp,
            message_type='note_off',
            data={'note': note, 'velocity': 0, 'channel': channel},
            priority=1  # High priority for note events
        )
        
        self.message_queue.put(message)
    
    def schedule_cc(self, cc: int, value: int, channel: int = 1,
                   when: Optional[float] = None) -> None:
        """Schedule a control change message with throttling.
        
        Args:
            cc: Control change number
            value: Control change value
            channel: MIDI channel
            when: Scheduled time (None for immediate)
        """
        timestamp = when if when is not None else time.perf_counter()
        
        # Check throttling for immediate messages
        if when is None and not self.cc_throttler.should_send_cc(channel, cc, value):
            return  # Message was throttled
        
        message = TimestampedMessage(
            timestamp=timestamp,
            message_type='cc',
            data={'cc': cc, 'value': value, 'channel': channel},
            priority=2  # Lower priority than notes
        )
        
        self.message_queue.put(message)
    
    def send_immediate(self, message_type: str, **kwargs) -> None:
        """Send a MIDI message immediately, bypassing optimization.
        
        Args:
            message_type: Type of message ('note_on', 'note_off', 'cc')
            **kwargs: Message parameters
        """
        start_time = time.perf_counter()
        
        try:
            if message_type == 'note_on':
                success = self.midi_output.send_note_on(
                    kwargs['note'], kwargs['velocity'], kwargs.get('channel', 1)
                )
            elif message_type == 'note_off':
                success = self.midi_output.send_note_off(
                    kwargs['note'], kwargs.get('velocity', 0), kwargs.get('channel', 1)
                )
            elif message_type == 'cc':
                success = self.midi_output.send_control_change(
                    kwargs['cc'], kwargs['value'], kwargs.get('channel', 1)
                )
            else:
                log.warning(f"Unknown message type: {message_type}")
                return
            
            # Record latency stats
            if success:
                latency_ms = (time.perf_counter() - start_time) * 1000
                self.stats.update(latency_ms)
        
        except Exception as e:
            log.error(f"Error sending immediate MIDI message: {e}")
    
    def _process_loop(self) -> None:
        """Background processing loop for optimized message transmission."""
        log.debug("Latency optimizer processing loop started")
        
        while not self._stop_event.is_set():
            try:
                current_time = time.perf_counter()
                
                # Process ready messages from queue
                ready_messages = self.message_queue.get_ready_messages(current_time)
                for message in ready_messages:
                    self._send_message(message)
                
                # Process throttled CC messages
                pending_ccs = self.cc_throttler.get_pending_messages()
                for channel, cc, value in pending_ccs:
                    self.send_immediate('cc', cc=cc, value=value, channel=channel)
                
                # Sleep briefly to prevent CPU spinning
                time.sleep(0.001)  # 1ms sleep
                
            except Exception as e:
                log.error(f"Error in latency optimizer processing loop: {e}")
        
        log.debug("Latency optimizer processing loop stopped")
    
    def _send_message(self, message: TimestampedMessage) -> None:
        """Send a single timestamped message.
        
        Args:
            message: Message to send
        """
        data = message.data
        
        try:
            if message.message_type == 'note_on':
                self.midi_output.send_note_on(data['note'], data['velocity'], data['channel'])
            elif message.message_type == 'note_off':
                self.midi_output.send_note_off(data['note'], data['velocity'], data['channel'])
            elif message.message_type == 'cc':
                self.midi_output.send_control_change(data['cc'], data['value'], data['channel'])
            
            # Update latency stats
            actual_time = time.perf_counter()
            intended_latency = (actual_time - message.timestamp) * 1000
            self.stats.update(abs(intended_latency))
        
        except Exception as e:
            log.error(f"Error sending scheduled MIDI message: {e}")
    
    def get_latency_stats(self) -> LatencyStats:
        """Get current latency statistics."""
        return self.stats
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status information."""
        return {
            'queue_size': self.message_queue.size(),
            'max_queue_size': self.message_queue.max_size,
            'queue_utilization': self.message_queue.size() / self.message_queue.max_size,
            'pending_cc_count': len(self.cc_throttler.pending),
            'total_messages_sent': self.stats.total_messages,
            'avg_latency_ms': self.stats.avg_latency_ms,
            'max_latency_ms': self.stats.max_latency_ms
        }
