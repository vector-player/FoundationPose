---
name: RGB-only mode implementation
overview: Implement RGB-only mode for FoundationPose that allows pose estimation and tracking without depth maps, using zero-depth fallback approach inspired by RGBTrack research.
todos:
  - id: add-rgb-only-flag
    content: Add rgb_only_mode parameter to FoundationPose class and data readers
    status: completed
  - id: modify-translation-estimation
    content: Modify guess_translation() to work without depth using mesh scale and mask information
    status: completed
  - id: update-data-reader
    content: Modify datareader.py to return zero-depth maps when rgb_only=True
    status: completed
  - id: skip-depth-filtering
    content: Skip depth filtering (erode/bilateral) when in RGB-only mode
    status: completed
  - id: add-cli-argument
    content: Add --rgb_only command-line argument to run.py
    status: completed
  - id: verify-network-input
    content: Verify network input handling works correctly with zero xyz_map (should fall back to RGB)
    status: completed
  - id: add-logging
    content: Add logging to indicate RGB-only mode and zero-depth detection
    status: completed
  - id: create-documentation
    content: Create feature_of_rgb_only.md with usage instructions and limitations
    status: completed
---

# RGB-Only Mode Implementation Plan for FoundationPose
The implementation of this plan is described in [feature_of_rgb_only](./feature_of_rgb_only.md)
## Overview

This plan outlines the implementation of RGB-only mode for FoundationPose, enabling pose estimation and tracking without requiring depth sensor data. The implementation follows the approach demonstrated in RGBTrack research, where zero-depth inputs allow the network to fall back to RGB-only features.

## Background

Based on the research documents:
- FoundationPose's RefineNet processes a 6-channel tensor (RGB + 3D point cloud from depth)
- When depth is missing or zero, the network falls back to relying purely on RGB features
- RGBTrack demonstrates that feeding zero-depth matrices into FoundationPose still yields reasonable tracking
- The network treats point-cloud channels as degenerate when depth is zero and operates as an RGB-only relative pose refiner

## Current Architecture Analysis

### Depth Usage Points

1. **Data Loading** (`datareader.py`):
   - `get_depth()` loads depth images from disk
   - `get_xyz_map()` converts depth to point cloud via `depth2xyzmap()`

2. **Pose Registration** (`estimater.py::register()`):
   - Depth filtering: `erode_depth()`, `bilateral_filter_depth()`
   - Translation estimation: `guess_translation()` uses median depth from mask region
   - xyz_map generation: `depth2xyzmap(depth, K)` creates point cloud
   - Passed to `refiner.predict()` and `scorer.predict()`

3. **Pose Tracking** (`estimater.py::track_one()`):
   - Similar depth processing pipeline
   - xyz_map generation via `depth2xyzmap_batch()`
   - Passed to refiner for pose refinement

4. **Network Input** (`learning/training/predict_pose_refine.py`, `predict_score.py`):
   - Concatenates RGB (3 channels) + xyz_map (3 channels) = 6-channel input
   - `torch.cat([rgbAs, xyz_mapAs], dim=1)` creates input tensor

5. **Translation Initialization** (`estimater.py::guess_translation()`):
   - Uses median depth from masked region to estimate Z coordinate
   - Projects 2D mask center to 3D using depth

## Implementation Strategy

### Phase 1: Core Infrastructure

#### 1.1 Add RGB-Only Mode Flag
- **File**: `estimater.py`
- **Changes**:
  - Add `rgb_only_mode` parameter to `FoundationPose.__init__()`
  - Store as instance variable `self.rgb_only_mode`
  - Default: `False` (backward compatible)

#### 1.2 Modify Data Reader
- **File**: `datareader.py`
- **Changes**:
  - Add `rgb_only` parameter to reader classes (`YcbineoatReader`, etc.)
  - Modify `get_depth()` to return zero-depth map when `rgb_only=True`
  - Zero-depth map: `np.zeros((H, W), dtype=np.float32)`
  - Ensure same resolution as RGB images

#### 1.3 Update Command-Line Interface
- **File**: `run.py`
- **Changes**:
  - Add `--rgb_only` flag (boolean, default=False)
  - Pass flag to estimator and data reader initialization
  - Update help text

### Phase 2: Translation Estimation Without Depth

#### 2.1 Modify guess_translation()
- **File**: `estimater.py`
- **Changes**:
  - Check `self.rgb_only_mode` flag
  - When RGB-only: use mesh diameter and camera intrinsics to estimate depth
  - Fallback strategy:
    - Use mesh bounding box center depth estimate
    - Or use fixed depth based on mesh scale
    - Or use mask-based depth estimation from mesh projection
  - Maintain backward compatibility when depth is available

**Implementation approach**:
```python
def guess_translation(self, depth, mask, K):
    vs, us = np.where(mask > 0)
    if len(us) == 0:
        return np.zeros((3))
    
    uc = (us.min() + us.max()) / 2.0
    vc = (vs.min() + vs.max()) / 2.0
    
    if self.rgb_only_mode:
        # Estimate depth from mesh scale and mask size
        mask_area = mask.sum()
        # Use mesh diameter as depth estimate
        estimated_depth = self.diameter * 2.0  # Rough scale estimate
        # Or: estimate from mask area vs expected object size
    else:
        valid = mask.astype(bool) & (depth >= 0.001)
        if not valid.any():
            return np.zeros((3))
        estimated_depth = np.median(depth[valid])
    
    center = (np.linalg.inv(K) @ np.asarray([uc, vc, 1]).reshape(3, 1)) * estimated_depth
    return center.reshape(3)
```

