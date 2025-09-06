
# Fugue Mode — Implementation Guide for a Generative Sequencer (Python)

**Audience:** An AI agent implementing a *fugue mode* in an existing Python-based generative music system.  
**Goal:** Generate contrapuntal fugues from a single **Subject**, using deterministic transformations, overlap logic (exposition, episodes, stretto), and counterpoint constraints.

---

## 0. Quick Glossary

- **Subject**: Primary melody to be imitated.
- **Answer (Real/Tonal)**: Subject transposed to the dominant (P5) or adjusted (tonal) to preserve key.
- **Countersubject**: A line that consistently accompanies the subject.
- **Exposition**: Initial round of entries, one per voice.
- **Episode**: Developmental passage using fragments/sequences of the subject.
- **Stretto**: Overlap where later entries begin before earlier ones have ended.
- **Augmentation/Diminution**: Time scaling of note values.
- **Inversion/Retrograde**: Pitch inversion and time-reversal of the subject.
- **Voices**: Independent monophonic lines (e.g., S, A, T, B).

---

## 1. Data Model

### 1.1 Pitch/Time Representation
Use MIDI integers for absolute pitch (recommended) and quarter-note units for duration:
```python
Note = TypedDict("Note", {"pitch": int, "dur": float, "vel": int})
Phrase = list[Note]          # monophonic sequence
Score = list[Phrase]         # list of voices
```
Grid resolution: choose at least 1/16 (0.25 quarters).

### 1.2 Subject
```python
Subject: Phrase    # melody in the home key (key_root, scale_mode)
key = {"root": 60, "mode": "minor"}  # example: C minor, root MIDI 60
tempo_bpm: float
```

### 1.3 Transformations (Pure Functions)
All functions return a **new** phrase (no mutation).

```python
def transpose(phrase: Phrase, semitones: int) -> Phrase: ...
def invert(phrase: Phrase, axis_pitch: int) -> Phrase: ...
def retrograde(phrase: Phrase) -> Phrase: ...
def time_scale(phrase: Phrase, s: float) -> Phrase: ...  # s>0
def shift_time(phrase: Phrase, offset_quarters: float) -> Phrase: ...
def slice_by_time(phrase: Phrase, t0: float, t1: float) -> Phrase: ...
```

**Axis for inversion**: choose tonic or median of subject range.  
**Velocity policy**: preserve; allow a global scaling parameter per voice.

---

## 2. Answer Logic

### 2.1 Real Answer (P5)
Transposition by +7 semitones from the subject’s first note (dominant).

### 2.2 Tonal Answer (Recommended Default)
Prevent early modulation by adjusting specific intervals at the beginning.

Algorithm (simplified practical rule):
1. Compute interval sequence `Δ = [p[i+1]-p[i] for i]` of the subject’s first measure (or first motif, e.g., up to a cadence or 1–2 beats).
2. Map the **first** tonic-to-dominant motion (`+7`) to **+5** only when it occurs while tonic harmony is implied.
3. Reconstruct the answered pitch line relative to the dominant entry note.

Provide a hook for scale-degree-aware refinement using the current key signature.

```python
def tonal_answer(subject: Phrase, key_root: int) -> Phrase:
    # start on dominant (key_root + 7) but correct the first +7 leap in Δ to +5
    ...
```
```

---

## 3. Voices and Entry Scheduling

### 3.1 Exposition Template
For `V` voices (2–4 typical):
- `V1`: Subject at time `t=0` in **tonic**.
- `V2`: Answer at `t = entry_gap` in **dominant** (real or tonal).
- `V3`: Subject at `t = 2*entry_gap` in **tonic**.
- `V4`: Answer at `t = 3*entry_gap` in **dominant**.

`entry_gap` defaults to subject length or a musical unit (e.g., 1–2 beats) for stretto-like expositions.

### 3.2 Countersubject (Optional)
If provided, render it whenever the subject/answer is present in another voice. Keep it **invertible** (counterpoint-safe above or below).

```python
class Entry(TypedDict):
    voice_index: int
    start_time: float
    material: Phrase  # a transformed subject or countersubject
```
```

---

## 4. Episodes and Development

Episodes are generated from **fragments** of the subject using sequences/transpositions.

**Recipe:**
- Choose a fragment `F = slice_by_time(subject, t0, t1)`.
- Build a **sequence** through the circle of fifths or diatonic degrees:
  - transpositions: `[+2, +2, +2]` (up by step) or `[+7, +7]` (up by fifths).
