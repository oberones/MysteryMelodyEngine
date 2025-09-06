# Mutation Engine Configuration Guide

## Overview

The mutation engine timing is fully configurable through the `config.yaml` file. This allows you to adjust how frequently the system applies automatic parameter changes.

## Configuration Options

### Mutation Timing Settings

```yaml
mutation:
  interval_min_s: 120          # Minimum time between mutations (seconds)
  interval_max_s: 240          # Maximum time between mutations (seconds)
  max_changes_per_cycle: 2     # Maximum parameters changed per mutation cycle
```

### Default Values

- **Minimum interval**: 120 seconds (2 minutes)
- **Maximum interval**: 240 seconds (4 minutes)  
- **Max changes per cycle**: 2 parameters

This means the system will automatically mutate 1-2 parameters every 2-4 minutes, creating a slowly evolving musical experience.

## Customizing Mutation Timing

### Faster Evolution (More Frequent Changes)

For more active parameter evolution:

```yaml
mutation:
  interval_min_s: 60           # 1 minute minimum
  interval_max_s: 120          # 2 minutes maximum
  max_changes_per_cycle: 3     # Up to 3 changes per cycle
```

### Slower Evolution (Less Frequent Changes)

For more stable, slowly evolving music:

```yaml
mutation:
  interval_min_s: 300          # 5 minutes minimum
  interval_max_s: 600          # 10 minutes maximum
  max_changes_per_cycle: 1     # Only 1 change per cycle
```

### Very Active Evolution (Experimental)

For constantly changing parameters:

```yaml
mutation:
  interval_min_s: 30           # 30 seconds minimum
  interval_max_s: 60           # 1 minute maximum  
  max_changes_per_cycle: 4     # Up to 4 changes per cycle
```

### Minimal Evolution (Rare Changes)

For mostly static music with occasional surprises:

```yaml
mutation:
  interval_min_s: 600          # 10 minutes minimum
  interval_max_s: 1200         # 20 minutes maximum
  max_changes_per_cycle: 1     # Only 1 change per cycle
```

## Understanding the Impact

### Interval Timing
- **Short intervals (30-120s)**: Create actively evolving, dynamic music
- **Medium intervals (120-300s)**: Provide balanced evolution (default)
- **Long intervals (300+s)**: Create stable music with occasional shifts

### Max Changes Per Cycle
- **1 change**: Subtle, focused evolution
- **2 changes**: Balanced complexity (default)
- **3+ changes**: More dramatic shifts

## Musical Considerations

### Genre-Specific Settings

**Ambient/Drone**:
```yaml
mutation:
  interval_min_s: 180          # 3 minutes
  interval_max_s: 420          # 7 minutes
  max_changes_per_cycle: 1     # Gentle single changes
```

**Techno/Electronic**:
```yaml
mutation:
  interval_min_s: 90           # 1.5 minutes
  interval_max_s: 180          # 3 minutes
  max_changes_per_cycle: 2     # Moderate complexity
```

**Experimental/Generative**:
```yaml
mutation:
  interval_min_s: 45           # 45 seconds
  interval_max_s: 90           # 1.5 minutes
  max_changes_per_cycle: 3     # High activity
```

## Real-time Monitoring

You can monitor mutation activity in the logs:

```
mutation_engine_init rules=8 interval=120-240s max_changes=2
mutation_cycle_complete rules_selected=2 mutations_applied=2
mutation_applied parameter=bpm old=120.0 new=123.4 delta=3.400 description=Tempo drift
```

## Advanced Usage

### Disabling Mutations Temporarily

Set a very long interval to effectively disable mutations:

```yaml
mutation:
  interval_min_s: 86400        # 24 hours
  interval_max_s: 86400        # 24 hours
  max_changes_per_cycle: 0     # No changes
```

### Manual Mutation Control

You can also trigger mutations manually in code:

```python
# Force an immediate mutation
mutation_engine.force_mutation()

# Get current timing stats
stats = mutation_engine.get_stats()
print(f"Time to next mutation: {stats['time_to_next_mutation_s']:.1f}s")
```

## Configuration Validation

The system validates your configuration values:

- `interval_min_s` and `interval_max_s` must be positive integers
- `interval_min_s` must be ≤ `interval_max_s`
- `max_changes_per_cycle` must be a positive integer

Invalid configurations will cause startup errors with clear error messages.

## Summary

The mutation engine timing is fully configurable and defaults to a musically balanced 2-4 minute interval. Adjust these values in `config.yaml` to match your desired level of musical evolution and restart the engine to apply changes.
