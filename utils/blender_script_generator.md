# Blender Script Generator Documentation

## Overview

The `blender_script_generator.py` is a Python utility that converts FoundationPose tracking data into standalone Blender animation scripts. It extracts pose matrices from FoundationPose output directories and generates a complete, self-contained Blender Python script that can be run directly in Blender to visualize the tracked object's motion in 3D.

## Purpose

This tool bridges the gap between FoundationPose tracking results and 3D visualization by:
- Extracting pose data from FoundationPose's `ob_in_cam` directory
- Converting coordinate systems (OpenCV to Blender)
- Filtering unreliable tracking data
- Generating a complete Blender script with embedded animation data
- Properly configuring camera parameters to replicate the original video viewpoint

## Key Features

### 1. **Automatic Pose Data Extraction**
   - Reads all pose matrices from the `ob_in_cam` directory
   - Handles various naming patterns (e.g., `garnier_00170.txt`, `000000.txt`)
   - Extracts frame numbers automatically

### 2. **Intelligent Pose Filtering**
   - Removes unreliable tracking data (outliers, tracking failures)
   - Filters extreme jumps that indicate complete tracking loss
   - Uses statistical analysis to identify and remove bad poses
   - Preserves smooth, reliable motion data

### 3. **Camera Intrinsics Integration**
   - Loads camera intrinsics from `cam_K.txt` files
   - Automatically configures Blender camera with correct focal length
   - Replicates the original video's camera viewpoint
   - Falls back to sensible defaults if intrinsics are unavailable

### 4. **Coordinate System Conversion**
   - Converts OpenCV coordinates (+X right, +Y down, +Z forward) to Blender coordinates (+X right, +Y forward, +Z up)
   - Properly handles object-in-camera coordinate transformations
   - Positions camera at origin to match FoundationPose's coordinate system

### 5. **Auto-Configuration**
   - Automatically detects object names from directory paths or filenames
   - Calculates optimal visualization settings based on motion bounds
   - Scales object representations and coordinate axes appropriately
   - Configures scene properties (frame rate, units, lighting)

### 6. **Professional Visualization**
   - Creates motion path visualization (red curve showing 3D trajectory)
   - Adds coordinate axes for reference
   - Professional lighting setup (sun + area lights)
   - Object representation with realistic proportions based on object type
   - Scene info text overlay

## Usage

### Basic Usage

```bash
python blender_script_generator.py --input <path_to_ob_in_cam_directory>
```

### Full Command with Options

```bash
python blender_script_generator.py \
    --input <path_to_ob_in_cam_directory> \
    --object_name <object_name> \
    --camera_intrinsics <path_to_cam_K.txt> \
    --output <output_script_name.py>
```

### Arguments

- `--input` (required): Path to the `ob_in_cam` directory containing pose matrix `.txt` files
- `--object_name` (optional): Name of the tracked object (e.g., "bottle", "mustard", "garnier"). If not provided, the script will attempt to auto-detect it from the directory path or filenames.
- `--camera_intrinsics` (optional): Path to the camera intrinsics file (`cam_K.txt`). If not provided, the script will search common locations.
- `--output` (optional): Output filename for the generated Blender script. If not provided, a timestamped filename will be generated automatically.

### Example Commands

```bash
# Basic usage with auto-detection
python blender_script_generator.py --input user/earbuds_003/output/ob_in_cam

# With explicit object name and camera intrinsics
python blender_script_generator.py \
    --input user/bottle_001/output/ob_in_cam \
    --object_name bottle \
    --camera_intrinsics user/bottle_001/input/cam_K.txt \
    --output bottle_animation.py

# Using FoundationPose demo data structure
python blender_script_generator.py \
    --input demo_data/mustard0/ob_in_cam \
    --camera_intrinsics demo_data/mustard0/cam_K.txt
```

## Use Cases

### 1. **Visualization of Tracking Results**
   - **Purpose**: Quickly visualize FoundationPose tracking results in 3D
   - **Benefit**: Verify tracking quality and object motion without writing custom visualization code
   - **Workflow**: Run FoundationPose → Generate Blender script → View animation in Blender

### 2. **Debugging Tracking Issues**
   - **Purpose**: Identify problematic frames, tracking failures, or coordinate system issues
   - **Benefit**: Visual inspection helps identify when tracking is lost or produces incorrect poses
   - **Features Used**: Pose filtering highlights unreliable data, motion path shows discontinuities

### 3. **Presentation and Documentation**
   - **Purpose**: Create professional animations for papers, presentations, or documentation
   - **Benefit**: Clean, professional visualization with proper lighting and camera setup
   - **Output**: Standalone script that can be shared and run on any Blender installation

### 4. **Coordinate System Verification**
   - **Purpose**: Verify that coordinate system conversions are correct
   - **Benefit**: Visual confirmation that object motion matches expected behavior
   - **Feature**: Camera positioned to replicate original video viewpoint

### 5. **Motion Analysis**
   - **Purpose**: Analyze object trajectories, motion patterns, and spatial relationships
   - **Benefit**: 3D visualization makes it easier to understand complex motion
   - **Features**: Motion path visualization, coordinate axes, distance statistics

### 6. **Quality Assessment**
   - **Purpose**: Assess tracking quality and identify frames that need manual correction
   - **Benefit**: Automatic filtering removes obvious outliers, highlighting remaining issues
   - **Output**: Statistics on filtered vs. original frames, distance ranges, motion bounds

