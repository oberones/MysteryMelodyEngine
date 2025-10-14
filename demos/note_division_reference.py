#!/usr/bin/env python3
"""Demo showing different note divisions and their timing effects."""

def calculate_timing(bpm, note_division):
    """Calculate timing for different note divisions."""
    
    # Map note divisions to their relationship to quarter notes
    division_to_beats = {
        'whole': 4.0,       # 1 whole note = 4 quarter notes
        'half': 2.0,        # 1 half note = 2 quarter notes  
        'quarter': 1.0,     # 1 quarter note = 1 quarter note
        'eighth': 0.5,      # 1 eighth note = 0.5 quarter notes
        'sixteenth': 0.25   # 1 sixteenth note = 0.25 quarter notes
    }
    
    beats_per_step = division_to_beats[note_division]
    seconds_per_quarter = 60.0 / bpm
    seconds_per_step = seconds_per_quarter * beats_per_step
    
    return seconds_per_step

def main():
    print("Note Division Timing Reference")
    print("=" * 40)
    print()
    
    bpms = [30, 60, 120]
    divisions = ['whole', 'half', 'quarter', 'eighth', 'sixteenth']
    
    for bpm in bpms:
        print(f"BPM: {bpm}")
        print("-" * 20)
        
        for division in divisions:
            timing = calculate_timing(bpm, division)
            
            if timing >= 1.0:
                time_str = f"{timing:.1f}s"
            else:
                time_str = f"{timing*1000:.0f}ms"
            
            print(f"  {division:>10}: {time_str:>6} per step")
        
        print()
    
    print("Usage Examples:")
    print("-" * 15)
    print("• For ambient/meditative music: Use whole or half notes with low BPM (15-30)")
    print("• For ballads: Use quarter notes with moderate BPM (60-80)")
    print("• For dance music: Use eighth or sixteenth notes with high BPM (120-140)")
    print("• For sound design: Use any division with very low BPM (5-15)")
    print()
    print("Configuration:")
    print("Add 'note_division: [whole|half|quarter|eighth|sixteenth]' to your config.yaml")

if __name__ == "__main__":
    main()
