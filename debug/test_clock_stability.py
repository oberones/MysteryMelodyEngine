#!/usr/bin/env python3
"""
Test script to validate the HighResClock stability fix.

This script simulates the conditions that caused the sequencer to stop
after ~2 hours by fast-forwarding the tick count and checking for proper
timing behavior.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sequencer import HighResClock, TickEvent
import time
import threading


def test_large_tick_count():
    """Test clock behavior with very large tick counts (simulating 2+ hours)."""
    print("Testing HighResClock stability with large tick counts...")
    
    clock = HighResClock(bpm=110.0, ppq=24)
    received_ticks = []
    errors = []
    
    def tick_callback(tick: TickEvent):
        received_ticks.append(tick)
        if len(received_ticks) % 1000 == 0:
            print(f"Received {len(received_ticks)} ticks, current step: {tick.step}")
        
        # Stop after a reasonable number of ticks for testing
        if len(received_ticks) >= 5000:
            clock.stop()
    
    # Simulate the clock having run for ~2 hours by setting a large tick count
    # At 110 BPM with PPQ=24: 110 * 24 = 2640 ticks/minute
    # 2 hours = 120 minutes = 120 * 2640 = 316,800 ticks
    # Let's test with an even larger number to be safe
    
    clock.set_tick_callback(tick_callback)
    
    # Manually set a large tick count to simulate long runtime
    large_tick_count = 15_000_000  # ~15 million ticks (about 95 hours at 110 BPM)
    print(f"Setting tick count to {large_tick_count:,} to simulate very long runtime...")
    
    clock.start()
    
    # Modify the clock's internal state to simulate long runtime
    clock._tick_count = large_tick_count
    
    # Let it run for a few seconds to see if it behaves properly
    start_time = time.time()
    timeout = 10.0  # 10 second timeout
    
    while clock._running and (time.time() - start_time) < timeout:
        time.sleep(0.1)
    
    if clock._running:
        clock.stop()
    
    print(f"Test completed. Received {len(received_ticks)} ticks in {time.time() - start_time:.2f} seconds")
    
    if len(received_ticks) > 100:  # Should receive many ticks in 10 seconds
        print("✅ Clock continued running properly with large tick count")
        return True
    else:
        print("❌ Clock failed to generate ticks consistently")
        return False


def test_timing_precision():
    """Test that timing remains precise over time."""
    print("\nTesting timing precision...")
    
    clock = HighResClock(bpm=120.0, ppq=4)  # Fast tempo for quick testing
    tick_times = []
    
    def timing_callback(tick: TickEvent):
        tick_times.append(tick.timestamp)
        if len(tick_times) >= 50:  # Collect 50 ticks
            clock.stop()
    
    clock.set_tick_callback(timing_callback)
    clock.start()
    
    # Wait for completion
    while clock._running:
        time.sleep(0.01)
    
    if len(tick_times) < 10:
        print("❌ Not enough ticks received for timing analysis")
        return False
    
    # Calculate intervals between ticks
    intervals = []
    for i in range(1, len(tick_times)):
        intervals.append(tick_times[i] - tick_times[i-1])
    
    # Expected interval: 60 / (120 * 4) = 0.125 seconds
    expected_interval = 60.0 / (120.0 * 4)
    avg_interval = sum(intervals) / len(intervals)
    
    print(f"Expected interval: {expected_interval:.6f}s")
    print(f"Average interval: {avg_interval:.6f}s")
    print(f"Deviation: {abs(avg_interval - expected_interval):.6f}s")
    
    # Allow 1ms tolerance
    if abs(avg_interval - expected_interval) < 0.001:
        print("✅ Timing precision is good")
        return True
    else:
        print("❌ Timing precision is poor")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("HighResClock Stability Test")
    print("=" * 60)
    
    test1_passed = test_large_tick_count()
    test2_passed = test_timing_precision()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Large tick count test: {'PASS' if test1_passed else 'FAIL'}")
    print(f"Timing precision test: {'PASS' if test2_passed else 'FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n✅ All tests passed! The clock stability fix appears to be working.")
        return 0
    else:
        print("\n❌ Some tests failed. The fix may need additional work.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
