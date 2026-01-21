# RGB-Only Mode Feature Documentation
An implementation of [plan_of_rgb-only_mode](./rgb-only_mode_implementation_db5c9b16.plan.md)

## Overview

FoundationPose now supports RGB-only mode, allowing pose estimation and tracking without requiring depth sensor data. This feature enables the use of FoundationPose with standard RGB cameras, making it more accessible and applicable to scenarios where depth sensors are unavailable or unreliable.

## Background

This implementation is based on research findings from RGBTrack and related work:

- FoundationPose's RefineNet processes a 6-channel tensor (RGB + 3D point cloud from depth)
- When depth is missing or zero, the network falls back to relying purely on RGB features
- RGBTrack demonstrates that feeding zero-depth matrices into FoundationPose still yields reasonable tracking
- The network treats point-cloud channels as degenerate when depth is zero and operates as an RGB-only relative pose refiner

## Usage

### Command-Line Interface

Enable RGB-only mode using the `--rgb_only` flag:

```bash
python run_demo.py --rgb_only --mesh_file path/to/mesh.obj --test_scene_dir path/to/scene
```

### Programmatic Usage

```python
from estimater import FoundationPose
from datareader import YcbineoatReader

# Initialize estimator with RGB-only mode
scorer = ScorePredictor()
refiner = PoseRefinePredictor()
est = FoundationPose(
    model_pts=mesh.vertices,
    model_normals=mesh.vertex_normals,
    mesh=mesh,
    scorer=scorer,
    refiner=refiner,
    rgb_only_mode=True  # Enable RGB-only mode
)

# Initialize data reader with RGB-only mode
reader = YcbineoatReader(
    video_dir=args.test_scene_dir,
    rgb_only=True  # Enable RGB-only mode
)

# Use normally - depth maps will be automatically set to zero
color = reader.get_color(0)
depth = reader.get_depth(0)  # Returns zero-depth map
mask = reader.get_mask(0)
pose = est.register(K=reader.K, rgb=color, depth=depth, ob_mask=mask)
```

## How It Works

### Implementation Details

1. **Zero-Depth Maps**: When RGB-only mode is enabled, data readers return zero-depth maps (all zeros) instead of loading actual depth images.

2. **Translation Estimation**: Without depth data, translation is estimated using:
   - Mask-based 2D center extraction
   - Mesh diameter/scale to estimate Z coordinate (heuristic: ~2.5x mesh diameter)
   - Camera intrinsics to project 2D center to 3D

3. **Depth Processing**: Depth filtering operations (erosion, bilateral filtering) are skipped when RGB-only mode is enabled.

4. **Network Input**: The network receives RGB (3 channels) + zero xyz_map (3 channels) = 6-channel input. When xyz_map is all zeros, the network automatically falls back to using RGB features only.

5. **xyz_map Generation**: The `depth2xyzmap()` functions correctly handle zero depth, producing zero xyz_map values, which signals the network to use RGB-only features.

### Code Flow

```
RGB-only mode enabled
    ↓
Data reader returns zero-depth map
    ↓
guess_translation() estimates depth from mesh scale
    ↓
Skip depth filtering (erode/bilateral)
    ↓
Generate zero xyz_map from zero depth
    ↓
Network receives RGB + zero xyz_map
    ↓
Network falls back to RGB features only
```

## Limitations and Considerations

### Accuracy

- **Translation Accuracy**: Without depth, translation estimation is less accurate, especially for absolute Z coordinate
- **Scale Ambiguity**: May have issues with absolute scale estimation
- **Initialization**: Registration may require better initial pose estimates or more refinement iterations

### Performance

- **Speed**: Should be similar or slightly faster (no depth processing overhead)
- **Robustness**: May be more sensitive to:
  - Lighting conditions
  - Texture quality
  - Occlusion
  - Similar-looking objects

### Network Training

- Current models were trained with depth data
- Network adapts to zero-depth inputs through its learned fallback behavior
- Future fine-tuning on RGB-only data could improve performance

## Comparison with Depth-Based Mode

| Aspect | Depth-Based Mode | RGB-Only Mode |
|--------|------------------|---------------|
| **Input Requirements** | RGB + Depth | RGB only |
| **Translation Accuracy** | High (metric) | Moderate (relative) |
| **Initialization** | Robust | May need more iterations |
| **Tracking Quality** | Excellent | Good (as shown in RGBTrack) |
| **Hardware Requirements** | RGB-D camera | Standard RGB camera |
| **Use Cases** | Industrial, robotics | Consumer, webcam, mobile |

## Supported Data Readers

RGB-only mode is supported in:

- `YcbineoatReader`
- `BopBaseReader` and all its subclasses:
  - `LinemodOcclusionReader`
  - `LinemodReader`
  - `YcbVideoReader`
  - `TlessReader`
  - `HomebrewedReader`
  - `ItoddReader`
  - `IcbinReader`
  - `TudlReader`

## Example Workflow

```bash
# Standard RGB-D mode
python run_demo.py \
  --mesh_file demo_data/mustard0/mesh/textured_simple.obj \
  --test_scene_dir demo_data/mustard0 \
  --debug 2

# RGB-only mode
python run_demo.py \
  --rgb_only \
  --mesh_file demo_data/mustard0/mesh/textured_simple.obj \
  --test_scene_dir demo_data/mustard0 \
  --debug 2 \
  --est_refine_iter 10  # May need more iterations for better results
```

## Debugging

When `debug >= 1`, the system logs RGB-only mode status:

```
RGB-only mode enabled: depth maps will be set to zero, network will use RGB features only
RGB-only mode: estimating depth as X.XXXX (mesh diameter: Y.YYYY)
RGB-only mode: skipping depth filtering
RGB-only mode: xyz_map is zero, network will use RGB features only
```

## Future Enhancements

Potential improvements for RGB-only mode:

1. **AI-Generated Depth**: Option to use monocular depth estimation networks (e.g., MiDaS, DPT) to generate pseudo-depth maps
2. **Mesh-Based Depth**: Use mesh projection to generate synthetic depth from estimated pose
3. **Hybrid Mode**: Automatically use depth when available, fall back to RGB-only when not
4. **Fine-Tuning**: Train models specifically for RGB-only mode to improve accuracy
5. **Better Translation Estimation**: Improve depth estimation heuristics using mask area, object size, or learned priors

## References

- RGBTrack: Demonstrates zero-depth approach works for FoundationPose-style tracking
- FoundationPose Architecture: Understanding how depth is used in the network
- Network Fallback Behavior: How networks handle zero xyz_map channels

## Troubleshooting

### Issue: Poor pose estimation accuracy
**Solution**: 
- Increase `--est_refine_iter` (try 10-15 iterations)
- Ensure good object mask quality
- Check that mesh scale is correct

### Issue: Translation seems incorrect
**Solution**:
- This is expected - translation estimation without depth is less accurate
- Consider using AI-generated depth or mesh-based depth estimation
- Verify camera intrinsics are correct

### Issue: Network warnings about non-zero xyz_map
**Solution**:
- Check that `rgb_only=True` is passed to both estimator and data reader
- Verify depth maps are actually zero (check debug output)

## Technical Notes

- Zero-depth maps are generated as `np.zeros((H, W), dtype=np.float32)`
- Depth estimation uses heuristic: `estimated_depth = mesh_diameter * 2.5`
- xyz_map verification checks for values > 1e-6 to detect non-zero depth
- All depth filtering is skipped when `rgb_only_mode=True`
