#!/usr/bin/env python3
"""
Enhanced Standalone Blender Script Generator for FoundationPose - FIXED VERSION
================================================================================
FIXED: Camera positioning to properly replicate original video viewpoint

Key fixes:
1. Use actual camera intrinsics (focal length, principal point)
2. Position camera at origin (since ob_in_cam is object-in-camera coordinates)
3. Use camera's actual focal length and sensor parameters
4. Proper coordinate system interpretation

This should now create animations that look exactly like the original video.
"""

import numpy as np
import os
import glob
import argparse
from pathlib import Path
from datetime import datetime

def extract_pose_data(pose_dir):
    """Extract all pose data from ob_in_cam directory"""
    
    print(f"🔍 Extracting pose data from: {pose_dir}")
    
    if not os.path.exists(pose_dir):
        raise FileNotFoundError(f"Directory not found: {pose_dir}")
    
    pose_files = sorted(glob.glob(os.path.join(pose_dir, "*.txt")))
    
    if not pose_files:
        raise FileNotFoundError(f"No pose files found in {pose_dir}")
    
    pose_data = []
    
    for pose_file in pose_files:
        # Extract frame identifier (handle different naming patterns)
        filename = os.path.basename(pose_file).replace('.txt', '')
        
        # Try different frame number extraction patterns
        if '_' in filename:
            # Pattern: garnier_00170.txt
            frame_str = filename.split('_')[-1]
        else:
            # Pattern: 000000.txt
            frame_str = filename
        
        try:
            frame_number = int(frame_str)
        except ValueError:
            print(f"⚠️  Could not extract frame number from {filename}, skipping")
            continue
        
        # Load pose matrix
        try:
            pose_matrix = np.loadtxt(pose_file).reshape(4, 4)
            pose_data.append((frame_number, pose_matrix))
        except Exception as e:
            print(f"⚠️  Error loading {pose_file}: {e}")
            continue
    
    if not pose_data:
        raise ValueError("No valid pose matrices found")
    
    # Sort by frame number
    pose_data.sort(key=lambda x: x[0])
    
    print(f"✅ Extracted {len(pose_data)} pose matrices")
    print(f"   Frame range: {pose_data[0][0]} to {pose_data[-1][0]}")
    
    return pose_data

def load_camera_intrinsics(cam_K_file):
    """Load camera intrinsics matrix"""
    if not os.path.exists(cam_K_file):
        print(f"⚠️  Camera intrinsics file not found: {cam_K_file}")
        print("   Using default camera parameters")
        return None
    
    try:
        K = np.loadtxt(cam_K_file)
        print(f"✅ Loaded camera intrinsics:")
        print(f"   Focal length: fx={K[0,0]:.1f}, fy={K[1,1]:.1f}")
        print(f"   Principal point: cx={K[0,2]:.1f}, cy={K[1,2]:.1f}")
        print(f"   Image size: ~{K[0,2]*2:.0f}x{K[1,2]*2:.0f} pixels")
        return K
    except Exception as e:
        print(f"⚠️  Error loading camera intrinsics: {e}")
        return None

def format_pose_data_for_python(pose_data):
    """Convert pose data to Python code representation"""
    
    lines = ["# Pose data extracted from FoundationPose ob_in_cam", "POSE_DATA = ["]
    
    for frame_num, pose_matrix in pose_data:
        # Format pose matrix as nested list
        lines.append(f"    ({frame_num}, [")
        for row in pose_matrix:
            row_str = "        [" + ", ".join(f"{val:.6f}" for val in row) + "],"
            lines.append(row_str)
        lines.append("    ]),")
    
    lines.append("]")
    lines.append("")
    
    return "\n".join(lines)

def auto_detect_object_name(pose_dir):
    """Auto-detect object name from directory path or pose filenames"""
    
    # Try to extract from directory path
    parts = Path(pose_dir).parts
    for part in reversed(parts):
        if part in ['garnier', 'bottle', 'mustard', 'hand', 'object', 'maybellene']:
            return part
    
    # Try to extract from pose filenames
    pose_files = glob.glob(os.path.join(pose_dir, "*.txt"))
    if pose_files:
        filename = os.path.basename(pose_files[0])
        if '_' in filename:
            prefix = filename.split('_')[0]
            if len(prefix) > 2:  # Reasonable object name length
                return prefix
    
    return "tracked_object"

