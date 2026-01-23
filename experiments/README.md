# Mask Tracking Investigation Experiments

This directory contains scripts and tools for investigating whether providing masks for all frames improves tracking quality.

## Overview

The investigation compares tracking performance with and without masks to determine:
1. Whether masks improve tracking accuracy
2. Whether masks improve tracking stability
3. When masks are most beneficial (occlusion, fast motion, etc.)

## Files

- `compare_mask_tracking.py`: Main comparison script that runs tracking with and without masks and compares results

## Usage

### Basic Usage

```bash
python experiments/compare_mask_tracking.py \
    --inputs /path/to/input/directory \
    --outputs /path/to/output/directory
```

### With Custom Mesh

```bash
python experiments/compare_mask_tracking.py \
    --inputs /path/to/input/directory \
    --mesh_file /path/to/mesh.obj \
    --outputs /path/to/output/directory
```

### RGB-Only Mode

```bash
python experiments/compare_mask_tracking.py \
    --inputs /path/to/input/directory \
    --rgb_only \
    --outputs /path/to/output/directory
```

### Full Options

```bash
python experiments/compare_mask_tracking.py \
    --inputs /path/to/input/directory \
    --mesh_file /path/to/mesh.obj \
    --outputs /path/to/output/directory \
    --est_refine_iter 5 \
    --track_refine_iter 2 \
    --debug 2 \
    --rgb_only
```

## Input Requirements

The input directory should follow the standard FoundationPose structure:
```
input_directory/
├── rgb/              # RGB images
│   ├── 000000.png
│   ├── 000001.png
│   └── ...
├── masks/            # Object masks (required for mask comparison)
│   ├── 000000.png
│   ├── 000001.png
│   └── ...
├── depth/            # Depth images (optional, for RGB-D mode)
│   ├── 000000.png
│   └── ...
└── cam_K.txt         # Camera intrinsics matrix
```

## Output

The script generates:
1. `comparison_results.json`: Detailed comparison metrics
2. `poses_no_mask.npy`: Pose sequence without masks
3. `poses_with_mask.npy`: Pose sequence with masks
4. `debug_no_mask/`: Debug outputs from tracking without masks
5. `debug_with_mask/`: Debug outputs from tracking with masks

## Metrics

The comparison includes:

### Stability Metrics
- **Translation variance**: Variance of translation across frames (lower is better)
- **Rotation variance**: Variance of rotation across frames (lower is better)
- **Frame-to-frame translation**: Average change between consecutive frames (lower is better)
- **Frame-to-frame rotation**: Average rotation change between consecutive frames (lower is better)

### Pose Error Metrics (if GT poses available)
- **Translation error**: Average translation error in meters
- **Rotation error**: Average rotation error in degrees
- **ADD error**: Average Distance of Model Points error in meters

## Interpretation

- **Positive improvements**: Masks help tracking
- **Negative improvements**: Masks hurt tracking (may indicate poor mask quality)
- **Near-zero improvements**: Masks have minimal effect

## Notes

- The script requires masks for all frames to perform the comparison
- If masks are missing for some frames, those frames will fall back to tracking without masks
- Ground truth poses are optional but recommended for quantitative evaluation
