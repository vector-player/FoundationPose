# run_demo.py Usage Guide

## Overview

`run_demo.py` is a demonstration script for FoundationPose, a 6D object pose estimation and tracking system. The script processes a sequence of RGB-D images to register and track the pose of a 3D object model.

## Use Cases

1. **Object Pose Registration**: Initial pose estimation from the first frame using RGB-D data
2. **Object Pose Tracking**: Sequential tracking of object pose across video frames
3. **Debugging and Visualization**: Visual inspection of pose estimation results
4. **Evaluation**: Testing pose estimation accuracy on custom datasets

## Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--mesh_file` | str | `demo_data/mustard0/mesh/textured_simple.obj` | Path to the 3D mesh file (.obj format) |
| `--test_scene_dir` | str | `demo_data/mustard0` | Directory containing test scene RGB-D images |
| `--est_refine_iter` | int | 5 | Number of refinement iterations for initial pose estimation |
| `--track_refine_iter` | int | 2 | Number of refinement iterations for pose tracking |
| `--debug` | int | 1 | Debug level (0-3): controls visualization and output verbosity |
| `--debug_dir` | str | `debug` | Output directory for debug files and visualizations |

### Debug Levels

- **debug = 0**: No visualization, minimal output
- **debug >= 1**: Shows visualization window using `cv2.imshow()` (requires display)
- **debug >= 2**: Saves visualization images to `debug_dir/track_vis/`
- **debug >= 3**: Additionally saves transformed mesh (`model_tf.obj`) and scene point cloud (`scene_complete.ply`)

## Basic Usage

### Standard Execution (with display)

```bash
python run_demo.py --mesh_file path/to/mesh.obj --test_scene_dir path/to/scene
```

### With Custom Parameters

```bash
python run_demo.py \
  --mesh_file demo_data/mustard0/mesh/textured_simple.obj \
  --test_scene_dir demo_data/mustard0 \
  --est_refine_iter 10 \
  --track_refine_iter 5 \
  --debug 2 \
  --debug_dir ./output
```

## Running in Headless Environments

When running `run_demo.py` in headless environments (Docker containers, SSH sessions without X11 forwarding, or servers without displays), the script will fail with a Qt/X11 display error when `debug >= 1` because it attempts to open a visualization window using `cv2.imshow()`.

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
xvfb-run -a python run_demo.py --debug 2
```

The `-a` flag automatically selects a display number.

**Option B: Manual Xvfb setup**

```bash
# Start Xvfb in the background
Xvfb :99 -screen 0 1024x768x24 &

# Set DISPLAY environment variable
export DISPLAY=:99

# Run your script
python run_demo.py --debug 2

# Clean up (optional)
killall Xvfb
```

**Option C: Using Xvfb with specific display number**

```bash
xvfb-run --server-args="-screen 0 1920x1080x24" -a python run_demo.py --debug 2
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
python run_demo.py --debug 0
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
python run_demo.py --debug 2
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
python run_demo.py --debug 2
```

#### Advantages
- ✅ Simple if X server exists

#### Disadvantages
- ⚠️ Requires existing X server
- ⚠️ May not work in containers

### Solution 5: Modify Script to Skip cv2.imshow()

For a permanent solution, you can modify `run_demo.py` to conditionally skip visualization based on an environment variable:

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
python run_demo.py --debug 2  # Will save images but not display
```

## Recommended Approach for Docker

For Docker containers, use Xvfb:

```dockerfile
# In Dockerfile
RUN apt-get update && apt-get install -y xvfb

# At runtime
CMD ["xvfb-run", "-a", "python", "run_demo.py", "--debug", "2"]
```

Or use docker-compose:

```yaml
services:
  foundationpose:
    image: your-image
    command: xvfb-run -a python run_demo.py --debug 2
```

## Output Files

The script generates the following outputs in `debug_dir`:

- **`ob_in_cam/`**: Pose matrices (4x4 transformation matrices) for each frame
- **`track_vis/`**: Visualization images (when `debug >= 2`)
- **`model_tf.obj`**: Transformed mesh model (when `debug >= 3`)
- **`scene_complete.ply`**: Scene point cloud (when `debug >= 3`)

## Example Workflow

```bash
# 1. Activate conda environment
conda activate foundationpose

# 2. Run with virtual display (headless)
xvfb-run -a python run_demo.py \
  --mesh_file demo_data/mustard0/mesh/textured_simple.obj \
  --test_scene_dir demo_data/mustard0 \
  --debug 2 \
  --debug_dir ./results

# 3. Check results
ls ./results/track_vis/     # Visualization images
ls ./results/ob_in_cam/     # Pose files
```

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

## Notes

- The script processes frames sequentially and tracks object pose across the sequence
- First frame uses registration (`est.register()`), subsequent frames use tracking (`est.track_one()`)
- Pose outputs are saved as 4x4 transformation matrices in `ob_in_cam/` directory
- Visualization shows 3D bounding box and coordinate axes overlaid on the RGB image
