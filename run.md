# run.py Usage Guide

## Overview

`run.py` is a demonstration script for FoundationPose, a 6D object pose estimation and tracking system. The script processes a sequence of RGB-D images (or RGB-only images) to register and track the pose of a 3D object model.

## Use Cases

1. **Object Pose Registration**: Initial pose estimation from the first frame using RGB-D data
2. **Object Pose Tracking**: Sequential tracking of object pose across video frames
3. **RGB-Only Pose Estimation**: Pose estimation and tracking without depth sensor (using `--rgb_only` flag)
4. **Debugging and Visualization**: Visual inspection of pose estimation results
5. **Evaluation**: Testing pose estimation accuracy on custom datasets
6. **Consumer Applications**: Using standard RGB cameras (webcams, smartphones) without depth sensors
7. **Mobile Robotics**: Pose tracking in environments where depth sensors are unavailable or unreliable

## Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--mesh_file` | str | `None` (auto-detected) | Path to the 3D mesh file (.obj format). If not provided, will auto-detect from `--test_scene_dir` or `--inputs` by searching common locations: `{input_dir}/mesh/textured_simple.obj`, `{input_dir}/mesh/*.obj`, or `{input_dir}/../mesh/*.obj` |
| `--test_scene_dir` | str | `demo_data/mustard0` | Directory containing test scene RGB-D images. Ignored if `--inputs` is provided. |
| `--inputs` | str | `None` | Directory containing test scene RGB-D images. Takes precedence over `--test_scene_dir` if both are provided. |
| `--outputs` | str | `None` | Output directory for results. Takes precedence over `--debug_dir` if both are provided. If `--inputs` is provided but `--outputs` is not, auto-generates `outputs/<timestamp>/` as sibling of inputs directory. |
| `--est_refine_iter` | int | 5 | Number of refinement iterations for initial pose estimation |
| `--track_refine_iter` | int | 2 | Number of refinement iterations for pose tracking |
| `--debug` | int | 1 | Debug level (0-3): controls visualization and output verbosity |
| `--debug_dir` | str | `debug` | Output directory for debug files. Used only if `--outputs` is not provided. |
| `--rgb_only` | flag | False | Enable RGB-only mode (no depth sensor required). Depth maps will be set to zero and network will use RGB features only |

### Debug Levels

- **debug = 0**: No visualization, minimal output
- **debug >= 1**: Shows visualization window using `cv2.imshow()` (requires display)
- **debug >= 2**: Saves visualization images to `debug_dir/track_vis/`
- **debug >= 3**: Additionally saves transformed mesh (`model_tf.obj`) and scene point cloud (`scene_complete.ply`)

## Basic Usage

### Standard Execution (RGB-D Mode with display)

```bash
# With auto-detection (mesh file found automatically from input directory)
python run.py --inputs path/to/scene
# or
python run.py --test_scene_dir path/to/scene

# With explicit mesh file (overrides auto-detection)
python run.py --mesh_file path/to/mesh.obj --inputs path/to/scene
# or
python run.py --mesh_file path/to/mesh.obj --test_scene_dir path/to/scene
```

### RGB-Only Mode Execution

```bash
# Basic RGB-only mode (mesh auto-detected from input directory)
python run.py --rgb_only --inputs path/to/scene
# or
python run.py --rgb_only --test_scene_dir path/to/scene

# RGB-only mode with explicit mesh file
python run.py --rgb_only --mesh_file path/to/mesh.obj --inputs path/to/scene
# or
python run.py --rgb_only --mesh_file path/to/mesh.obj --test_scene_dir path/to/scene

# RGB-only mode with visualization (headless, auto-detected mesh)
xvfb-run -a python run.py --rgb_only \
  --inputs demo_data/mustard0 \
  --debug 2
# or
xvfb-run -a python run.py --rgb_only \
  --test_scene_dir demo_data/mustard0 \
  --debug 2
```
![](./docs/feature_of_rgb_only/vis_rgb_only.gif)

### With Custom Parameters

