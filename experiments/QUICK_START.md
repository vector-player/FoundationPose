# Quick Start Guide: Mask Tracking Investigation

## Quick Test

To quickly test if masks improve tracking:

```bash
cd /root/FoundationPose
python experiments/compare_mask_tracking.py \
    --inputs ./user/mustard0_rgb/inputs \
    --outputs ./experiments/results/test_run
```

## What Gets Compared

The script runs tracking **twice** on the same sequence:
1. **Baseline**: Without masks (current behavior)
2. **Experimental**: With masks (new behavior)

## Understanding Results

### Positive Improvement = Masks Help
- Translation variance improvement > 0: More stable translation
- Rotation variance improvement > 0: More stable rotation
- Pose error improvement > 0: More accurate poses

### Negative Improvement = Masks Hurt
- May indicate poor mask quality
- May indicate masks are too restrictive
- Consider mask quality check

### Near-Zero = Minimal Effect
- Masks don't significantly impact tracking
- May not be worth the computational cost

## Expected Output

```
TRACKING COMPARISON RESULTS
======================================================================
Number of frames: 100

Stability Comparison:
  translation_variance_improvement: 0.000123
  rotation_variance_improvement: 0.045678
  frame_to_frame_trans_improvement: 0.000012
  frame_to_frame_rot_improvement: 0.001234

Pose Error Comparison:
  Translation error (no mask): 0.012345 m
  Translation error (with mask): 0.011234 m
  Translation improvement: 0.001111 m
  ...
```

## Troubleshooting

### "Mask not available for frame X"
- Some frames may not have masks
- Script falls back to tracking without masks
- Check mask directory structure

### "Very few valid points after mask filtering"
- Mask may be too restrictive
- Check mask quality
- Consider mask dilation

### No improvement detected
- May be normal for some sequences
- Masks may not help in all scenarios
- Check if masks are accurate

## Next Steps

1. Review `comparison_results.json` for detailed metrics
2. Check debug visualizations in `debug_no_mask/` and `debug_with_mask/`
3. Compare pose sequences: `poses_no_mask.npy` vs `poses_with_mask.npy`
4. Analyze when masks help vs. hurt
