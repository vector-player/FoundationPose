# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


from estimater import *
from datareader import *
import argparse
from datetime import datetime
import shutil


def find_mesh_file(test_scene_dir, mesh_file=None):
  """
  Auto-detect mesh file from test_scene_dir if mesh_file is not explicitly provided.
  
  Search order:
  1. If mesh_file is provided and exists, use it
  2. {test_scene_dir}/mesh/textured_simple.obj (common pattern for demo_data)
  3. {test_scene_dir}/mesh/*.obj (if exactly one .obj file exists)
  4. {test_scene_dir}/../mesh/*.obj (if test_scene_dir is a subdirectory)
  5. Default fallback to demo_data/mustard0/mesh/textured_simple.obj
  
  Returns:
    str: Path to mesh file
  """
  code_dir = os.path.dirname(os.path.realpath(__file__))
  default_mesh = f'{code_dir}/demo_data/mustard0/mesh/textured_simple.obj'
  
  # If mesh_file is explicitly provided and exists, use it
  if mesh_file and os.path.exists(mesh_file):
    return mesh_file
  
  # Normalize test_scene_dir path
  test_scene_dir = os.path.abspath(test_scene_dir)
  
  # Track searched locations for user feedback
  searched_locations = []
  
  # Try common patterns
  candidates = [
    # Pattern 1: {test_scene_dir}/mesh/textured_simple.obj (most common)
    os.path.join(test_scene_dir, 'mesh', 'textured_simple.obj'),
    # Pattern 3: {test_scene_dir}/../mesh/textured_simple.obj (parent directory)
    os.path.join(os.path.dirname(test_scene_dir), 'mesh', 'textured_simple.obj'),
  ]
  
  # Check Pattern 1 and Pattern 3 first
  for candidate in candidates:
    searched_locations.append(candidate)
    if os.path.exists(candidate):
      logging.info(f"[OK] Auto-detected mesh file: {candidate}")
      return candidate
  
  # Pattern 2: Check if there's exactly one .obj file in mesh directory
  mesh_dir = os.path.join(test_scene_dir, 'mesh')
  searched_locations.append(f"{mesh_dir}/*.obj")
  if os.path.isdir(mesh_dir):
    obj_files = [f for f in os.listdir(mesh_dir) if f.endswith('.obj')]
    if len(obj_files) == 1:
      candidate = os.path.join(mesh_dir, obj_files[0])
      logging.info(f"[OK] Auto-detected mesh file: {candidate}")
      return candidate
    elif len(obj_files) > 1:
      logging.warning(f"Found {len(obj_files)} .obj files in {mesh_dir}, cannot auto-select. Please specify --mesh_file")
      logging.info(f"  Available mesh files: {', '.join(obj_files)}")
  
  # Check parent directory mesh folder
  parent_mesh_dir = os.path.join(os.path.dirname(test_scene_dir), 'mesh')
  searched_locations.append(f"{parent_mesh_dir}/*.obj")
  if os.path.isdir(parent_mesh_dir):
    obj_files = [f for f in os.listdir(parent_mesh_dir) if f.endswith('.obj')]
    if len(obj_files) == 1:
      candidate = os.path.join(parent_mesh_dir, obj_files[0])
      logging.info(f"[OK] Auto-detected mesh file: {candidate}")
      return candidate
  
  # Provide helpful hints when mesh file cannot be found
  print("\n" + "="*70)
  print("WARNING: MESH FILE AUTO-DETECTION FAILED")
  print("="*70)
  print(f"Could not find mesh file for input directory: {test_scene_dir}\n")
  print("Searched locations:")
  for i, loc in enumerate(searched_locations, 1):
    exists = os.path.exists(loc) if not loc.endswith('/*.obj') else os.path.isdir(os.path.dirname(loc))
    status = "[EXISTS]" if exists else "[NOT FOUND]"
    print(f"  {i}. {loc} {status}")
  
  # Check if input directory exists and list its contents
  if os.path.isdir(test_scene_dir):
    print(f"\nContents of input directory ({test_scene_dir}):")
    try:
      contents = os.listdir(test_scene_dir)
      if contents:
        for item in sorted(contents)[:10]:  # Show first 10 items
          item_path = os.path.join(test_scene_dir, item)
          item_type = "[DIR]" if os.path.isdir(item_path) else "[FILE]"
          print(f"  {item_type}  {item}")
        if len(contents) > 10:
          print(f"  ... and {len(contents) - 10} more items")
      else:
        print("  (empty directory)")
    except PermissionError:
      print("  (permission denied)")
  else:
    print(f"\nWARNING: input directory does not exist: {test_scene_dir}")
  
  print("\nSUGGESTIONS:")
  print("  1. Create a 'mesh' subdirectory in your input directory and place your .obj file there:")
  print(f"     mkdir -p {test_scene_dir}/mesh")
  print(f"     # Then copy your mesh.obj file to {test_scene_dir}/mesh/")
  print("\n  2. Or specify the mesh file explicitly using --mesh_file:")
  print("     python run.py --mesh_file /path/to/your/mesh.obj --inputs <path>")
  print("     # or")
  print("     python run.py --mesh_file /path/to/your/mesh.obj --test_scene_dir <path>")
  print("\n  3. Expected directory structure:")
  print("     input_directory/")
  print("     ├── rgb/          (RGB images)")
  print("     ├── depth/        (depth images, optional)")
  print("     ├── mesh/         (mesh files)")
  print("     │   └── *.obj")
  print("     └── cam_K.txt     (camera intrinsics)")
  print("="*70 + "\n")
  
  # Fallback to default
  logging.warning(f"Using default mesh file: {default_mesh}")
  logging.warning("This may not match your test scene. Please specify --mesh_file for accurate results.")
  return default_mesh