```bash
# RGB-D mode (mesh auto-detected)
python run.py \
  --inputs demo_data/mustard0 \
  --est_refine_iter 10 \
  --track_refine_iter 5 \
  --debug 2 \
  --debug_dir ./output
# or use --test_scene_dir instead of --inputs

# RGB-only mode with more refinement iterations (mesh auto-detected)
python run.py \
  --rgb_only \
  --inputs demo_data/mustard0 \
  --est_refine_iter 10 \
  --track_refine_iter 5 \
  --debug 2 \
  --debug_dir ./output_rgb_only
# or use --test_scene_dir instead of --inputs
```

## Running in Headless Environments

When running `run.py` in headless environments (Docker containers, SSH sessions without X11 forwarding, or servers without displays), the script will fail with a Qt/X11 display error when `debug >= 1` because it attempts to open a visualization window using `cv2.imshow()`.

### Error Message

```
qt.qpa.xcb: could not connect to display :1
qt.qpa.plugin: Could not load the Qt platform plugin "xcb"
This application failed to start because no Qt platform plugin could be initialized.
```

## Solutions for Headless Environments

### Solution 1: Use Xvfb (Virtual Display) - Recommended

Xvfb (X Virtual Framebuffer) creates a virtual display that allows GUI applications to run without a physical display.

#### Installation

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install xvfb

# CentOS/RHEL
sudo yum install xorg-x11-server-Xvfb
```

#### Usage

**Option A: Using xvfb-run (simplest)**

```bash
xvfb-run -a python run.py --debug 2
```

The `-a` flag automatically selects a display number.

**Option B: Manual Xvfb setup**

```bash
# Start Xvfb in the background
Xvfb :99 -screen 0 1024x768x24 &

# Set DISPLAY environment variable
export DISPLAY=:99

# Run your script
python run.py --debug 2

# Clean up (optional)
killall Xvfb
```

**Option C: Using Xvfb with specific display number**

```bash
xvfb-run --server-args="-screen 0 1920x1080x24" -a python run.py --debug 2
```

#### Advantages
- ✅ No code modifications required
- ✅ Works with any GUI application
- ✅ Allows full visualization functionality
- ✅ Can capture screenshots if needed

#### Disadvantages
- ⚠️ Requires additional package installation
- ⚠️ Slight performance overhead

### Solution 2: Disable Visualization (Set debug=0)

If visualization is not needed, simply set `debug=0` to skip the `cv2.imshow()` calls:

```bash
python run.py --debug 0
```

For saving visualization images without displaying them, you can modify the script to skip `cv2.imshow()` calls, or use `debug=2` with Xvfb.

#### Advantages
- ✅ No additional dependencies
- ✅ Fastest execution
- ✅ No display required

#### Disadvantages
- ⚠️ No real-time visualization
- ⚠️ Still saves images if `debug >= 2` (but won't crash)

### Solution 3: X11 Forwarding (SSH)

If connecting via SSH, enable X11 forwarding:

```bash
# Connect with X11 forwarding
ssh -X username@hostname

# Or with trusted X11 forwarding (less secure but more compatible)
ssh -Y username@hostname

# Then run normally
python run.py --debug 2
```

#### Prerequisites
- X server running on client machine (XQuartz on macOS, Xming on Windows, native X on Linux)
- X11 forwarding enabled in SSH server config (`/etc/ssh/sshd_config`: `X11Forwarding yes`)

#### Advantages
- ✅ Real display on your local machine
- ✅ No virtual display overhead

#### Disadvantages
- ⚠️ Requires X server on client
- ⚠️ Network latency for display
- ⚠️ Doesn't work in Docker without additional setup

### Solution 4: Set DISPLAY Environment Variable

If an X server is available on a different display:

```bash
export DISPLAY=:0  # or :1, :2, etc.
python run.py --debug 2
```

#### Advantages
- ✅ Simple if X server exists

#### Disadvantages
- ⚠️ Requires existing X server
- ⚠️ May not work in containers

### Solution 5: Modify Script to Skip cv2.imshow()

For a permanent solution, you can modify `run.py` to conditionally skip visualization based on an environment variable:

```python
# Add at the top
import os