def filter_reliable_poses(pose_data):
    """Filter pose data to remove unreliable tracking (large jumps or outliers)"""
    
    if len(pose_data) < 10:
        return pose_data
    
    print(f"🔍 Filtering {len(pose_data)} poses for reliability...")
    
    # Calculate distances from origin
    distances = []
    for frame_num, pose_matrix in pose_data:
        distance = np.linalg.norm(pose_matrix[:3, 3])
        distances.append((frame_num, pose_matrix, distance))
    
    # Calculate statistics
    distance_values = [d[2] for d in distances]
    mean_distance = np.mean(distance_values)
    std_distance = np.std(distance_values)
    
    # Use lenient filtering - only remove extreme outliers that are clearly tracking failures
    max_reasonable_distance = mean_distance + 3 * std_distance  # Very lenient
    min_reasonable_distance = max(0.1, mean_distance - 3 * std_distance)
    
    print(f"   📊 Using lenient filtering: allowing {min_reasonable_distance:.2f}m - {max_reasonable_distance:.2f}m")
    
    # Only detect very sudden large jumps (tracking completely lost)
    filtered_poses = []
    prev_distance = None
    
    for i, (frame_num, pose_matrix, distance) in enumerate(distances):
        # Only filter extreme outliers that are clearly impossible
        if distance > max_reasonable_distance or distance < min_reasonable_distance:
            print(f"   ⚠️  Filtering frame {frame_num}: distance {distance:.2f}m (outside {min_reasonable_distance:.2f}-{max_reasonable_distance:.2f}m)")
            continue
            
        # Only detect massive jumps that indicate complete tracking loss (>10m jump)
        if prev_distance is not None and abs(distance - prev_distance) > 10.0:
            print(f"   ⚠️  Filtering frame {frame_num}: massive jump from {prev_distance:.2f}m to {distance:.2f}m")
            continue
            
        filtered_poses.append((frame_num, pose_matrix))
        prev_distance = distance
    
    print(f"✅ Kept {len(filtered_poses)}/{len(pose_data)} reliable poses")
    print(f"   Distance range: {min([np.linalg.norm(p[1][:3, 3]) for p in filtered_poses]):.2f}m - {max([np.linalg.norm(p[1][:3, 3]) for p in filtered_poses]):.2f}m")
    
    return filtered_poses

def calculate_scene_bounds(pose_data):
    """Calculate scene bounds and optimal visualization settings"""
    
    positions = np.array([pose[1][:3, 3] for pose in pose_data])
    distances = np.array([np.linalg.norm(pos) for pos in positions])
    
    stats = {
        'positions': positions,
        'distances': distances,
        'min_distance': distances.min(),
        'max_distance': distances.max(),
        'mean_distance': distances.mean(),
        'position_bounds': {
            'x_min': positions[:, 0].min(),
            'x_max': positions[:, 0].max(),
            'y_min': positions[:, 1].min(), 
            'y_max': positions[:, 1].max(),
            'z_min': positions[:, 2].min(),
            'z_max': positions[:, 2].max()
        }
    }
    
    # Auto-configure visualization settings based on reliable data
    max_distance = stats['max_distance']
    distance_range = stats['max_distance'] - stats['min_distance']
    
    if max_distance > 10:
        object_size = max_distance * 0.05
        coord_size = max_distance * 0.1
    elif max_distance < 1:
        object_size = 0.02
        coord_size = 0.1
    else:
        object_size = max_distance * 0.03
        coord_size = max_distance * 0.08
    
    stats['visualization'] = {
        'object_size': object_size,
        'coord_size': coord_size
    }
    
    return stats