- Optionally apply inversion or diminution and distribute across voices with **canonic imitation**.

```python
def make_sequence(fragment: Phrase, steps: list[int], step_len_beats: float) -> Phrase: ...
```
```

Include a cadence/half-cadence generator to prepare the next **subject re-entry**.

---

## 5. Stretto

**Definition:** later entries begin before earlier entries end.  
Parameterize by **overlap ratio** \(\rho \in [0,1]\): start the next entry at `t = current_start + (1-ρ)*subject_len`.

- `ρ=0`: no overlap (standard exposition).
- `ρ≈0.5`: classic stretto feel.
- `ρ>0.7`: dense canonic web (use stricter counterpoint checks).

---

## 6. Counterpoint Constraints (Scoring)

Evaluate on a fixed time grid (e.g., 1/16). For each adjacent pair of grid times `k,k+1` and each unordered voice pair `(i,j)` compute vertical intervals modulo 12.

### 6.1 Hard Constraints
- **No exact unison on consecutive onsets** between different voices except at cadences.
- **Range** per voice: configurable `[min_pitch, max_pitch]`.
- **Max leap**: e.g., ≤ 9 semitones (except at cadences).

### 6.2 Soft Constraints (Cost Terms)
- **Parallel perfects** (P8/P5): strong penalty when same directed motion.
- **Direct perfects** (hidden fifths/octaves on strong beats): medium penalty.
- **Dissonance on strong beats** unless prepared/resolved: penalty.
- **Voice crossing/overlap**: penalty unless allowed.
- **Rhythmic independence**: reward off-beat entries and syncopation variety.
- **Contour smoothness**: reward stepwise motion.

Total score:
\(
J = \sum w_{\text{par}} C_{\text{par}} + w_{\text{dir}} C_{\text{dir}} + w_{\text{diss}} C_{\text{diss}} + w_{\text{cross}} C_{\text{cross}} + w_{\text{smooth}} C_{\text{smooth}} + \cdots
\)

**Search strategy:** greedy with backtracking, beam search, or ILP/MIP for small problems. Provide a time budget parameter.

---

## 7. API Contract (Minimal)

```python
@dataclass
class FugueParams:
    n_voices: int = 3
    key_root: int = 60          # tonic MIDI (e.g., 60 = C4)
    mode: str = "minor"
    entry_gap_beats: float | None = None  # default: subject length
    stretto_overlap: float = 0.0          # 0..1
    use_tonal_answer: bool = True
    allow_inversion: bool = False
    allow_retrograde: bool = False
    allow_augmentation: bool = False
    allow_diminution: bool = False
    episode_density: float = 0.5          # 0..1
    cadence_every_measures: int = 4
    # Counterpoint weights:
    w_parallel: float = 5.0
    w_direct: float = 2.5
    w_disson: float = 3.0
    w_cross: float = 1.0
    w_smooth: float = -1.0                 # negative rewards (lower is better)
    # Ranges per voice (relative to tonic); implement sensible defaults per voice
    ranges: list[tuple[int,int]] | None = None
```
```

### 7.1 Core Function
```python
def render_fugue(subject: Phrase, params: FugueParams) -> Score:
    """
    Returns a Score (list[Phrase]) of n_voices.
    Steps:
      1) Build entry plan (exposition) using tonal/real answers.
      2) Interleave countersubject if provided; else auto-generate a species-style line.
      3) Insert episodes based on fragments + sequences; add cadences.
      4) Optionally add stretto sections per params.stretto_overlap.
      5) Optimize with counterpoint scoring; resolve conflicts by adjusting octave, rhythm, or fragment choice.
    """
```
```

---

## 8. Reference Algorithms (Pseudocode)

### 8.1 Entry Plan
```
make_entry_plan(subject_len L, voices V, gap G, overlap ρ):
    if G is None: G = L * (1 - ρ)
    for v in 0..V-1:
        start[v] = v * G
        material[v] = subject if v % 2 == 0 else answer(subject)
    return [Entry(v, start[v], material[v]) for v in voices]
```

### 8.2 Counterpoint Pass (Greedy)
```
for each beat k:
  for each voice v:
    if onset at k in v: continue
    propose {hold, neighbor up, neighbor down, passing tone, rest}
    score each proposal by ΔJ on pairwise constraints at k..k+1
    commit best local move