# Replace lines 72-73 with:
if debug >= 1 and os.getenv('DISPLAY'):
    cv2.imshow('1', vis[...,::-1])
    cv2.waitKey(1)
```

Then run with `DISPLAY` unset or empty:

```bash
unset DISPLAY
python run.py --debug 2  # Will save images but not display
```

## Recommended Approach for Docker

For Docker containers, use Xvfb:

```dockerfile
# In Dockerfile
RUN apt-get update && apt-get install -y xvfb

# At runtime
CMD ["xvfb-run", "-a", "python", "run.py", "--debug", "2"]
```

Or use docker-compose:

```yaml
services:
  foundationpose:
    image: your-image
    command: xvfb-run -a python run.py --debug 2
```

## Input and Output Directory Selection

### Input Directory Logic

The script determines the input directory using the following priority:

1. **If `--inputs` is provided**: Use `--inputs` (ignores `--test_scene_dir` if also provided)
2. **Else if `--test_scene_dir` is provided**: Use `--test_scene_dir`
3. **Else**: Use default `demo_data/mustard0`

**Examples:**
```bash
# Uses --inputs (ignores --test_scene_dir)
python run.py --inputs /path/to/inputs --test_scene_dir /other/path

# Uses --test_scene_dir
python run.py --test_scene_dir /path/to/scene

# Uses default demo_data/mustard0
python run.py
```

### Output Directory Logic

The script determines the output directory using the following priority:

1. **If `--outputs` is provided**: Use `--outputs` (ignores `--debug_dir` if also provided)
2. **Else if `--inputs` is provided**: Auto-generate `outputs/<timestamp>/` as sibling of `inputs` directory
   - Example: If `--inputs /data/scene001`, generates `/data/outputs/20240123_143022/`
3. **Else if `--debug_dir` is provided**: Use `--debug_dir`
4. **Else**: Use default `debug`

**Examples:**
```bash
# Uses --outputs (ignores --debug_dir)
python run.py --inputs /data/scene --outputs /results/output1 --debug_dir /other/debug

# Auto-generates outputs/<timestamp>/ as sibling of inputs
python run.py --inputs /data/scene001
# Creates: /data/outputs/20240123_143022/

# Uses --debug_dir
python run.py --test_scene_dir /data/scene --debug_dir /custom/debug

# Uses default debug
python run.py --test_scene_dir /data/scene
```

### Directory Structure Example

When using `--inputs` with auto-generated outputs:

```
/data/
├── scene001/          (--inputs)
│   ├── rgb/
│   ├── depth/
│   ├── mesh/
│   └── cam_K.txt
└── outputs/           (auto-generated sibling)
    └── 20240123_143022/  (timestamped output)
        ├── ob_in_cam/
        ├── track_vis/
        └── ...
```

## Output Files

The script generates the following outputs in the output directory (determined by the logic above):

- **`ob_in_cam/`**: Pose matrices (4x4 transformation matrices) for each frame
- **`track_vis/`**: Visualization images (when `debug >= 2`)
- **`model_tf.obj`**: Transformed mesh model (when `debug >= 3`)
- **`scene_complete.ply`**: Scene point cloud (when `debug >= 3`)

### Output Directory Cleanup

**Important**: The script automatically clears the output directory before each run to ensure clean results:

- If the output directory exists, all its contents are removed before processing begins
- The directory structure (`track_vis/` and `ob_in_cam/`) is then recreated
- This prevents mixing old and new results from previous runs
- Uses Python's `shutil.rmtree()` for safe, cross-platform directory removal that handles paths with spaces and special characters correctly

**Note**: If you want to preserve previous results, either:
- Use different output directories for each run (e.g., with timestamps)
- Manually backup the output directory before running
- Use the auto-generated timestamped outputs when using `--inputs`

## Example Workflows

### Workflow 1: RGB-D Mode (Standard)

```bash
# 1. Activate conda environment
conda activate foundationpose

