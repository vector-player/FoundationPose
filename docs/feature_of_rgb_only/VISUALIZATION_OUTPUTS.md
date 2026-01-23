# RGB-Only Mode Visualization Outputs

## Overview

When running RGB-only mode with `--debug 2` or higher, the system generates visualization outputs that can be used to verify the pose estimation results.

## Generated Files

### 1. Tracking Visualization Images
**Location**: `debug/track_vis/*.png`

- **Count**: One image per frame (711-737 images depending on dataset)
- **Content**: RGB image with overlaid:
  - 3D bounding box of the object
  - Coordinate axes (RGB = XYZ)
  - Pose visualization
- **Purpose**: Visual verification of pose estimation and tracking quality
- **Size**: ~300KB per image

**Example**: `debug/track_vis/1581120424100262102.png`

### 2. Registration Visualization
**Location**: `debug/vis_refiner.png` and `debug/vis_score.png`

- **vis_refiner.png**: Visualization of pose refinement process
  - Shows multiple pose hypotheses
  - Size: ~21MB
- **vis_score.png**: Visualization of pose scoring
  - Shows how poses are ranked
  - Size: ~5MB

### 3. Input Data Visualizations
**Location**: `debug/`

- **color.png**: Input RGB image (first frame)
- **ob_mask.png**: Object mask used for registration
- **scene_raw.ply**: Point cloud from raw depth (empty in RGB-only mode)
- **scene_complete.ply**: Complete scene point cloud (mask-based in RGB-only mode)
- **init_center.ply**: Initial translation estimate point

### 4. Pose Files
**Location**: `debug/ob_in_cam/*.txt`

- **Format**: 4x4 transformation matrices (one per frame)
- **Content**: Object pose in camera coordinates
- **Count**: One file per frame (711-737 files)

## How to View Visualizations

### Option 1: View Individual Images
```bash
# View a specific tracking visualization
eog debug/track_vis/1581120424100262102.png

# Or use any image viewer
feh debug/track_vis/*.png
```

### Option 2: Create Animation/GIF
```bash
# Create a GIF from tracking visualizations
cd debug/track_vis
convert -delay 10 -loop 0 *.png tracking_animation.gif
```

### Option 3: View Point Clouds
```bash
# View point cloud files (if available)
meshlab debug/scene_complete.ply
# or
cloudcompare debug/scene_complete.ply
```

### Option 4: Python Script to View
```python
import matplotlib.pyplot as plt
import imageio
import glob

# View first few tracking visualizations
vis_files = sorted(glob.glob('debug/track_vis/*.png'))[:10]
fig, axes = plt.subplots(2, 5, figsize=(15, 6))
for i, img_file in enumerate(vis_files):
    img = imageio.imread(img_file)
    axes[i//5, i%5].imshow(img)
    axes[i//5, i%5].set_title(f'Frame {i}')
    axes[i//5, i%5].axis('off')
plt.tight_layout()
plt.savefig('rgb_only_tracking_samples.png')
plt.show()
```

## What to Look For in Visualizations

### Tracking Visualization (track_vis/*.png)

**Good Results**:
- ✅ Bounding box aligns well with object
- ✅ Coordinate axes point in correct directions
- ✅ Smooth tracking across frames (no jumps)
- ✅ Consistent pose estimates

**Potential Issues**:
- ⚠️ Bounding box misaligned → pose estimation may need more iterations
- ⚠️ Large jumps between frames → tracking may have failed
- ⚠️ Coordinate axes pointing wrong direction → rotation estimation issue

### Registration Visualization (vis_refiner.png, vis_score.png)

**Good Results**:
- ✅ Multiple pose hypotheses visible
- ✅ Clear best pose selection
- ✅ Consistent scoring

## Sample Visualization Analysis

Based on the runtime test:

```
Total visualization images: 711
Average image size: ~300KB
Total visualization data: ~213MB

Frame distribution:
- Registration: 1 frame (frame 0)
- Tracking: 710 frames (frames 1-710)
```

## Debug Levels

| Debug Level | Outputs Generated |
|-------------|-------------------|
| `--debug 0` | Pose files only (`ob_in_cam/*.txt`) |
| `--debug 1` | Pose files + real-time display (requires X11) |
| `--debug 2` | Pose files + saved visualization images (`track_vis/*.png`) |
| `--debug 3` | All of above + mesh files (`model_tf.obj`, `scene_complete.ply`) |

## RGB-Only Mode Specific Notes

### Differences from Depth-Based Mode

1. **Point Clouds**: 
   - `scene_raw.ply` will be empty or minimal (no depth data)
   - `scene_complete.ply` uses mask-based points only

2. **Depth Images**: 
   - No `depth.png` saved in RGB-only mode (depth is zero)

3. **Visualization Quality**:
   - Tracking visualizations should look similar to depth-based mode
   - May show slightly less accurate bounding boxes (especially for translation)

## Verification Checklist

When reviewing visualizations, verify:

- [ ] Tracking visualizations show object bounding box
- [ ] Bounding boxes are reasonably aligned with objects
- [ ] No large jumps between consecutive frames
- [ ] Coordinate axes are visible and consistent
- [ ] Pose files are generated for all frames
- [ ] No obvious tracking failures

## Example Command to Generate Visualizations

```bash
# Generate full visualization set
python run.py --rgb_only \
  --mesh_file demo_data/mustard0/mesh/textured_simple.obj \
  --test_scene_dir demo_data/mustard0 \
  --debug 2 \
  --est_refine_iter 5 \
  --track_refine_iter 2
```

This will generate:
- 711+ tracking visualization images
- Registration visualizations
- All pose files
- Debug point clouds and masks

## Summary

✅ **Visualization outputs are available** when running with `--debug 2` or higher.

The runtime test generated:
- **711 tracking visualization images** showing pose estimation results
- **Registration visualizations** showing the pose selection process
- **All input data visualizations** for debugging
- **711 pose files** with transformation matrices

These visualizations can be used to verify that RGB-only mode is working correctly and producing reasonable pose estimates.
