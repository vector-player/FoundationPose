# Mask Tracking Investigation - Implementation Summary

## Overview

This document summarizes the implementation of mask-based tracking improvements for FoundationPose. The investigation aims to determine whether providing masks for all frames improves tracking quality compared to using masks only during initial registration.

## Implementation Details

### Phase 1: Code Modifications

#### 1.1 Modified `track_one()` Method (`FoundationPose/estimater.py`)

**Changes:**
- Added optional `ob_mask` parameter to `track_one()` method signature
- Implemented mask-based filtering of valid points (similar to registration)
- Added drift detection using mask center comparison
- Implemented translation refinement when drift is detected

**Key Features:**
- **Mask Filtering**: Filters xyz_map using mask to identify valid object points
- **Drift Detection**: Compares current pose translation with mask center
- **Translation Refinement**: If drift > 10% of object diameter, adjusts pose translation towards mask center (30% weight)
- **Backward Compatibility**: Works without masks (ob_mask=None)

**Code Location:** Lines 292-370 in `estimater.py`

#### 1.2 Updated `run.py` Main Loop

**Changes:**
- Modified tracking loop to retrieve masks for all frames (not just frame 0)
- Added error handling for missing masks (falls back to tracking without masks)
- Maintains backward compatibility with datasets that don't have masks for all frames

**Code Location:** Lines 209-226 in `run.py`

**Key Features:**
- Attempts to get mask for each frame during tracking
- Gracefully handles missing masks with fallback behavior
- Logs warnings when masks are unavailable

#### 1.3 Mask-Based Filtering Implementation

**Implementation Details:**
- Mask shape validation and resizing if needed
- Valid point computation: `valid = (xyz_map[...,2]>=0.001) & (ob_mask>0)` for RGB-D mode
- Valid point computation: `valid = (ob_mask > 0)` for RGB-only mode
- Warning when very few valid points detected
- Debug output: saves mask images when debug>=2

### Phase 2: Experimental Setup

#### 2.1 Comparison Script (`experiments/compare_mask_tracking.py`)

**Features:**
- Runs tracking twice on the same sequence:
  1. Without masks (baseline)
  2. With masks (experimental)
- Saves pose sequences and comparison metrics
- Generates detailed JSON report

**Metrics Computed:**
- **Stability Metrics:**
  - Translation variance across frames
  - Rotation variance across frames
  - Frame-to-frame translation changes
  - Frame-to-frame rotation changes

- **Pose Error Metrics** (if GT available):
  - Translation error (meters)
  - Rotation error (degrees)
  - ADD error (Average Distance of Model Points, meters)

**Usage:**
```bash
python experiments/compare_mask_tracking.py \
    --inputs /path/to/input/directory \
    --outputs /path/to/output/directory
```

#### 2.2 Evaluation Framework

**Functions:**
- `compute_pose_errors()`: Computes translation, rotation, and ADD errors
- `compute_tracking_stability()`: Computes stability metrics from pose sequence
- `run_tracking_sequence()`: Runs tracking with/without masks on a sequence
- `compare_tracking_results()`: Compares results and generates report

**Output Files:**
- `comparison_results.json`: Detailed metrics comparison
- `poses_no_mask.npy`: Pose sequence without masks
- `poses_with_mask.npy`: Pose sequence with masks
- `debug_no_mask/`: Debug outputs without masks
- `debug_with_mask/`: Debug outputs with masks

## Technical Details

### Mask Usage Strategy

The implementation uses masks in three ways:

1. **Point Filtering**: Filters xyz_map to only include points within the mask
2. **Drift Detection**: Compares pose translation with mask center to detect drift
3. **Translation Refinement**: Adjusts pose translation towards mask center when drift detected

### Drift Detection Threshold

- **Threshold**: 10% of object diameter
- **Refinement Weight**: 30% towards mask center, 70% towards current pose
- **Rationale**: Conservative approach to avoid over-correction

### Backward Compatibility

- All changes are backward compatible
- `ob_mask` parameter is optional (defaults to None)
- Existing code continues to work without modification
- Missing masks are handled gracefully

## Testing Recommendations

### Test Scenarios

1. **Occlusion Cases**: Test sequences with partial occlusions
2. **Fast Motion**: Test sequences with rapid object movement
3. **Similar Objects**: Test sequences with multiple similar objects
4. **Low Texture**: Test sequences with low-texture objects
5. **RGB-Only Mode**: Test sequences in RGB-only mode (masks may be more critical)

### Evaluation Criteria

**Quantitative:**
- Reduced pose error (if GT available)
- Improved tracking stability (lower variance)
- Fewer tracking failures

**Qualitative:**
- Better tracking in occlusion scenarios
- More stable tracking during fast motion
- Improved performance in RGB-only mode

## Files Modified

1. `FoundationPose/estimater.py`: Modified `track_one()` method
2. `FoundationPose/run.py`: Updated tracking loop to provide masks
3. `FoundationPose/experiments/compare_mask_tracking.py`: New comparison script
4. `FoundationPose/experiments/README.md`: Documentation for experiments
5. `FoundationPose/experiments/IMPLEMENTATION_SUMMARY.md`: This file

## Next Steps

1. Run comparison experiments on test sequences
2. Analyze results to determine when masks help vs. hurt
3. Optimize mask usage strategy based on findings
4. Consider conditional mask usage (only when beneficial)
5. Document best practices based on experimental results

## Notes

- Mask quality is critical: poor masks may hurt tracking
- Computation overhead is minimal (mask processing is fast)
- The implementation is conservative to avoid over-correction
- Further optimization may be possible based on experimental results