# 2. Run with virtual display (headless, mesh auto-detected)
# Using --inputs with auto-generated outputs
xvfb-run -a python run.py \
  --inputs demo_data/mustard0 \
  --debug 2
# Outputs will be in: demo_data/outputs/<timestamp>/

# Or specify custom output directory
xvfb-run -a python run.py \
  --inputs demo_data/mustard0 \
  --outputs ./results \
  --debug 2

# Or use --test_scene_dir with --debug_dir (legacy)
xvfb-run -a python run.py \
  --test_scene_dir demo_data/mustard0 \
  --debug_dir ./results \
  --debug 2

# 3. Check results
ls ./results/track_vis/     # Visualization images
ls ./results/ob_in_cam/     # Pose files
ls ./results/depth.png      # Depth image (RGB-D mode only)
```

### Workflow 2: RGB-Only Mode

```bash
# 1. Activate conda environment
conda activate foundationpose

# 2. Run RGB-only mode with virtual display (headless, mesh auto-detected)
# Using --inputs with auto-generated outputs
xvfb-run -a python run.py \
  --rgb_only \
  --inputs demo_data/mustard0 \
  --debug 2 \
  --est_refine_iter 5 \
  --track_refine_iter 2
# Outputs will be in: demo_data/outputs/<timestamp>/

# Or specify custom output directory
xvfb-run -a python run.py \
  --rgb_only \
  --inputs demo_data/mustard0 \
  --outputs ./results_rgb_only \
  --debug 2 \
  --est_refine_iter 5 \
  --track_refine_iter 2

# 3. Check results
ls ./results_rgb_only/track_vis/     # Visualization images
ls ./results_rgb_only/ob_in_cam/     # Pose files
# Note: depth.png will NOT exist in RGB-only mode
```

### Workflow 3: RGB-Only Mode for Quick Testing

```bash
# Quick test without visualization (fastest, mesh auto-detected)
# Using --inputs with auto-generated outputs
python run.py \
  --rgb_only \
  --inputs demo_data/mustard0 \
  --debug 0 \
  --est_refine_iter 2 \
  --track_refine_iter 1
# Outputs will be in: demo_data/outputs/<timestamp>/

