# Extending the Mutation Engine: Custom Rules Guide

## Overview

The Mystery Music Station's mutation engine is designed to be highly extensible, allowing developers to create custom mutation rules that define how parameters evolve over time. This guide covers everything you need to know about creating, configuring, and deploying custom mutation rules.

## Table of Contents

1. [Understanding Mutation Rules](#understanding-mutation-rules)
2. [Basic Custom Rules](#basic-custom-rules)
3. [Advanced Rule Patterns](#advanced-rule-patterns)
4. [Configuration and Deployment](#configuration-and-deployment)
5. [Testing Custom Rules](#testing-custom-rules)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Examples](#examples)

---

## Understanding Mutation Rules

### What is a Mutation Rule?

A mutation rule defines how a specific parameter can be automatically changed by the mutation engine. Each rule specifies:

- **Parameter**: Which state parameter to modify
- **Weight**: How likely this rule is to be selected (higher = more frequent)
- **Delta Range**: The range of possible changes
- **Delta Scale**: Multiplier for the delta values
- **Description**: Human-readable description for logging

### The MutationRule Class

```python
@dataclass
class MutationRule:
    parameter: str                           # Parameter name in state
    weight: float = 1.0                     # Selection weight
    delta_range: Tuple[float, float] = (-0.1, 0.1)  # Min/max change
    delta_scale: float = 1.0                # Scale factor for changes
    description: str = ""                   # Description for logs
```

### How Rules Are Applied

1. **Selection**: Rules are selected using weighted random selection
2. **Delta Generation**: A random value is chosen from `delta_range`
3. **Scaling**: The delta is multiplied by `delta_scale`
4. **Application**: The scaled delta is added to the current parameter value
5. **Validation**: The state system validates and clamps the result

---

## Basic Custom Rules

### Creating a Simple Rule

```python
from mutation import MutationRule

# Create a simple tempo variation rule
tempo_rule = MutationRule(
    parameter="bpm",
    weight=2.0,                    # Higher weight = more likely
    delta_range=(-3.0, 3.0),      # ±3 BPM change
    delta_scale=1.0,               # No scaling
    description="Gentle tempo drift"
)
```

### Adding Rules to the Engine

```python
# Add the rule to a running mutation engine
mutation_engine.add_rule(tempo_rule)

# Or add multiple rules at once
rules = [tempo_rule, density_rule, swing_rule]
for rule in rules:
    mutation_engine.add_rule(rule)
```

### Removing Rules

```python
# Remove a rule by parameter name
success = mutation_engine.remove_rule("bpm")
if success:
    print("Rule removed successfully")
else:
    print("Rule not found")
```

---

## Advanced Rule Patterns

### 1. Probability-Based Rules

Rules that affect the likelihood of events occurring:

```python
# Rule that varies note probability
note_prob_rule = MutationRule(
    parameter="note_probability",
    weight=2.5,
    delta_range=(-0.03, 0.03),     # Small changes for stability
    delta_scale=1.0,
    description="Note probability variance"
)

# Rule for step trigger probability  
step_prob_rule = MutationRule(
    parameter="step_probability",
    weight=1.8,
    delta_range=(-0.05, 0.05),
    delta_scale=1.0,
    description="Step trigger probability shift"
)
```

### 2. Audio Effect Rules

Rules that modify synthesis parameters:

```python
# Filter cutoff with larger deltas for audible changes
filter_rule = MutationRule(
    parameter="filter_cutoff",
    weight=2.0,
    delta_range=(-8.0, 8.0),       # Larger range for audio params
    delta_scale=1.0,
    description="Filter cutoff sweep"
)

# Reverb with asymmetric range (favor increases)
reverb_rule = MutationRule(
    parameter="reverb_mix",
    weight=1.5,
    delta_range=(-2.0, 5.0),       # Asymmetric: less likely to reduce
    delta_scale=1.0,
    description="Reverb depth variation"
)

# Distortion with careful bounds
distortion_rule = MutationRule(
    parameter="distortion_amount",
    weight=1.0,
    delta_range=(-0.1, 0.15),      # Gentle distortion changes
    delta_scale=1.0,
    description="Subtle distortion variation"
)
```

### 3. Rhythmic Pattern Rules

Rules affecting timing and rhythm:

```python
# Swing with tight bounds for musicality
swing_rule = MutationRule(
    parameter="swing",
    weight=1.5,
    delta_range=(-0.02, 0.02),     # Tight bounds for musicality
    delta_scale=1.0,
    description="Swing feel adjustment"
)

# Sequence length changes
length_rule = MutationRule(
    parameter="sequence_length",
    weight=0.8,                    # Lower weight for structural changes
    delta_range=(-1, 2),           # Favor increasing length
    delta_scale=1.0,
    description="Sequence length evolution"
)
```

### 4. Conditional Rules

Rules that only apply under certain conditions:

```python
class ConditionalMutationRule(MutationRule):
    """A mutation rule that only applies when conditions are met."""
    
    def __init__(self, condition_func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.condition_func = condition_func
    
    def should_apply(self, state):
        """Check if this rule should be applied."""
        return self.condition_func(state)

# Example: Only mutate reverb when density is high
def high_density_condition(state):
    return state.get("density", 0) > 0.7

conditional_reverb = ConditionalMutationRule(
    condition_func=high_density_condition,
    parameter="reverb_mix",
    weight=2.0,
    delta_range=(0, 8.0),          # Only increases when density is high
    description="Reverb boost during dense sections"
)
```

### 5. Linked Parameter Rules

Rules that affect multiple parameters simultaneously:

```python
class LinkedMutationRule:
    """Rule that affects multiple parameters together."""
    
    def __init__(self, rules, description=""):
        self.rules = rules
        self.description = description
    
    def apply(self, mutation_engine):
        """Apply all linked rules together."""
        for rule in self.rules:
            mutation_engine._apply_mutation(rule)

# Example: Ambient mode - reduce density and increase reverb together
ambient_rules = LinkedMutationRule([
    MutationRule("density", weight=0, delta_range=(-0.1, -0.05)),
    MutationRule("reverb_mix", weight=0, delta_range=(3.0, 8.0)),
    MutationRule("filter_cutoff", weight=0, delta_range=(-15.0, -5.0))
], description="Ambient atmosphere shift")
```

---

## Configuration and Deployment

### Method 1: Runtime Addition

Add rules while the engine is running:

```python
# In your application code
def add_custom_rules(mutation_engine):
    """Add custom rules to the mutation engine."""
    
    # Harmonic tension rule
    tension_rule = MutationRule(
        parameter="harmonic_tension",
        weight=1.2,
        delta_range=(-0.08, 0.12),    # Favor increasing tension
        delta_scale=1.0,
        description="Harmonic tension evolution"
    )
    
    # Rhythmic complexity rule
    complexity_rule = MutationRule(
        parameter="rhythmic_complexity",
        weight=0.8,
        delta_range=(-0.05, 0.1),     # Gradual complexity increase
        delta_scale=1.0,
        description="Rhythmic pattern complexity"
    )
    
    mutation_engine.add_rule(tension_rule)
    mutation_engine.add_rule(complexity_rule)

# Use it in main.py
add_custom_rules(mutation_engine)
```

### Method 2: Plugin System

Create a plugin file for custom rules:

```python
# custom_rules.py
"""Custom mutation rules plugin."""

from mutation import MutationRule

def get_custom_rules():
    """Return a list of custom mutation rules."""
    return [
        MutationRule(
            parameter="ambient_level",
            weight=1.0,
            delta_range=(-0.05, 0.08),
            description="Ambient atmosphere level"
        ),
        MutationRule(
            parameter="texture_density", 
            weight=1.5,
            delta_range=(-0.1, 0.1),
            description="Textural density variation"
        ),
        MutationRule(
            parameter="spectral_tilt",
            weight=0.7,
            delta_range=(-0.03, 0.03),
            description="Spectral tilt adjustment"
        )
    ]

def register_rules(mutation_engine):
    """Register all custom rules with the engine."""
    for rule in get_custom_rules():
        mutation_engine.add_rule(rule)
```

### Method 3: Configuration File Extension

Extend the YAML configuration to include custom rules:

```yaml
# config.yaml
mutation:
  interval_min_s: 120
  interval_max_s: 240
  max_changes_per_cycle: 2
  
  # Custom rules section
  custom_rules:
    - parameter: "pad_volume"
      weight: 1.5
      delta_range: [-3.0, 5.0]
      delta_scale: 1.0
      description: "Pad volume breathing"
      
    - parameter: "bass_presence"
      weight: 2.0
      delta_range: [-0.1, 0.15]
      delta_scale: 1.0
      description: "Bass presence variation"
      
    - parameter: "stereo_width"
      weight: 0.8
      delta_range: [-0.05, 0.05]
      delta_scale: 1.0
      description: "Stereo field width"
```

Then load them in your configuration handler:

```python
# config.py extension
class CustomRuleConfig(BaseModel):
    parameter: str
    weight: float = 1.0
    delta_range: List[float] = [-0.1, 0.1]
    delta_scale: float = 1.0
    description: str = ""

class MutationConfig(BaseModel):
    interval_min_s: int = 120
    interval_max_s: int = 240
    max_changes_per_cycle: int = 2
    custom_rules: List[CustomRuleConfig] = []

def load_custom_rules(config, mutation_engine):
    """Load custom rules from configuration."""
    for rule_config in config.mutation.custom_rules:
        rule = MutationRule(
            parameter=rule_config.parameter,
            weight=rule_config.weight,
            delta_range=tuple(rule_config.delta_range),
            delta_scale=rule_config.delta_scale,
            description=rule_config.description
        )
        mutation_engine.add_rule(rule)
```

---

## Testing Custom Rules

### Unit Testing

Create tests for your custom rules:

```python
# test_custom_rules.py
import pytest
from mutation import MutationRule, MutationEngine
from state import State
from config import MutationConfig

class TestCustomRules:
    
    @pytest.fixture
    def state_with_custom_params(self):
        """State with custom parameters."""
        state = State()
        state.set("ambient_level", 0.5)
        state.set("texture_density", 0.3)
        state.set("harmonic_tension", 0.6)
        return state
    
    def test_ambient_level_rule(self, state_with_custom_params):
        """Test ambient level mutation rule."""
        rule = MutationRule(
            parameter="ambient_level",
            weight=1.0,
            delta_range=(-0.1, 0.1),
            description="Test ambient rule"
        )
        
        config = MutationConfig(max_changes_per_cycle=1)
        engine = MutationEngine(config, state_with_custom_params)
        engine.add_rule(rule)
        
        initial_value = state_with_custom_params.get("ambient_level")
        engine._apply_mutation(rule)
        final_value = state_with_custom_params.get("ambient_level")
        
        # Should have changed within expected range
        assert abs(final_value - initial_value) <= 0.1
        
    def test_rule_bounds_respected(self, state_with_custom_params):
        """Test that custom rules respect parameter bounds."""
        # Add parameter with custom validation to state
        def validate_texture_density(value):
            return max(0.0, min(1.0, float(value)))
        
        # Set up state validation (this would be in your State class)
        state_with_custom_params._validate_param = lambda p, v: validate_texture_density(v) if p == "texture_density" else v
        
        rule = MutationRule(
            parameter="texture_density",
            delta_range=(0.8, 1.0),  # Large positive delta
            description="Test bounds rule"
        )
        
        config = MutationConfig(max_changes_per_cycle=1)
        engine = MutationEngine(config, state_with_custom_params)
        
        # Apply rule multiple times
        for _ in range(10):
            engine._apply_mutation(rule)
            value = state_with_custom_params.get("texture_density")
            assert 0.0 <= value <= 1.0  # Should stay in bounds
```

### Integration Testing

Test how custom rules work with the whole system:

```python
def test_custom_rules_integration():
    """Test custom rules in complete system."""
    # Set up full system with custom rules
    config = MutationConfig(
        interval_min_s=1,
        interval_max_s=2,
        max_changes_per_cycle=2
    )
    
    state = State()
    engine = MutationEngine(config, state)
    
    # Add custom rules
    custom_rules = [
        MutationRule("custom_param1", weight=1.0, delta_range=(-0.1, 0.1)),
        MutationRule("custom_param2", weight=2.0, delta_range=(-0.2, 0.2)),
        MutationRule("custom_param3", weight=0.5, delta_range=(-0.05, 0.05))
    ]
    
    for rule in custom_rules:
        state.set(rule.parameter, 0.5)  # Set initial values
        engine.add_rule(rule)
    
    # Force mutations and check behavior
    initial_history_len = len(engine.get_history())
    engine.force_mutation()
    
    assert len(engine.get_history()) > initial_history_len
    
    # Check that custom parameters can be mutated
    history = engine.get_history()
    custom_params_mutated = [event.parameter for event in history 
                           if event.parameter.startswith("custom_")]
    assert len(custom_params_mutated) > 0
```

---

## Best Practices

### 1. Parameter Naming

Use clear, hierarchical naming for custom parameters:

```python
# Good naming patterns
"synth.filter.cutoff"
"rhythm.complexity.level"
"ambient.reverb.size"
"texture.grain.density"

# Avoid generic names
"param1", "value", "setting"
```

### 2. Weight Selection

Choose weights thoughtfully based on impact:

```python
# High impact, frequent changes
density_rule = MutationRule("density", weight=3.0, ...)

# Medium impact, moderate frequency
filter_rule = MutationRule("filter_cutoff", weight=2.0, ...)

# Structural changes, infrequent
structure_rule = MutationRule("sequence_length", weight=0.5, ...)
```

### 3. Delta Range Guidelines

Size delta ranges appropriately for each parameter type:

```python
# Percentage parameters (0-1): small deltas
MutationRule("density", delta_range=(-0.05, 0.05))

# MIDI values (0-127): medium deltas  
MutationRule("filter_cutoff", delta_range=(-8.0, 8.0))

# Tempo: moderate deltas
MutationRule("bpm", delta_range=(-3.0, 3.0))

# Timing: very small deltas
MutationRule("swing", delta_range=(-0.02, 0.02))
```

### 4. Musical Considerations

Keep musicality in mind:

```python
# Favor musically pleasing directions
reverb_rule = MutationRule(
    "reverb_mix", 
    delta_range=(-2.0, 5.0)  # Easier to add than remove reverb
)

# Avoid extreme changes in sensitive parameters
pitch_rule = MutationRule(
    "transpose", 
    delta_range=(-1, 1),     # Small semitone steps only
    weight=0.3               # Infrequent pitch changes
)
```

### 5. Performance Considerations

- **Limit the number of rules**: More rules = more processing time
- **Use appropriate weights**: Avoid too many high-weight rules
- **Consider parameter validation cost**: Complex validation slows mutations
- **Monitor memory usage**: Keep rule descriptions concise

---

## Troubleshooting

### Common Issues

**1. Rule Never Selected**
```python
# Problem: Weight too low or parameter doesn't exist
rule = MutationRule("nonexistent_param", weight=0.1)

# Solution: Check parameter exists and increase weight
state.set("custom_param", 0.5)  # Ensure parameter exists
rule = MutationRule("custom_param", weight=1.0)  # Reasonable weight
```

**2. No Visible Changes**
```python
# Problem: Delta range too small
rule = MutationRule("volume", delta_range=(-0.001, 0.001))

# Solution: Increase delta range for noticeable changes
rule = MutationRule("volume", delta_range=(-2.0, 2.0))
```

**3. Values Getting Stuck at Bounds**
```python
# Problem: Delta always pushes to same bound
rule = MutationRule("density", delta_range=(0.1, 0.2))  # Always increases

# Solution: Use symmetric or appropriate ranges
rule = MutationRule("density", delta_range=(-0.1, 0.1))  # Bidirectional
```

**4. Rules Interfering with Each Other**
```python
# Problem: Multiple rules affecting same parameter
rule1 = MutationRule("bpm", weight=2.0, delta_range=(-5, 5))
rule2 = MutationRule("bpm", weight=2.0, delta_range=(-3, 3))

# Solution: Combine into single rule or use different parameters
bpm_rule = MutationRule("bpm", weight=2.0, delta_range=(-5, 5))
```

### Debugging Tools

**Check Rule Registration**:
```python
# List all active rules
for rule in mutation_engine._rules:
    print(f"{rule.parameter}: weight={rule.weight}, range={rule.delta_range}")
```

**Monitor Rule Selection**:
```python
# Enable debug logging to see which rules are selected
import logging
logging.getLogger("mutation").setLevel(logging.DEBUG)
```

**Track Parameter Changes**:
```python
# Add state listener to monitor all changes
def debug_changes(change):
    print(f"Parameter {change.parameter}: {change.old_value} -> {change.new_value}")

state.add_listener(debug_changes)
```

---

## Examples

### Example 1: Ambient Music Generator

```python
def create_ambient_rules():
    """Rules for ambient music generation."""
    return [
        # Slow, gentle changes to create evolving atmosphere
        MutationRule(
            "pad_volume",
            weight=2.0,
            delta_range=(-2.0, 3.0),
            description="Pad volume breathing"
        ),
        MutationRule(
            "reverb_size",
            weight=1.5,
            delta_range=(-0.05, 0.1),
            description="Reverb space evolution"
        ),
        MutationRule(
            "filter_resonance",
            weight=1.0,
            delta_range=(-0.02, 0.03),
            description="Filter resonance shimmer"
        ),
        MutationRule(
            "stereo_width",
            weight=0.8,
            delta_range=(-0.03, 0.05),
            description="Stereo field breathing"
        )
    ]
```

### Example 2: Techno Pattern Evolution

```python
def create_techno_rules():
    """Rules for techno pattern evolution."""
    return [
        # Rhythmic emphasis
        MutationRule(
            "kick_emphasis",
            weight=3.0,
            delta_range=(-0.1, 0.15),
            description="Kick drum emphasis"
        ),
        MutationRule(
            "hihat_shuffle",
            weight=2.5,
            delta_range=(-0.05, 0.05),
            description="Hi-hat shuffle amount"
        ),
        # Filter sweeps
        MutationRule(
            "filter_cutoff",
            weight=2.0,
            delta_range=(-12.0, 12.0),
            description="Filter sweep movement"
        ),
        # Acid-style resonance
        MutationRule(
            "acid_resonance",
            weight=1.5,
            delta_range=(-0.08, 0.12),
            description="Acid resonance variation"
        )
    ]
```

### Example 3: Jazz Harmony Evolution

```python
def create_jazz_rules():
    """Rules for jazz harmony evolution."""
    return [
        # Harmonic complexity
        MutationRule(
            "chord_extensions",
            weight=1.8,
            delta_range=(-0.1, 0.1),
            description="Chord extension density"
        ),
        MutationRule(
            "voice_leading_tension",
            weight=1.5,
            delta_range=(-0.05, 0.08),
            description="Voice leading tension"
        ),
        # Rhythmic sophistication
        MutationRule(
            "syncopation_level",
            weight=2.0,
            delta_range=(-0.03, 0.05),
            description="Syncopation complexity"
        ),
        MutationRule(
            "comp_sparsity",
            weight=1.2,
            delta_range=(-0.08, 0.05),
            description="Comping sparsity"
        )
    ]
```

---

## Conclusion

The mutation engine's extensibility allows for unlimited creative possibilities. By understanding the core concepts and following the patterns outlined in this guide, you can create custom rules that bring your unique musical vision to life in the Mystery Music Station.

Remember to:
- Start with simple rules and gradually add complexity
- Test thoroughly to ensure musical results
- Monitor performance impact of custom rules
- Document your rules for future reference
- Share interesting rules with the community

Happy mutating! 🎵✨