repeat N passes or until ΔJ < ε
```

### 8.3 Episode Builder
```
choose fragment F from subject by salience (peaks, repeated n-grams)
choose sequence steps S (heuristic from key and mode)
E = concatenate( transpose(F, s) for s in cumulative(S) )
distribute E across voices with shifting offsets for imitation
insert cadence pattern to prepare next tonic/dominant entry
```

---

## 9. Tonal Answer — Practical Mapping

A minimal context-aware mapping for the **opening** scale degrees (minor shown; major analogous):

| Subject Degree | Real Answer (to V) | Tonal Answer |
|---|---|---|
| 1 → 5 leap | +7 | **+5** |
| 5 → 1 | -7 | **-5** |
| 4 → 5 (pre-dominant) | +1 | +1 |
| Leading tone → tonic | +1 | +1 (preserve leading tone function) |

Implement this via a **piecewise transposition** over the first motif; revert to real-transpose afterwards.

---

## 10. Test Vectors

### 10.1 Minimal Subject (C minor, 4 beats)
```python
subject = [
  {"pitch": 60, "dur": 1.0, "vel": 96},  # C
  {"pitch": 67, "dur": 1.0, "vel": 96},  # G (P5)
  {"pitch": 63, "dur": 1.0, "vel": 96},  # Eb
  {"pitch": 65, "dur": 1.0, "vel": 96},  # F
]
```
Expected tonal answer opening on G (pitch 67) with corrected leap to +5 for the first motion.

### 10.2 Stretto Overlap
`stretto_overlap = 0.5` → entry 2 starts at beat 2 when subject length is 4 beats.

### 10.3 Constraint Sanity
- Create two voices moving in the same direction by step to force detection of parallel fifths between C–G and D–A, etc.

---

## 11. Export / Integration

- **MIDI**: render each voice to a separate MIDI channel; preserve articulations.
- **DAW/Host**: expose parameters through your existing sequencer UI.
- **Determinism**: seed the random generator for reproducibility; log the chosen transformations/entries.
- **Callbacks**: provide hooks for user-supplied countersubjects or custom constraint evaluators.

---

## 12. Safety & Failure Modes

- If constraint solver fails, **relax** soft weights and retry; never produce silent output.
- Enforce voice ranges to avoid extreme registers when transposing.
- Limit augmentation/diminution to rational multiples of the grid to prevent drift.

---

## 13. Minimal Reference Implementation Sketch

```python
def render_fugue(subject: Phrase, params: FugueParams) -> Score:
    L = sum(n["dur"] for n in subject)
    G = params.entry_gap_beats or L * (1 - params.stretto_overlap)

    # 1) Build exposition
    voices = [[] for _ in range(params.n_voices)]
    entries = []
    for v in range(params.n_voices):
        start = v * G
        mat = subject if v % 2 == 0 else (
            tonal_answer(subject, params.key_root) if params.use_tonal_answer
            else transpose(subject, +7)
        )
        entries.append({"voice_index": v, "start_time": start, "material": mat})

    # 2) Place entries
    for e in entries:
        voices[e["voice_index"]] += shift_time(e["material"], e["start_time"])

    # 3) Fill gaps with countersubject/episodes (omitted here; use Section 4/8)
    # 4) Constraint pass to polish
    #    (apply penalties, adjust octaves, add passing tones)

    return voices
```
---

## 14. Parameter Defaults (Suggested)

- `n_voices`: 3 for clarity; 4 for richer texture.
- `stretto_overlap`: 0.0 for basic; 0.4–0.6 for dramatic.
- `episode_density`: 0.4 default; 0.7 for complex development.
- `ranges`: e.g., for C minor tonic 60:
  - V1: [72, 88], V2: [65, 81], V3: [57, 74], V4: [48, 67]

---

## 15. Acceptance Criteria

- **A. Structure**: Clear exposition with alternating Subject/Answer; at least one episode; at least one later subject re-entry.
- **B. Constraints**: No blatant parallel fifths/octaves during strong beats in adjacent voices.
- **C. Musicality**: Voices remain in range; reasonable contour; cadential closure.
- **D. Reproducibility**: Same seed → identical fugue; logs list all transformations and timings.

---

## 16. Future Extensions

- Multi-subject fugues (double/triple) with invertible counterpoint tables.
- Learned tonal-answer mapping via scale-degree tagger.
- Constraint solver upgrade to ILP with binary variables per grid cell.
- Style conditioning (Bach-like, Baroque-lite) via learned cost weights.

---

**End of Spec.**
