# BENCH PRESS vs SQUAT - Quick Comparison Guide

## Pattern Recognition

### ✅ SAME
- Eccentric → Bottom → Concentric phase structure
- Magnitude drops during descent
- Clear minima at bottom position
- Return to baseline after rep
- Velocity-based phase detection works
- Gaussian smoothing (sigma=2) optimal

### ⚠️ DIFFERENT

| Aspect | Squat | Bench Press |
|--------|-------|-------------|
| **Baseline Magnitude** | ~1.0g (standing) | ~0.976g (lockout) |
| **Movement Plane** | Vertical | Horizontal |
| **ROM (magnitude drop)** | ~0.5-0.7g | ~0.36g |
| **Bottom Magnitude** | ~0.3-0.5g | ~0.45-0.87g |
| **Concentric Peaks** | Lower | Higher (1.0-1.46g) |
| **Impact Events** | Possible | NO |
| **Rep Duration** | 2-4s | 1-3s |
| **Depth Consistency** | More consistent | More variable |
| **Dominant Axis** | Y (gravity) | Y (bar path) |

## Configuration Changes Needed

```python
# FROM SQUAT:
BASELINE_MAG_MEAN = 1.000  # Standing position
BOTTOM_THRESHOLD = 0.500
MIN_REP_DURATION = 2.0

# TO BENCH PRESS:
BASELINE_MAG_MEAN = 0.976  # Lockout position
BOTTOM_THRESHOLD = 0.870
MIN_REP_DURATION = 1.0
```

## Terminology Updates

| Squat | Bench Press |
|-------|-------------|
| Standing | Lockout |
| Descent | Eccentric |
| Bottom | Chest Touch |
| Ascent | Concentric Press |

## Detection Reliability

**Both exercises**: HIGH reliability
- Squat: ✓✓✓✓✓ (5/5)
- Bench Press: ✓✓✓✓✓ (5/5)

**Suitable for**:
- ✅ Rep counting
- ✅ Form analysis
- ✅ Real-time feedback
- ✅ Velocity-based training
- ✅ Fatigue monitoring

## Notebook Adaptation Strategy

1. **Copy** `squat_analysis.ipynb` → `benchpress_analysis.ipynb`
2. **Update** thresholds (baseline, bottom, timing)
3. **Rename** phases (Standing→Lockout, etc.)
4. **Remove** impact event detection
5. **Add** power analysis (concentric peaks)
6. **Adjust** visualization labels
7. **Test** with bench press data

**Result**: ✅ DONE - `benchpress_analysis.ipynb` ready!