if __name__=='__main__':
  parser = argparse.ArgumentParser()
  code_dir = os.path.dirname(os.path.realpath(__file__))
  parser.add_argument('--mesh_file', type=str, default=None, help='Path to the 3D mesh file (.obj format). If not provided, will auto-detect from --test_scene_dir or --inputs.')
  parser.add_argument('--test_scene_dir', type=str, default=None, help='Directory containing test scene RGB-D images. Ignored if --inputs is provided.')
  parser.add_argument('--inputs', type=str, default=None, help='Directory containing test scene RGB-D images. Takes precedence over --test_scene_dir if both are provided.')
  parser.add_argument('--outputs', type=str, default=None, help='Output directory for results. Takes precedence over --debug_dir if both are provided. If --inputs is provided but --outputs is not, auto-generates outputs/<timestamp>/ as sibling of inputs.')
  parser.add_argument('--est_refine_iter', type=int, default=5)
  parser.add_argument('--track_refine_iter', type=int, default=2)
  parser.add_argument('--debug', type=int, default=1)
  parser.add_argument('--debug_dir', type=str, default=None, help='Output directory for debug files. Used only if --outputs is not provided.')
  parser.add_argument('--rgb_only', action='store_true', help='Enable RGB-only mode (no depth sensor required). Depth maps will be set to zero and network will use RGB features only.')
  parser.add_argument('--no_masks', action='store_false', dest='use_masks', default=True, help='Disable mask usage for tracking. By default, masks are automatically used if mask files exist in the masks/ directory.')
  args = parser.parse_args()

  set_logging_format()
  set_seed(0)

  # Determine which input directory to use
  # Priority: --inputs > --test_scene_dir > default
  if args.inputs:
    test_scene_dir = args.inputs
    if args.test_scene_dir:
      logging.warning(f"Both --inputs and --test_scene_dir provided. Using --inputs: {args.inputs} (ignoring --test_scene_dir)")
  elif args.test_scene_dir:
    test_scene_dir = args.test_scene_dir
  else:
    test_scene_dir = f'{code_dir}/demo_data/mustard0'
    logging.info(f"No input directory specified, using default: {test_scene_dir}")

  # Determine which output directory to use
  # Priority: --outputs > auto-generated (if inputs given) > --debug_dir > default
  if args.outputs:
    debug_dir = args.outputs
    if args.debug_dir:
      logging.warning(f"Both --outputs and --debug_dir provided. Using --outputs: {args.outputs} (ignoring --debug_dir)")
  elif args.inputs:
    # Auto-generate outputs/<timestamp>/ as sibling of inputs
    inputs_abs = os.path.abspath(args.inputs)
    inputs_parent = os.path.dirname(inputs_abs)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_dir = os.path.join(inputs_parent, 'outputs', timestamp)
    logging.info(f"Auto-generating output directory as sibling of inputs: {debug_dir}")
  elif args.debug_dir:
    debug_dir = args.debug_dir
  else:
    debug_dir = f'{code_dir}/debug'
    logging.info(f"No output directory specified, using default: {debug_dir}")

  # Auto-detect mesh file if not explicitly provided
  mesh_file = find_mesh_file(test_scene_dir, args.mesh_file)
  mesh = trimesh.load(mesh_file)

  debug = args.debug
  
  # Safely clear and recreate output directory
  # Remove existing directory contents if it exists, then create subdirectories
  if os.path.exists(debug_dir):
    shutil.rmtree(debug_dir)
    logging.info(f"Cleared existing output directory: {debug_dir}")
  os.makedirs(f'{debug_dir}/track_vis', exist_ok=True)
  os.makedirs(f'{debug_dir}/ob_in_cam', exist_ok=True)
  logging.info(f"Created output directory structure: {debug_dir}")

  to_origin, extents = trimesh.bounds.oriented_bounds(mesh)
  bbox = np.stack([-extents/2, extents/2], axis=0).reshape(2,3)

  scorer = ScorePredictor()
  refiner = PoseRefinePredictor()
  glctx = dr.RasterizeCudaContext()
  est = FoundationPose(model_pts=mesh.vertices, model_normals=mesh.vertex_normals, mesh=mesh, scorer=scorer, refiner=refiner, debug_dir=debug_dir, debug=debug, glctx=glctx, rgb_only_mode=args.rgb_only)
  logging.info("estimator initialization done")

  reader = YcbineoatReader(video_dir=test_scene_dir, shorter_side=None, zfar=np.inf, rgb_only=args.rgb_only)

  for i in range(len(reader.color_files)):
    logging.info(f'i:{i}')
    color = reader.get_color(i)
    depth = reader.get_depth(i)
    if i==0:
      mask = reader.get_mask(0).astype(bool)
      pose = est.register(K=reader.K, rgb=color, depth=depth, ob_mask=mask, iteration=args.est_refine_iter)

      if debug>=3:
        m = mesh.copy()
        m.apply_transform(pose)
        m.export(f'{debug_dir}/model_tf.obj')
        xyz_map = depth2xyzmap(depth, reader.K)
        valid = depth>=0.001
        pcd = toOpen3dCloud(xyz_map[valid], color[valid])
        o3d.io.write_point_cloud(f'{debug_dir}/scene_complete.ply', pcd)
    else:
      # Get mask for tracking frame (if enabled and available)
      if args.use_masks:
        try:
          mask = reader.get_mask(i).astype(bool)
          pose = est.track_one(rgb=color, depth=depth, K=reader.K, ob_mask=mask, iteration=args.track_refine_iter)
        except (FileNotFoundError, AttributeError) as e:
          # If mask not available, track without mask (backward compatibility)
          logging.info(f"Mask not available for frame {i}, tracking without mask: {e}")
          pose = est.track_one(rgb=color, depth=depth, K=reader.K, iteration=args.track_refine_iter)
      else:
        # Masks disabled, track without masks
        pose = est.track_one(rgb=color, depth=depth, K=reader.K, iteration=args.track_refine_iter)

    os.makedirs(f'{debug_dir}/ob_in_cam', exist_ok=True)
    np.savetxt(f'{debug_dir}/ob_in_cam/{reader.id_strs[i]}.txt', pose.reshape(4,4))

    if debug>=1:
      center_pose = pose@np.linalg.inv(to_origin)
      vis = draw_posed_3d_box(reader.K, img=color, ob_in_cam=center_pose, bbox=bbox)
      vis = draw_xyz_axis(color, ob_in_cam=center_pose, scale=0.1, K=reader.K, thickness=3, transparency=0, is_input_rgb=True)
      cv2.imshow('1', vis[...,::-1])
      cv2.waitKey(1)


    if debug>=2:
      os.makedirs(f'{debug_dir}/track_vis', exist_ok=True)
      imageio.imwrite(f'{debug_dir}/track_vis/{reader.id_strs[i]}.png', vis)