# Check pose files only
ls demo_data/outputs/*/ob_in_cam/
```

### Workflow 4: RGB-Only Mode with Full Visualization

```bash
# Generate complete visualization set (mesh auto-detected)
# Using --inputs with custom outputs
xvfb-run -a python run.py \
  --rgb_only \
  --inputs demo_data/mustard0 \
  --outputs ./rgb_only_vis \
  --debug 2 \
  --est_refine_iter 5 \
  --track_refine_iter 2

# Create GIF animation from visualizations
cd rgb_only_vis/track_vis
ffmpeg -y -framerate 10 -pattern_type glob -i '*.png' \
  -vf "scale=640:-1:flags=lanczos" -c:v gif ../tracking_animation.gif
```

## RGB-Only Mode Use Cases

### When to Use RGB-Only Mode

1. **No Depth Sensor Available**
   - Standard RGB cameras (webcams, smartphones)
   - Consumer devices without depth capabilities
   - Legacy camera systems

2. **Depth Sensor Unreliable**
   - Poor lighting conditions affecting depth sensors
   - Reflective or transparent surfaces
   - Outdoor environments with sunlight interference

3. **Cost Constraints**
   - Avoiding expensive RGB-D cameras
   - Using existing RGB camera infrastructure
   - Mobile/embedded applications

4. **Privacy Concerns**
   - Applications where depth data collection is restricted
   - Public-facing systems

### RGB-Only Mode Characteristics

| Aspect | RGB-D Mode | RGB-Only Mode |
|--------|------------|---------------|
| **Input Requirements** | RGB + Depth | RGB only |
| **Translation Accuracy** | High (metric) | Moderate (relative) |
| **Initialization** | Robust | May need more iterations |
| **Tracking Quality** | Excellent | Good |
| **Hardware Requirements** | RGB-D camera | Standard RGB camera |
| **Use Cases** | Industrial, robotics | Consumer, webcam, mobile |

### RGB-Only Mode Recommendations

- **Refinement Iterations**: Use `--est_refine_iter 5-10` for better initial pose estimation
- **Tracking Iterations**: `--track_refine_iter 2` is usually sufficient
- **Visualization**: Use `--debug 2` with Xvfb to generate verification images
- **Accuracy**: Expect slightly lower accuracy than depth-based mode, especially for absolute translation

## Troubleshooting

### Issue: "could not connect to display"
**Solution**: Use Xvfb or set `debug=0`

### Issue: Xvfb not found
**Solution**: Install with `apt-get install xvfb` or `yum install xorg-x11-server-Xvfb`

### Issue: Still seeing Qt errors with Xvfb
**Solution**: Ensure Xvfb is running and DISPLAY is set correctly:
```bash
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
```

### Issue: Want visualization but no display
**Solution**: Use `debug=2` with Xvfb to save images without displaying them

### Issue: RGB-only mode poor pose accuracy
**Solution**: 
- Increase `--est_refine_iter` to 10-15
- Ensure good object mask quality
- Verify mesh scale is correct
- Check camera intrinsics

### Issue: RGB-only mode translation seems incorrect
**Solution**:
- This is expected - translation estimation without depth is less accurate
- Translation uses heuristic based on mesh diameter
- Consider using more refinement iterations
- Verify camera intrinsics are correct

### Issue: RGB-only mode crashes during visualization
**Solution**: Ensure you have the latest code with RGB-only mode visualization fixes (Issue #2 resolved)

## Notes

- The script processes frames sequentially and tracks object pose across the sequence
- First frame uses registration (`est.register()`), subsequent frames use tracking (`est.track_one()`)
- Pose outputs are saved as 4x4 transformation matrices in `ob_in_cam/` directory
- Visualization shows 3D bounding box and coordinate axes overlaid on the RGB image
- **Input directory selection**: 
  - `--inputs` takes precedence over `--test_scene_dir` if both are provided
  - If neither is provided, defaults to `demo_data/mustard0`
- **Output directory selection**:
  - `--outputs` takes precedence over `--debug_dir` if both are provided
  - If `--inputs` is provided but `--outputs` is not, auto-generates `outputs/<timestamp>/` as sibling of inputs
  - If `--debug_dir` is provided (and `--outputs` is not), uses `--debug_dir`
  - Otherwise defaults to `debug`
- **Output directory cleanup**: The output directory is automatically cleared before each run using Python's `shutil.rmtree()` for safe, cross-platform operation. This ensures clean results and prevents mixing old and new outputs. The directory structure is then recreated with `track_vis/` and `ob_in_cam/` subdirectories.
- **Mesh file auto-detection**: If `--mesh_file` is not provided, the script automatically searches for mesh files in common locations relative to the input directory:
  - `{input_dir}/mesh/textured_simple.obj` (most common pattern)
  - `{input_dir}/mesh/*.obj` (if exactly one .obj file exists)
  - `{input_dir}/../mesh/*.obj` (parent directory)
  - Falls back to default `demo_data/mustard0/mesh/textured_simple.obj` if none found
- **RGB-only mode**: When `--rgb_only` is enabled, depth maps are set to zero and the network falls back to RGB features only
- **RGB-only mode**: Translation estimation uses mesh diameter heuristic (~2.5x mesh diameter)
- **RGB-only mode**: No `depth.png` file is generated in debug output (confirms RGB-only mode)

## Additional Resources

- **RGB-Only Mode Documentation**: See `docs/feature_of_rgb_only/feature_of_rgb_only.md` for detailed information
- **Visualization Guide**: See `docs/feature_of_rgb_only/VISUALIZATION_OUTPUTS.md` for visualization details
- **Test Results**: See `docs/feature_of_rgb_only/RUNTIME_TEST_RESULTS.md` for test results and use cases
