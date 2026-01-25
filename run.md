# run.py Usage Guide

## Overview

`run.py` is a demonstration script for FoundationPose, a 6D object pose estimation and tracking system. The script processes a sequence of RGB-D images (or RGB-only images) to register and track the pose of a 3D object model.

```shell
xvfb-run -a python run.py --rgb_only --debug 2 --inputs path/to/inputs
```

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

## Naming Conventions and Directory Structure

### Overview

FoundationPose uses specific naming conventions for input directories and files. Following these conventions ensures proper automatic path resolution and prevents errors. The script automatically locates mask files by replacing the `rgb` subdirectory with `masks` in the path.

### Input Directory Structure

Your input directory should follow this structure:

```
input_directory/
├── rgb/              # RGB images (required)
│   ├── 000000.png
│   ├── 000001.png
│   └── ...
├── masks/            # Object masks (required)
│   ├── 000000.png
│   ├── 000001.png
│   └── ...
├── depth/            # Depth images (optional, for RGB-D mode)
│   ├── 000000.png
│   └── ...
├── mesh/             # 3D mesh files (optional, for auto-detection)
│   ├── textured_simple.obj
│   └── ...
└── cam_K.txt         # Camera intrinsics matrix (required)
```

### Critical Naming Rules

#### 1. **Subdirectory Names Must Be Exact**

- ✅ **Correct**: Use `rgb` and `masks` as exact subdirectory names
- ❌ **Incorrect**: `RGB`, `Rgb`, `rgb_images`, `rgb_data`

**Why**: The script searches for mask files by replacing the `rgb` directory component with `masks`. The replacement is case-sensitive and must match exactly.

#### 2. **Parent Directory Names Can Contain 'rgb'**

- ✅ **Safe**: `mustard0_rgb/inputs/rgb/` → mask path: `mustard0_rgb/inputs/masks/`
- ✅ **Safe**: `my_rgb_dataset/scene001/rgb/` → mask path: `my_rgb_dataset/scene001/masks/`
- ✅ **Safe**: `rgb_camera_data/inputs/rgb/` → mask path: `rgb_camera_data/inputs/masks/`

**Why**: The path replacement algorithm uses component-based matching, so it only replaces the `rgb` directory component, not all occurrences of 'rgb' in the path. This allows parent directories to contain 'rgb' in their names without issues.

#### 3. **File Names Must Match Between rgb/ and masks/**

- ✅ **Correct**: 
  - `rgb/1581120424100262102.png` → `masks/1581120424100262102.png`
  - `rgb/frame_001.png` → `masks/frame_001.png`
- ❌ **Incorrect**: 
  - `rgb/frame_001.png` → `masks/mask_001.png` (different filename)
  - `rgb/image.png` → `masks/image_mask.png` (different filename)

**Why**: The script uses the same filename from the RGB image to locate the corresponding mask file.

### Path Replacement Design

The script uses a **component-based path replacement** algorithm to safely handle directory names containing 'rgb':

1. **Path Splitting**: The RGB image path is split into directory components
2. **Component Matching**: The algorithm searches for a directory component named exactly `rgb`
3. **Selective Replacement**: Only the matching directory component is replaced with `masks`
4. **Path Reconstruction**: The path is reconstructed with the replaced component

**Example**:
```
Input RGB path:  ./user/mustard0_rgb/inputs/rgb/1581120424100262102.png
Path components: ['.', 'user', 'mustard0_rgb', 'inputs', 'rgb', '1581120424100262102.png']
Find 'rgb' component: index 4
Replace component:  ['.', 'user', 'mustard0_rgb', 'inputs', 'masks', '1581120424100262102.png']
Output mask path:   ./user/mustard0_rgb/inputs/masks/1581120424100262102.png
```

Notice that `mustard0_rgb` remains unchanged - only the `rgb` subdirectory is replaced.

### Best Practices

#### ✅ Recommended Directory Naming

```bash
# Good: Descriptive names that may contain 'rgb'
my_dataset_rgb/
scene001_rgb/
rgb_camera_data/
mustard0_rgb/

# All of these work correctly because the 'rgb' subdirectory is separate
```