### Phase 3: Depth Processing Pipeline

#### 3.1 Handle Zero-Depth in Processing Functions
- **File**: `estimater.py`
- **Changes**:
  - Modify `register()` and `track_one()` to skip depth filtering when RGB-only
  - Skip `erode_depth()` and `bilateral_filter_depth()` calls when depth is all zeros
  - Or make these functions handle zero-depth gracefully (no-op)

#### 3.2 xyz_map Generation
- **File**: `Utils.py`
- **Changes**:
  - `depth2xyzmap()` already handles zero depth correctly (returns zeros)
  - `depth2xyzmap_batch()` also handles zero depth
  - Verify behavior: zero depth → zero xyz_map (all channels zero)
  - This is correct: network will use RGB features only

### Phase 4: Network Input Handling

#### 4.1 Verify Network Compatibility
- **Files**: `learning/training/predict_pose_refine.py`, `predict_score.py`
- **Changes**:
  - Networks already concatenate RGB + xyz_map
  - When xyz_map is all zeros, network falls back to RGB features
  - No changes needed - this is the intended behavior
  - Add logging to indicate RGB-only mode when xyz_map is detected as all zeros

### Phase 5: Registration Initialization

#### 5.1 Modify generate_random_pose_hypo()
- **File**: `estimater.py`
- **Changes**:
  - Check if RGB-only mode affects pose hypothesis generation
  - May need to adjust translation initialization in `register()`
  - Ensure pose hypotheses use estimated depth from `guess_translation()`

### Phase 6: Testing and Validation

#### 6.1 Update Demo Script
- **File**: `run.py`
- **Changes**:
  - Add example usage with `--rgb_only` flag
  - Ensure backward compatibility (default behavior unchanged)

#### 6.2 Documentation
- **File**: Create `feature_of_rgb_only.md`
- **Content**:
  - Usage instructions
  - Limitations and expected accuracy differences
  - Comparison with depth-based mode
  - References to RGBTrack research

## Implementation Details

### Key Files to Modify

1. **`estimater.py`**:
   - Add `rgb_only_mode` parameter
   - Modify `guess_translation()` for depth-free translation estimation
   - Skip depth filtering when RGB-only
   - Add logging for RGB-only mode

2. **`datareader.py`**:
   - Add `rgb_only` parameter to reader classes
   - Modify `get_depth()` to return zeros when RGB-only

3. **`run.py`**:
   - Add `--rgb_only` command-line argument
   - Pass flag through initialization chain

4. **`Utils.py`** (if needed):
   - Verify zero-depth handling in `depth2xyzmap()` functions
   - Add helper function to generate zero-depth maps

### Translation Estimation Strategy

When depth is unavailable, estimate translation using:
1. **Mask-based 2D center**: Extract from object mask
2. **Mesh scale-based depth**: Use mesh diameter/scale to estimate Z
3. **Camera intrinsics**: Project 2D center to 3D with estimated depth

Alternative approaches:
- Use mesh projection to estimate depth from expected object size
- Use multiple depth hypotheses and let refinement handle it
- Use prior knowledge about object scale

### Expected Behavior

- **Registration**: Initial pose estimation works but may be less accurate without depth
- **Tracking**: Sequential tracking should work reasonably well (as shown in RGBTrack)
- **Accuracy**: Expect some degradation compared to depth-based mode, especially for translation
- **Robustness**: May be more sensitive to lighting, texture, and occlusion

## Testing Plan

1. **Unit Tests**:
   - Test zero-depth map generation
   - Test `guess_translation()` with zero depth
   - Test xyz_map generation with zero depth

2. **Integration Tests**:
   - Run `run.py` with `--rgb_only` flag
   - Compare outputs with depth-based mode
   - Verify pose estimation still works

3. **Validation**:
   - Test on datasets with and without depth
   - Measure accuracy degradation
   - Document limitations

## Limitations and Considerations

1. **Translation Accuracy**: Without depth, translation estimation is less accurate
2. **Scale Ambiguity**: May have issues with absolute scale
3. **Initialization**: Registration may require better initial pose estimates
4. **Network Training**: Current models trained with depth; may benefit from RGB-only fine-tuning
5. **Performance**: Should be similar or slightly faster (no depth processing)

## Future Enhancements

1. **AI-Generated Depth**: Option to use monocular depth estimation networks
2. **Mesh-Based Depth**: Use mesh projection to generate synthetic depth
3. **Hybrid Mode**: Use depth when available, fall back to RGB-only when not
4. **Fine-Tuning**: Train models specifically for RGB-only mode

## References

- RGBTrack research showing zero-depth approach works
- FoundationPose architecture understanding depth usage
- Network fallback behavior when xyz_map channels are zero