## Input Requirements

### Directory Structure

The script expects a directory containing pose matrix files:

```
ob_in_cam/
├── 000000.txt
├── 000001.txt
├── 000002.txt
└── ...
```

or

```
ob_in_cam/
├── garnier_00170.txt
├── garnier_00171.txt
└── ...
```

### Pose Matrix Format

Each `.txt` file should contain a 4×4 transformation matrix in row-major format:

```
r11 r12 r13 tx
r21 r22 r23 ty
r31 r32 r33 tz
0   0   0   1
```

This represents the object's pose in camera coordinates (ob_in_cam).

### Camera Intrinsics Format

The `cam_K.txt` file should contain a 3×3 camera intrinsics matrix:

```
fx  0   cx
0   fy  cy
0   0   1
```

## Output

### Generated Blender Script

The script generates a standalone Python file that:
- Contains all pose data embedded as Python code
- Includes camera intrinsics (if provided)
- Has complete Blender scene setup code
- Can be run directly in Blender without external dependencies
- Is self-contained and portable

### Script Contents

The generated script includes:
1. **Embedded Pose Data**: All pose matrices formatted as Python lists
2. **Camera Configuration**: Camera intrinsics and Blender camera setup
3. **Scene Setup**: Clearing scene, creating objects, lighting
4. **Animation Creation**: Keyframe generation from pose data
5. **Visualization**: Motion paths, coordinate axes, object representation
6. **Metadata**: Source information, frame ranges, statistics

## Running the Generated Script in Blender

1. **Open Blender** (version 2.8+ recommended)

2. **Clear Default Scene**:
   - Press `A` to select all
   - Press `X` → `Delete` to remove default objects

3. **Load Script**:
   - Switch to **Scripting** workspace
   - Click **File** → **Open** (or `Alt+O`)
   - Select the generated `.py` file

4. **Run Script**:
   - Click **Run Script** button (or press `Alt+P`)
   - Watch the console for progress messages

5. **View Animation**:
   - Switch to **Animation** workspace
   - Press `SPACE` to play animation
   - Use timeline scrubber to navigate frames

6. **Camera View**:
   - Press `Numpad 0` to view from camera (should match original video)
   - Press `Numpad 1/3/7` for front/side/top views

## Technical Details

### Coordinate System Conversion

The script converts from OpenCV to Blender coordinate systems:

- **OpenCV**: +X right, +Y down, +Z forward (into scene)
- **Blender**: +X right, +Y forward, +Z up

The conversion matrix:
```
[1   0   0   0]   # X stays the same
[0   0   1   0]   # Y_blender = Z_opencv
[0  -1   0   0]   # Z_blender = -Y_opencv
[0   0   0   1]
```

### Pose Filtering Algorithm

1. Calculates distance from origin for each pose
2. Computes mean and standard deviation
3. Filters poses outside 3σ range (very lenient)
4. Detects massive jumps (>10m) indicating tracking loss
5. Preserves smooth, continuous motion

### Camera Positioning

- **Camera Location**: Origin (0, 0, 0)
- **Rationale**: `ob_in_cam` data represents object position relative to camera
- **Rotation**: 90° around X-axis to align with FoundationPose +Z direction
- **Focal Length**: Calculated from camera intrinsics if available

## Troubleshooting

### No Pose Files Found
- **Error**: `No pose files found in {pose_dir}`
- **Solution**: Verify the input directory path contains `.txt` files with pose matrices

### Camera Intrinsics Not Found
- **Warning**: Script will use default camera parameters
- **Solution**: Provide `--camera_intrinsics` argument or place `cam_K.txt` in expected locations

### Tracking Quality Issues
- **Symptom**: Animation shows erratic motion or jumps
- **Solution**: The script automatically filters unreliable poses, but you may need to review the source tracking data

### Blender Script Errors
- **Error**: Script fails to run in Blender
- **Solution**: Ensure you're using Blender 2.8+ and have cleared the default scene before running

## Integration with FoundationPose Workflow

```
FoundationPose Tracking
    ↓
[ob_in_cam/ directory with pose matrices]
    ↓
blender_script_generator.py
    ↓
[Standalone Blender script]
    ↓
Blender Animation
```

## Advanced Usage

### Custom Object Proportions

The generated script includes object-specific scaling:
- Bottles/Mustard: Taller proportions (0.6, 0.6, 1.5)
- Garnier: Cosmetic bottle proportions (0.8, 0.8, 1.2)
- Generic: Default cube (1.0, 1.0, 1.0)

You can modify these in the generated script's `create_tracked_object()` function.

### Adjusting Visualization Settings

The generated script includes configurable features:
- `MOTION_TRAIL`: Enable/disable motion path visualization
- `COORDINATE_AXES`: Show/hide coordinate system axes
- `PROFESSIONAL_LIGHTING`: Enable/disable lighting setup
- `OBJECT_REPRESENTATION`: Show/hide object visualization

Modify these constants in the generated script to customize the visualization.

## Summary

The `blender_script_generator.py` is an essential tool for visualizing FoundationPose tracking results. It automates the conversion of pose data into professional 3D animations, making it easy to verify tracking quality, debug issues, and create visualizations for presentations or documentation. The generated scripts are standalone and portable, requiring only Blender to run.