#### ❌ Avoid These Patterns

```bash
# Avoid: Using 'rgb' as part of the subdirectory name
rgb_images/          # Should be just 'rgb/'
rgb_data/            # Should be just 'rgb/'
mask_images/         # Should be just 'masks/'
```

### Common Mistakes and Solutions

#### Mistake 1: Case Sensitivity

**Problem**: Using `RGB` instead of `rgb`
```
Error: Mask file not found: ./inputs/RGB/... → ./inputs/masks/...
```

**Solution**: Use lowercase `rgb` and `masks` for subdirectory names.

#### Mistake 2: Missing Masks Directory

**Problem**: Only `rgb/` directory exists, no `masks/` directory
```
Error: Mask file not found: ./inputs/masks/1581120424100262102.png
```

**Solution**: Create a `masks/` directory with corresponding mask files.

#### Mistake 3: Filename Mismatch

**Problem**: RGB and mask files have different names
```
RGB: rgb/frame_001.png
Mask: masks/mask_001.png  # Different name!
```

**Solution**: Ensure mask files have the same filename as their corresponding RGB images.

#### Mistake 4: Incorrect Directory Structure

**Problem**: Files are not in the expected subdirectories
```
inputs/
├── image1.png      # Should be in rgb/
└── mask1.png       # Should be in masks/
```

**Solution**: Organize files into `rgb/` and `masks/` subdirectories.

### Verification Checklist

Before running the script, verify:

- [ ] Input directory contains `rgb/` subdirectory with RGB images
- [ ] Input directory contains `masks/` subdirectory with mask images
- [ ] Mask filenames match RGB filenames exactly
- [ ] `cam_K.txt` file exists in the input directory root
- [ ] If using RGB-D mode, `depth/` subdirectory exists with depth images
- [ ] If auto-detecting mesh, `mesh/` subdirectory exists with `.obj` files

### Example: Correct Directory Setup

```bash
# Create directory structure
mkdir -p my_scene/rgb my_scene/masks my_scene/depth my_scene/mesh

# Copy RGB images
cp images/*.png my_scene/rgb/

# Copy corresponding masks (same filenames!)
cp masks/*.png my_scene/masks/

# Copy camera intrinsics
cp cam_K.txt my_scene/

# Run the script
python run.py --inputs my_scene
```

### Technical Details

The path replacement uses Python's `os.path` functions for cross-platform compatibility:

- **Windows**: Uses backslashes (`\`) as path separators
- **Linux/macOS**: Uses forward slashes (`/`) as path separators
- **Component Matching**: Searches from the end of the path to find the last occurrence of `rgb` as a directory component
- **Error Handling**: Raises `FileNotFoundError` with detailed information if mask file cannot be found

This design ensures that:
1. Parent directories can safely contain 'rgb' in their names
2. Only the intended `rgb` subdirectory is replaced
3. Paths work correctly across different operating systems
4. Clear error messages help diagnose issues

## Mesh Files and Material Requirements

### Overview

FoundationPose requires a 3D mesh file (`.obj` format) representing the object to be tracked. The mesh file can optionally include texture materials for enhanced visualization and rendering. This section covers mesh file requirements, material specifications, and the fallback mechanism when texture images are missing.

### Mesh File Format

FoundationPose supports OBJ format mesh files. The mesh file should contain:
- **Vertices** (`v` lines): 3D coordinates of mesh vertices
- **Faces** (`f` lines): Face definitions connecting vertices
- **Texture coordinates** (`vt` lines): Optional UV coordinates for texture mapping
- **Material library reference** (`mtllib` line): Reference to a Material Template Library (MTL) file

### Material Template Library (MTL) Files

If your mesh uses textures, you need a corresponding MTL file that defines material properties and references texture images.

#### MTL File Structure

An MTL file contains material definitions with the following format:

```
# Comments start with #
newmtl material_name
Ns 96.078431          # Specular exponent
Ka 1.000000 1.000000 1.000000  # Ambient color (RGB)
Kd 0.800000 0.800000 0.800000  # Diffuse color (RGB)
Ks 0.500000 0.500000 0.500000  # Specular color (RGB)
Ke 0.000000 0.000000 0.000000  # Emissive color (RGB)
Ni 1.000000           # Optical density (index of refraction)
d 1.000000            # Dissolve (transparency, 0.0-1.0)
illum 2               # Illumination model (0-10)
map_Kd texture.png    # Diffuse texture map (IMAGE REFERENCE)
```

#### Texture Image References

To use a texture image with your mesh, you must reference it in the MTL file using one of these map commands:

| Command | Description | Example |
|---------|-------------|---------|
| `map_Kd` | Diffuse texture map (most common) | `map_Kd shaded.png` |
| `map_Ks` | Specular texture map | `map_Ks specular.png` |
| `map_Ka` | Ambient texture map | `map_Ka ambient.png` |
| `map_Bump` or `map_bump` | Normal/bump map | `map_Bump normal.png` |
| `map_d` | Opacity/alpha map | `map_d alpha.png` |

**Important Notes:**
- Image paths in MTL files are **relative to the MTL file's directory**
- Supported image formats: PNG, JPG, JPEG, TGA, BMP, TIFF
- The `map_Kd` command is the most commonly used for basic texture mapping

#### Example: Complete MTL File with Texture

```
# Blender 4.4.3 MTL File
# www.blender.org

newmtl model.001
Ns 218.920959
Ka 1.000000 1.000000 1.000000
Kd 0.000000 0.000000 0.000000
Ks 0.500000 0.500000 0.500000
Ke 1.000000 1.000000 1.000000
Ni 1.500000
d 1.000000
illum 2
map_Kd shaded.png
```

In this example, `shaded.png` should be located in the same directory as the MTL file.

### Material Requirements and Fallback Mechanism

FoundationPose handles mesh materials with the following priority:

1. **Texture Image (Preferred)**: If the MTL file references a texture image and the image file exists, FoundationPose will use it for rendering.
2. **Vertex Colors**: If no texture image is available but the mesh has vertex colors, those will be used.
3. **Default Gray Color**: If neither texture nor vertex colors are available, a default gray color (RGB: 128, 128, 128) is assigned.

#### Automatic Detection and Fallback

When loading a mesh, FoundationPose automatically:

1. **Checks for texture image**: If the mesh has `TextureVisuals` and the MTL file references an image, it attempts to load the texture.
2. **Logs status**: 
   - ✓ Success: `[make_mesh_tensors] ✓ Texture image found and loaded`
   - ⚠ Warning: `[make_mesh_tensors] ⚠ Texture image is missing (mesh has TextureVisuals but no material image)`
3. **Prompts user (if texture missing)**: When a texture is expected but missing, the system will prompt you with options:
   ```
   ============================================================
   MESH TEXTURE IMAGE MISSING
   ============================================================
   The mesh references a texture but no image file was found.
   
   Options:
     1. Cancel - Exit the program
     2. Vertex Colors - Use existing vertex colors (if available)
     3. Default Gray - Proceed with default gray color
   ============================================================
   Select option (1/2/3) [default: 3]:
   ```

#### Common Scenarios

**Scenario 1: MTL file missing texture reference**
- **Symptom**: MTL file defines material properties but has no `map_Kd` (or similar) line
- **Result**: System detects `TextureVisuals` but no image, prompts for fallback option
- **Solution**: Add `map_Kd texture.png` to your MTL file

**Scenario 2: Texture image file missing**
- **Symptom**: MTL file references an image (e.g., `map_Kd texture.png`) but the file doesn't exist
- **Result**: System detects missing file, prompts for fallback option
- **Solution**: Ensure the texture image file exists in the same directory as the MTL file

**Scenario 3: Mesh without texture coordinates**
- **Symptom**: Mesh has no `vt` (texture coordinate) lines in OBJ file
- **Result**: System uses vertex colors or default gray
- **Solution**: This is normal - not all meshes need textures

### Best Practices

1. **Always include `map_Kd` in MTL file if using textures**: Even if other material properties are set, the texture image reference is required.

2. **Keep texture images in the same directory as MTL file**: This ensures relative paths work correctly.

3. **Use descriptive texture filenames**: Names like `texture_diffuse.png` or `shaded.png` are clearer than generic names.

4. **Verify texture file exists**: Before running, ensure the image file referenced in the MTL actually exists.

5. **Test mesh loading**: If you're unsure about your mesh setup, test loading it in a 3D viewer (like Blender or MeshLab) to verify materials load correctly.

### Example: Setting Up a Mesh with Texture

```
mesh/
├── object.obj          # Mesh file
├── object.mtl          # Material file
└── texture.png          # Texture image
```

**object.obj** (excerpt):
```
mtllib object.mtl
v -0.5 -0.5 0.0
v 0.5 -0.5 0.0
v 0.0 0.5 0.0
vt 0.0 0.0
vt 1.0 0.0
vt 0.5 1.0
usemtl material.001
f 1/1 2/2 3/3
```

**object.mtl**:
```
newmtl material.001
Kd 1.0 1.0 1.0
map_Kd texture.png
```

### Troubleshooting Mesh Material Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Texture image is missing" prompt | MTL references texture but file missing | Add texture file or remove `map_Kd` line |
| No texture loaded | MTL file has no `map_Kd` line | Add `map_Kd texture.png` to MTL file |
| Wrong texture path | Image in different directory | Move image to MTL directory or use correct relative path |
| Mesh appears gray | No texture or vertex colors | This is expected fallback behavior |

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

### Issue: Shape Mismatch Error When Using Multiple Masks
**Error Message**:
```
ValueError: operands could not be broadcast together with shapes (1,4) (3,)
```

**Location**: `estimater.py`, line 348 in `track_one()` method

**When It Occurs**:
- ✅ Frame 0 (registration): Works fine
- ✅ Frame 1 (first tracking frame): Works fine
- ❌ Frame 2+ (subsequent tracking frames): Fails with shape mismatch error

**Root Cause**:
This error occurs when using masks for multiple frames during tracking. The issue stems from an inconsistent tensor shape:

1. **Frame 0 (Registration)**: `self.pose_last` has shape `(4, 4)` - a single pose matrix
2. **Frame 1+ (Tracking)**: After the first tracking update, `self.pose_last` becomes shape `(1, 4, 4)` - a batch tensor with one pose
3. **Shape Mismatch**: The code attempts to extract translation as `self.pose_last[:3, 3]`, which:
   - Works correctly for `(4, 4)` shape → returns `(3,)` translation vector
   - Fails for `(1, 4, 4)` shape → returns `(1, 4)` instead of `(3,)`
   - Causes broadcast error when subtracting from mask center `(3,)` vector

**The Fix**:
The code has been updated to handle both tensor shapes correctly:

```python
# Handle both (4,4) and (1,4,4) shapes for pose_last
if len(self.pose_last.shape) == 3:
    # Batch dimension present: shape is (1, 4, 4)
    current_center = self.pose_last[0, :3, 3].cpu().numpy()
else:
    # No batch dimension: shape is (4, 4)
    current_center = self.pose_last[:3, 3].cpu().numpy()
```

**Solution Status**:
✅ **Fixed**: This issue has been resolved in the codebase. The fix:
- Detects the shape of `self.pose_last` automatically
- Extracts translation correctly for both `(4, 4)` and `(1, 4, 4)` shapes
- Maintains backward compatibility with single-frame mask usage
- Works correctly with fallback behavior (when only first frame mask is provided)

**Compatibility**:
The fix is fully compatible with all mask usage scenarios:
- ✅ **First frame mask only** (fallback): Fix only runs when masks are available, skipped otherwise
- ✅ **All frames have masks**: Fix handles both shapes correctly throughout tracking
- ✅ **No masks at all**: Fix never executes, no interference
- ✅ **Mixed mask availability**: Fix only runs when masks are present

**If You Encounter This Error**:
1. **Update your codebase**: Ensure you have the latest version with the fix applied
2. **Check your setup**: Verify mask files exist and are correctly named (see [Naming Conventions](#naming-conventions-and-directory-structure))
3. **Verify fix is applied**: Check `estimater.py` lines 347-367 for the shape detection code

**Technical Details**:
- The error occurs in the mask-based drift detection code
- This code compares the current pose translation with the mask center to detect tracking drift
- When drift is detected (>10% of object diameter), the pose translation is adjusted towards the mask center
- The fix ensures this drift detection works correctly regardless of tensor shape

**Related Documentation**: See `docs/debug/operands_could_not_be_broadcast_together_with_shapes(1,4)(3,).md` for detailed technical analysis.

### Issue: RuntimeError When Adjusting Pose with Masks
**Error Message**:
```
RuntimeError: Inplace update to inference tensor outside InferenceMode is not allowed.
You can make a clone to get a normal tensor before doing inplace update.
```

**Location**: `estimater.py`, line 365 in `track_one()` method

**When It Occurs**:
- ✅ Frame 0 (registration): Works fine
- ✅ Frame 1 (first tracking frame): May work (depending on tensor state)
- ❌ Frame 2+ (subsequent tracking frames): Fails when drift is detected and pose adjustment is attempted

**Root Cause**:
This error occurs after the shape mismatch fix when the code attempts to adjust the pose translation based on mask center. The issue is that `self.pose_last` is an **inference tensor** (created by the refiner model), which PyTorch protects from in-place modifications.

**The Problem**:
1. **Inference tensor from refiner**: `self.pose_last` is set from `pose` returned by `refiner.predict()`, which creates an inference tensor
2. **Inference tensors are read-only**: PyTorch prevents in-place modifications to inference tensors outside of inference mode
3. **In-place modification fails**: When drift is detected, the code tries to modify `self.pose_last[0, :3, 3]` in-place, which PyTorch blocks

**The Fix**:
The code has been updated to clone the inference tensor, converting it to a normal tensor that can be modified:

```python
# Line 378 - After refiner.predict()
pose, vis = self.refiner.predict(...)
# Clone to convert inference tensor to normal tensor, allowing in-place modifications
self.pose_last = pose.clone()
```

**Solution Status**:
✅ **Fixed**: This issue has been resolved in the codebase. The fix:
- Clones the inference tensor when assigning to `self.pose_last`
- Converts inference tensor to normal tensor, allowing safe in-place modifications
- Works correctly with the shape mismatch fix
- Maintains compatibility with all mask usage scenarios

**Why This Happens**:
- PyTorch models run with `torch.inference_mode()` or `torch.no_grad()` create inference tensors
- Inference tensors are read-only to prevent accidental modifications
- When mask-based drift detection adjusts pose translation, it needs to modify the tensor in-place
- Cloning converts the inference tensor to a normal tensor that can be safely modified

**Relationship to Shape Mismatch Error**:
- Both errors occur in the same code section (mask-based drift detection)
- The shape mismatch error occurs when extracting translation from `self.pose_last`
- The RuntimeError occurs when trying to modify `self.pose_last` after drift is detected
- Both fixes work together to enable mask-based pose adjustment

**If You Encounter This Error**:
1. **Update your codebase**: Ensure you have the latest version with both fixes applied
2. **Check tensor cloning**: Verify line 378 in `estimater.py` uses `.clone()`
3. **Verify mask files**: Ensure mask files exist and are correctly named

**Technical Details**:
- Inference tensors are created when models run in inference mode
- PyTorch RFC 17 introduced inference tensor protection
- Cloning is a lightweight operation for small tensors (4x4 or 1x4x4 pose matrices)
- The fix ensures `self.pose_last` is always a normal tensor that can be modified

**Related Documentation**: See `docs/debug/RuntimeError: Inplace update to inference tensor outside InferenceMode is not allowed.md` for detailed technical analysis, code flow diagrams, and multiple solution approaches.

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
- **Naming conventions**: See the [Naming Conventions and Directory Structure](#naming-conventions-and-directory-structure) section for important guidelines on directory and file naming. The script uses component-based path replacement to locate mask files, allowing parent directories to contain 'rgb' in their names safely.
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