def generate_blender_script_template(pose_data, object_name, source_info, camera_K=None):
    """Generate the complete Blender script with embedded data and FIXED camera positioning"""
    
    # Filter unreliable poses first
    filtered_pose_data = filter_reliable_poses(pose_data)
    
    # Calculate scene bounds and optimal settings
    scene_stats = calculate_scene_bounds(filtered_pose_data)
    vis_settings = scene_stats['visualization']
    
    # Generate pose data as Python code (using filtered data)
    pose_data_code = format_pose_data_for_python(filtered_pose_data)
    
    # Camera intrinsics code
    if camera_K is not None:
        camera_code = f"""
# Camera intrinsics from FoundationPose data
CAMERA_K = np.array([
    [{camera_K[0,0]:.6f}, {camera_K[0,1]:.6f}, {camera_K[0,2]:.6f}],
    [{camera_K[1,0]:.6f}, {camera_K[1,1]:.6f}, {camera_K[1,2]:.6f}],
    [{camera_K[2,0]:.6f}, {camera_K[2,1]:.6f}, {camera_K[2,2]:.6f}]
])

# Camera parameters
FOCAL_LENGTH_MM = {camera_K[0,0]:.1f}  # Focal length in pixels
SENSOR_WIDTH_MM = 36.0  # Standard sensor width
IMAGE_WIDTH_PX = {camera_K[0,2]*2:.0f}
IMAGE_HEIGHT_PX = {camera_K[1,2]*2:.0f}

# Calculate focal length in mm for Blender
FOCAL_LENGTH_BLENDER_MM = (FOCAL_LENGTH_MM * SENSOR_WIDTH_MM) / IMAGE_WIDTH_PX
"""
    else:
        camera_code = """
# Default camera parameters (no intrinsics file found)
CAMERA_K = None
FOCAL_LENGTH_BLENDER_MM = 35.0  # Default focal length
SENSOR_WIDTH_MM = 36.0
IMAGE_WIDTH_PX = 640
IMAGE_HEIGHT_PX = 480
"""
    
    script_template = f'''#!/usr/bin/env python3
"""
Standalone FoundationPose Blender Animation Script - FIXED VERSION
================================================================
FIXED: Camera positioning to properly replicate original video viewpoint

Generated on: {datetime.now().isoformat()}
Source: {source_info}
Object: {object_name}
Frames: {len(filtered_pose_data)} total ({filtered_pose_data[0][0]} to {filtered_pose_data[-1][0]}) - filtered from {len(pose_data)} original

KEY FIXES:
1. Camera positioned at origin (ob_in_cam coordinates)
2. Uses actual camera intrinsics for focal length
3. Proper coordinate system interpretation
4. Should now look exactly like the original video

Usage in Blender:
1. Open Blender
2. Delete default objects (A → X → Delete)
3. Switch to Scripting workspace
4. Load and run this script (Alt+P)
5. Switch to Animation workspace and press SPACE to play
"""

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector, Euler

# ============================
# EMBEDDED POSE DATA
# ============================

{pose_data_code}

# ============================
# CAMERA INTRINSICS
# ============================

{camera_code}

# ============================
# CONFIGURATION
# ============================

OBJECT_NAME = "{object_name}"
FRAME_RATE = 30
ANIMATION_SPEED = 1.0

# Auto-configured visualization settings
OBJECT_SIZE = {vis_settings['object_size']:.3f}
COORD_SIZE = {vis_settings['coord_size']:.3f}

# Features
MOTION_TRAIL = True
COORDINATE_AXES = True
PROFESSIONAL_LIGHTING = True
OBJECT_REPRESENTATION = True

# Source information (for reference)
SOURCE_INFO = {{
    'generated_on': '{datetime.now().isoformat()}',
    'source_data': '{source_info}',
    'object_name': '{object_name}',
    'total_frames': {len(filtered_pose_data)},
    'original_frames': {len(pose_data)},
    'frame_range': '{filtered_pose_data[0][0]}-{filtered_pose_data[-1][0]}',
    'distance_range': '{scene_stats['min_distance']:.2f}m - {scene_stats['max_distance']:.2f}m',
    'motion_bounds': {{
        'x_range': '[{scene_stats['position_bounds']['x_min']:.2f}, {scene_stats['position_bounds']['x_max']:.2f}]m',
        'y_range': '[{scene_stats['position_bounds']['y_min']:.2f}, {scene_stats['position_bounds']['y_max']:.2f}]m',
        'z_range': '[{scene_stats['position_bounds']['z_min']:.2f}, {scene_stats['position_bounds']['z_max']:.2f}]m'
    }}
}}

# ============================
# COORDINATE SYSTEM CONVERSION
# ============================

def convert_cv_to_blender(cv_matrix):
    """
    Convert OpenCV camera coordinates to Blender coordinates
    
    OpenCV: +X right, +Y down, +Z forward (into scene)
    Blender: +X right, +Y forward, +Z up
    
    FIXED: This properly converts ob_in_cam coordinates to Blender space
    """
    cv_to_blender = Matrix([
        [1,  0,  0,  0],  # X stays the same
        [0,  0,  1,  0],  # Y_blender = Z_opencv  
        [0, -1,  0,  0],  # Z_blender = -Y_opencv
        [0,  0,  0,  1]
    ])
    
    return cv_to_blender @ Matrix(cv_matrix)

def extract_transform_components(pose_matrix):
    """Extract location, rotation, and scale from 4x4 transformation matrix"""
    location, rotation, scale = pose_matrix.decompose()
    rotation = rotation.to_euler()  # Convert quaternion to Euler
    return location, rotation, scale

# ============================
# SCENE SETUP
# ============================

def clear_scene():
    """Clear all objects from the Blender scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Clear orphaned data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

def create_material(name, color=(1, 0, 0, 1)):
    """Create a material with specified color"""
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = color
    return material

def create_fixed_camera():
    """
    FIXED: Create camera positioned to replicate original video viewpoint
    
    Key fixes:
    1. Camera at origin (0,0,0) - ob_in_cam coordinates are relative to camera
    2. Use actual focal length from camera intrinsics
    3. Proper sensor parameters
    4. Rotate 90° around X-axis to align with FoundationPose +Z direction
    5. This should now look exactly like the original video
    """
    
    # FIXED: Camera at origin since ob_in_cam is object-in-camera coordinates
    camera_location = Vector((0, 0, 0))
    
    bpy.ops.object.camera_add(location=camera_location)
    camera = bpy.context.active_object
    camera.name = "FixedCamera"
    
    # FIXED: Use actual focal length from camera intrinsics
    camera.data.lens = FOCAL_LENGTH_BLENDER_MM
    camera.data.sensor_width = SENSOR_WIDTH_MM
    camera.data.sensor_height = SENSOR_WIDTH_MM * (IMAGE_HEIGHT_PX / IMAGE_WIDTH_PX)
    camera.data.clip_start = 0.1
    camera.data.clip_end = 100.0
    
    # FIXED: Camera points along +Z axis (FoundationPose camera direction)
    # Rotate 90 degrees around X-axis to align with FoundationPose coordinate system
    camera.rotation_euler = (np.pi/2, 0, 0)  # 90 degrees around X-axis
    
    print(f"✅ Created FIXED camera: {{camera.name}}")
    print(f"   Position: {{camera_location}} (origin - ob_in_cam coordinates)")
    print(f"   Focal length: {{FOCAL_LENGTH_BLENDER_MM:.1f}}mm (from intrinsics)")
    print(f"   Sensor: {{SENSOR_WIDTH_MM}}x{{camera.data.sensor_height:.1f}}mm")
    print(f"   Image: {{IMAGE_WIDTH_PX}}x{{IMAGE_HEIGHT_PX}} pixels")
    print(f"   Rotation: 90° around X-axis (aligns with FoundationPose +Z direction)")
    print(f"   This should now replicate the original video viewpoint!")
    
    return camera

def create_tracked_object():
    """Create animated object representing tracked target"""
    
    # Create main tracking object (empty for precise positioning)
    bpy.ops.object.empty_add(type='ARROWS', radius=OBJECT_SIZE, location=(0, 0, 0))
    tracked_object = bpy.context.active_object
    tracked_object.name = f"{{OBJECT_NAME}}_TrackedObject"
    
    if OBJECT_REPRESENTATION:
        # Create visual representation with realistic proportions
        bpy.ops.mesh.primitive_cube_add(size=OBJECT_SIZE, location=(0, 0, 0))
        object_cube = bpy.context.active_object
        object_cube.name = f"{{OBJECT_NAME}}_Representation"
        
        # Apply realistic object proportions (adapt based on object type)
        if 'bottle' in OBJECT_NAME.lower() or 'mustard' in OBJECT_NAME.lower():
            # Bottle proportions: taller than wide
            object_cube.scale = (0.6, 0.6, 1.5)
        elif 'garnier' in OBJECT_NAME.lower():
            # Cosmetic bottle proportions
            object_cube.scale = (0.8, 0.8, 1.2)
        else:
            # Generic object proportions
            object_cube.scale = (1.0, 1.0, 1.0)
        
        # Bright green material for clear visibility
        object_material = create_material(f"{{OBJECT_NAME}}_Material", (0, 1, 0, 1))
        object_cube.data.materials.append(object_material)
        
        # Parent cube to empty for precise control
        object_cube.parent = tracked_object
    
    # Add metadata
    tracked_object["object_type"] = "FoundationPose_Tracked_Object"
    tracked_object["source_info"] = str(SOURCE_INFO)
    
    print(f"✅ Created tracked object: {{tracked_object.name}}")
    return tracked_object

def create_coordinate_axes():
    """Create coordinate axes for reference"""
    if not COORDINATE_AXES:
        return
    
    bpy.ops.object.empty_add(type='PLAIN_AXES', radius=COORD_SIZE, location=(0, 0, 0))
    axes = bpy.context.active_object
    axes.name = "CoordinateSystem"
    
    print("✅ Created coordinate axes")
    return axes

def create_professional_lighting():
    """Create professional lighting setup"""
    if not PROFESSIONAL_LIGHTING:
        return
    
    # Sun light for overall illumination
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    sun_light = bpy.context.active_object
    sun_light.name = "SunLight"
    sun_light.data.energy = 3.0
    
    # Area light for ambient lighting
    bpy.ops.object.light_add(type='AREA', location=(-2, -2, 3))
    area_light = bpy.context.active_object
    area_light.name = "AreaLight"
    area_light.data.energy = 2.0
    area_light.data.size = 2.0
    
    print("✅ Created professional lighting")

def setup_scene_properties():
    """Configure scene properties for optimal animation"""
    scene = bpy.context.scene
    
    # Frame rate and timing
    scene.render.fps = FRAME_RATE
    scene.render.fps_base = 1.0
    
    # Unit system
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'METERS'
    
    # Render engine (try modern first, fallback to compatible)
    try:
        scene.render.engine = 'BLENDER_EEVEE'
        scene.eevee.use_ssr = True
        scene.eevee.use_bloom = True
    except:
        try:
            scene.render.engine = 'EEVEE'
        except:
            pass  # Use default engine
    
    print(f"✅ Scene configured: {{FRAME_RATE}} FPS, metric units")

# ============================
# ANIMATION CREATION
# ============================

def create_animation_keyframes(tracked_object):
    """
    FIXED: Create animation keyframes from embedded pose data
    
    Key fix: ob_in_cam data shows object position relative to camera at origin
    This should now create the exact same visual as the original video
    """
    
    # Clear existing keyframes
    if tracked_object.animation_data:
        tracked_object.animation_data_clear()
    
    # Set animation frame range
    frame_start = 1
    frame_end = len(POSE_DATA)
    
    bpy.context.scene.frame_start = frame_start
    bpy.context.scene.frame_end = frame_end
    bpy.context.scene.frame_set(frame_start)
    
    print(f"🎬 Creating FIXED animation:")
    print(f"   Source frames: {{POSE_DATA[0][0]}} to {{POSE_DATA[-1][0]}}")
    print(f"   Blender frames: {{frame_start}} to {{frame_end}}")
    print(f"   FIXED: Camera at origin, object moves as in ob_in_cam data")
    print(f"   This should now replicate the original video exactly!")
    
    # Create keyframes using FIXED methodology
    object_positions = []
    
    for i, (source_frame, pose_matrix) in enumerate(POSE_DATA):
        blender_frame = i + 1
        
        # Convert pose to Blender coordinate system
        blender_matrix = convert_cv_to_blender(pose_matrix)
        
        # CRITICAL: Set frame BEFORE setting object transform
        bpy.context.scene.frame_set(blender_frame)
        
        # FIXED: Use ob_in_cam data directly (object position relative to camera)
        object_location = blender_matrix.translation
        object_rotation = blender_matrix.to_euler('XYZ')
        
        # Set object transform
        tracked_object.location = object_location
        tracked_object.rotation_euler = object_rotation
        
        # Insert keyframes with explicit frame numbers
        tracked_object.keyframe_insert(data_path="location", frame=blender_frame)
        tracked_object.keyframe_insert(data_path="rotation_euler", frame=blender_frame)
        
        # Store position for path visualization
        object_positions.append(object_location.copy())
        
        # Progress feedback
        if i % 50 == 0 or i == len(POSE_DATA) - 1:
            distance = np.linalg.norm(np.array(pose_matrix)[:3, 3])
            print(f"   Frame {{blender_frame:3d}}: Source {{source_frame}} | Pos {{object_location}} | Dist {{distance:.2f}}m")
    
    # Set linear interpolation for smooth motion
    if tracked_object.animation_data and tracked_object.animation_data.action:
        for fcurve in tracked_object.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = 'LINEAR'
    
    print(f"✅ Created {{len(POSE_DATA)}} keyframes with linear interpolation")
    return object_positions

def create_motion_path_visualization(object_positions):
    """Create motion path visualization using curve object"""
    if not MOTION_TRAIL or len(object_positions) < 2:
        return
    
    try:
        # Create curve for motion path
        curve_data = bpy.data.curves.new(name=f"{{OBJECT_NAME}}_Path", type='CURVE')
        curve_data.dimensions = '3D'
        curve_obj = bpy.data.objects.new(f"{{OBJECT_NAME}}_Path", curve_data)
        bpy.context.collection.objects.link(curve_obj)
        
        # Add points to curve
        spline = curve_data.splines.new(type='POLY')
        spline.points.add(len(object_positions) - 1)
        
        for i, pos in enumerate(object_positions):
            spline.points[i].co = (*pos, 1.0)
        
        # Visual properties
        curve_data.bevel_depth = OBJECT_SIZE * 0.02
        curve_data.bevel_resolution = 3
        
        # Red material for path
        path_material = create_material(f"{{OBJECT_NAME}}_PathMaterial", (1, 0, 0, 1))
        curve_obj.data.materials.append(path_material)
        
        print("✅ Motion path visualization created")
        return curve_obj
    
    except Exception as e:
        print(f"⚠️  Motion path creation failed: {{e}}")
        return None

# ============================
# MAIN EXECUTION
# ============================

def create_foundationpose_animation():
    """Main function to create the complete FoundationPose animation with FIXED camera"""
    
    print("🚀 Starting FoundationPose Blender Animation - FIXED VERSION")
    print("=" * 60)
    print(f"📊 Data Summary:")
    print(f"   Object: {{OBJECT_NAME}}")
    print(f"   Frames: {{len(POSE_DATA)}} total")
    print(f"   Range: {{POSE_DATA[0][0]}} to {{POSE_DATA[-1][0]}}")
    print(f"   Distance: {{SOURCE_INFO['distance_range']}}")
    print(f"   FIXED: Camera at origin, proper focal length")
    print("=" * 60)
    
    try:
        # 1. Clear scene
        print("1️⃣ Clearing scene...")
        clear_scene()
        
        # 2. Setup scene properties
        print("2️⃣ Setting up scene...")
        setup_scene_properties()
        
        # 3. Create objects
        print("3️⃣ Creating scene objects...")
        camera = create_fixed_camera()  # FIXED: Proper camera positioning
        tracked_object = create_tracked_object()
        create_coordinate_axes()
        create_professional_lighting()
        
        # 4. Create animation (FIXED: Camera at origin, object moves as in ob_in_cam)
        print("4️⃣ Creating FIXED animation keyframes...")
        object_positions = create_animation_keyframes(tracked_object)
        
        # 5. Create motion visualization
        print("5️⃣ Setting up motion visualization...")
        create_motion_path_visualization(object_positions)
        
        # 6. Final setup
        print("6️⃣ Final configuration...")
        bpy.context.scene.camera = camera
        bpy.context.scene.frame_set(1)
        
        # Set viewport shading
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'SOLID'
                        break
        
        # Add scene info text to show animation details in viewport
        bpy.ops.object.text_add(location=(0, 0, 2))
        text_obj = bpy.context.active_object
        text_obj.name = "FoundationPose_SceneInfo"
        text_obj.data.body = f"FoundationPose Animation - FIXED\\n{{OBJECT_NAME}}\\nFrames: {{len(POSE_DATA)}}\\nCamera: Origin + {{FOCAL_LENGTH_BLENDER_MM:.1f}}mm"
        
        # Make the text well-sized and positioned for viewport visibility  
        text_obj.scale = (0.5, 0.5, 0.5)  # Good readable size
        print(f"📝 Scene info text created showing: FoundationPose Animation - FIXED | {{OBJECT_NAME}} | {{len(POSE_DATA)}} frames")
        
        print("=" * 60)
        print("🎉 FoundationPose Animation Created Successfully - FIXED VERSION!")
        print(f"📊 Scene Summary:")
        print(f"   📹 Camera: {{camera.name}} (FIXED: at origin with proper focal length)")
        print(f"   🎯 Tracked object: {{tracked_object.name}}")
        print(f"   🎬 Animation: {{len(POSE_DATA)}} frames at {{FRAME_RATE}} FPS")
        print(f"   📏 Motion range: {{SOURCE_INFO['distance_range']}}")
        print(f"   🛤️  Motion path: Red curve showing 3D trajectory")
        print(f"   🎥 FIXED: Should now look exactly like the original video!")
        print("")
        print("▶️  Press SPACE to play animation")
        print("🔄 Use timeline scrubber to navigate frames")
        print("👁️  Change viewport shading for different views")
        print("📐 Use Numpad keys for different camera angles:")
        print("   Numpad 1: Front view")
        print("   Numpad 3: Side view")
        print("   Numpad 7: Top view")
        print("   Numpad 0: Camera view (should match original video)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating animation: {{e}}")
        import traceback
        traceback.print_exc()
        return False

# ============================
# EXECUTE SCRIPT
# ============================

if __name__ == "__main__":
    # Check if running in Blender
    try:
        import bpy
        create_foundationpose_animation()
    except ImportError:
        print("❌ This script must be run inside Blender!")
        print("1. Open Blender")
        print("2. Go to Scripting workspace")
        print("3. Load and run this script")
        print("4. Switch to Animation workspace and press SPACE")
'''
    
    return script_template

def main():
    parser = argparse.ArgumentParser(description='Generate FIXED standalone Blender script with proper camera positioning')
    parser.add_argument('--input', type=str, required=True,
                       help='Path to ob_in_cam directory containing pose matrices')
    parser.add_argument('--object_name', type=str, default=None,
                       help='Name of tracked object (auto-detected if not provided)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output filename for Blender script (default: auto-generated)')
    parser.add_argument('--camera_intrinsics', type=str, default=None,
                       help='Path to camera intrinsics file (cam_K.txt)')
    
    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.exists(args.input):
        print(f"❌ Input directory not found: {args.input}")
        return
    
    print("🔄 Generating FIXED Standalone Blender Script")
    print("=" * 60)
    
    # Extract pose data
    try:
        pose_data = extract_pose_data(args.input)
    except Exception as e:
        print(f"❌ Error extracting pose data: {e}")
        return
    
    # Load camera intrinsics
    camera_K = None
    if args.camera_intrinsics:
        camera_K = load_camera_intrinsics(args.camera_intrinsics)
    else:
        # Try to auto-detect camera intrinsics
        possible_cam_files = [
            "demo_data/mustard0/cam_K.txt",
            "demo_data/garnier/cam_K.txt",
            os.path.join(os.path.dirname(args.input), "../cam_K.txt"),
            os.path.join(os.path.dirname(args.input), "../../cam_K.txt"),
        ]
        
        for cam_file in possible_cam_files:
            if os.path.exists(cam_file):
                camera_K = load_camera_intrinsics(cam_file)
                break
    
    # Auto-detect object name if not provided
    if args.object_name is None:
        args.object_name = auto_detect_object_name(args.input)
    
    print(f"🎯 Object name: {args.object_name}")
    
    # Generate output filename if not provided
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"blender_{args.object_name}_animation_FIXED_{timestamp}.py"
    
    # Calculate scene statistics for summary
    scene_stats = calculate_scene_bounds(pose_data)
    
    # Generate script (filtering will happen inside the template function)
    print(f"📝 Generating FIXED Blender script...")
    original_count = len(pose_data)
    script_content = generate_blender_script_template(
        pose_data, 
        args.object_name, 
        args.input,
        camera_K
    )
    
    # Calculate final filtered count for summary
    filtered_pose_data = filter_reliable_poses(pose_data)
    filtered_count = len(filtered_pose_data)
    
    # Write script file
    try:
        with open(args.output, 'w') as f:
            f.write(script_content)
        
        print(f"✅ FIXED standalone Blender script created: {args.output}")
        print(f"📊 Script contains:")
        print(f"   📈 {filtered_count} reliable pose matrices (filtered from {original_count} original)")
        print(f"   🎬 Frame range: {filtered_pose_data[0][0]} to {filtered_pose_data[-1][0]}")
        
        # Calculate filtered scene stats for display
        filtered_scene_stats = calculate_scene_bounds(filtered_pose_data)
        print(f"   📏 Distance range: {filtered_scene_stats['min_distance']:.2f}m - {filtered_scene_stats['max_distance']:.2f}m")
        print(f"   📁 Size: {os.path.getsize(args.output) / 1024:.1f} KB")
        
        if filtered_count < original_count:
            print(f"   🚨 Removed {original_count - filtered_count} unreliable poses (likely tracking loss)")
        print("")
        print("🚀 FIXED Features:")
        print("   ✅ FIXED: Camera positioned at origin (ob_in_cam coordinates)")
        print("   ✅ FIXED: Uses actual camera intrinsics for focal length")
        print("   ✅ FIXED: Proper coordinate system interpretation")
        print("   ✅ FIXED: Should now replicate original video viewpoint exactly")
        print("   ✅ Intelligent pose filtering to remove unreliable tracking data")  
        print("   ✅ Clean scene start with informative text overlay")
        print("   ✅ Fixed animation keyframes with proper frame timing")
        print("   ✅ Professional lighting setup")
        print("   ✅ Object representation with realistic proportions")
        print("   ✅ Motion path visualization")
        print("   ✅ Auto-configured scene based on reliable motion bounds")
        print("")
        print("🎯 Usage Instructions:")
        print(f"1. Copy {args.output} to your Blender machine")
        print("2. Open Blender")
        print("3. Delete default objects (A → X → Delete)")
        print("4. Switch to Scripting workspace")
        print(f"5. Load {args.output} in the text editor")
        print("6. Click 'Run Script' or press Alt+P")
        print("7. Switch to Animation workspace")
        print("8. Press SPACE to play the animation!")
        print("9. Press Numpad 0 for camera view (should match original video)")
        
    except Exception as e:
        print(f"❌ Error writing script file: {e}")
        return

if __name__ == "__main__":
    main() 