# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

"""
Comparison script to evaluate tracking quality with and without masks.

This script runs tracking twice on the same sequence:
1. Without masks (baseline)
2. With masks (experimental)

It then compares the results using various metrics.
"""

import sys
import os
code_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, code_dir)

from estimater import *
from datareader import *
import argparse
from datetime import datetime
import shutil
import json
import numpy as np
from scipy.spatial.transform import Rotation as R
from Utils import *


def compute_pose_errors(pose_pred, pose_gt, model_pts):
    """
    Compute pose errors between predicted and ground truth poses.
    
    @pose_pred: Predicted pose (4,4)
    @pose_gt: Ground truth pose (4,4)
    @model_pts: Model points (N,3)
    
    Returns:
        trans_error: Translation error (meters)
        rot_error: Rotation error (degrees)
        add_error: ADD error (meters)
    """
    if pose_gt is None:
        return None, None, None
    
    # Translation error
    trans_error = np.linalg.norm(pose_pred[:3, 3] - pose_gt[:3, 3])
    
    # Rotation error (angle between rotation matrices)
    R_pred = pose_pred[:3, :3]
    R_gt = pose_gt[:3, :3]
    R_diff = R_pred @ R_gt.T
    trace = np.trace(R_diff)
    trace = np.clip(trace, -1, 3)  # Clamp for numerical stability
    rot_error = np.arccos((trace - 1) / 2) * 180 / np.pi
    
    # ADD error (Average Distance of Model Points)
    pred_pts = transform_pts(model_pts, pose_pred)
    gt_pts = transform_pts(model_pts, pose_gt)
    add_error = np.mean(np.linalg.norm(pred_pts - gt_pts, axis=1))
    
    return trans_error, rot_error, add_error


def compute_tracking_stability(poses):
    """
    Compute tracking stability metrics from pose sequence.
    
    @poses: List of poses (N, 4, 4)
    
    Returns:
        trans_variance: Variance of translation across frames
        rot_variance: Variance of rotation angles across frames
        frame_to_frame_trans: Average frame-to-frame translation change
        frame_to_frame_rot: Average frame-to-frame rotation change
    """
    if len(poses) < 2:
        return None, None, None, None
    
    translations = np.array([p[:3, 3] for p in poses])
    trans_variance = np.var(translations, axis=0).mean()
    
    rotations = np.array([R.from_matrix(p[:3, :3]).as_euler('xyz', degrees=True) for p in poses])
    rot_variance = np.var(rotations, axis=0).mean()
    
    # Frame-to-frame changes
    frame_to_frame_trans = []
    frame_to_frame_rot = []
    for i in range(1, len(poses)):
        trans_diff = np.linalg.norm(translations[i] - translations[i-1])
        frame_to_frame_trans.append(trans_diff)
        
        R_diff = poses[i][:3, :3] @ poses[i-1][:3, :3].T
        trace = np.trace(R_diff)
        trace = np.clip(trace, -1, 3)
        rot_diff = np.arccos((trace - 1) / 2) * 180 / np.pi
        frame_to_frame_rot.append(rot_diff)
    
    avg_frame_to_frame_trans = np.mean(frame_to_frame_trans) if frame_to_frame_trans else None
    avg_frame_to_frame_rot = np.mean(frame_to_frame_rot) if frame_to_frame_rot else None
    
    return trans_variance, rot_variance, avg_frame_to_frame_trans, avg_frame_to_frame_rot


def run_tracking_sequence(reader, est, mesh, use_mask=False, est_refine_iter=5, track_refine_iter=2, debug=1, debug_dir=None):
    """
    Run tracking on a sequence with or without masks.
    
    @reader: Data reader instance
    @est: FoundationPose estimator instance
    @mesh: Mesh object
    @use_mask: Whether to use masks during tracking
    @est_refine_iter: Refinement iterations for registration
    @track_refine_iter: Refinement iterations for tracking
    @debug: Debug level
    @debug_dir: Debug directory
    
    Returns:
        poses: List of poses (N, 4, 4)
        errors: List of pose errors if GT available
    """
    poses = []
    errors = []
    
    # Reset estimator state
    est.pose_last = None
    
    for i in range(len(reader.color_files)):
        logging.info(f'Frame {i}/{len(reader.color_files)}, use_mask={use_mask}')
        color = reader.get_color(i)
        depth = reader.get_depth(i)
        
        if i == 0:
            # Registration
            mask = reader.get_mask(0).astype(bool)
            pose = est.register(K=reader.K, rgb=color, depth=depth, ob_mask=mask, iteration=est_refine_iter)
        else:
            # Tracking
            if use_mask:
                try:
                    mask = reader.get_mask(i).astype(bool)
                    pose = est.track_one(rgb=color, depth=depth, K=reader.K, ob_mask=mask, iteration=track_refine_iter)
                except (FileNotFoundError, AttributeError) as e:
                    logging.warning(f"Mask not available for frame {i}, using without mask: {e}")
                    pose = est.track_one(rgb=color, depth=depth, K=reader.K, iteration=track_refine_iter)
            else:
                pose = est.track_one(rgb=color, depth=depth, K=reader.K, iteration=track_refine_iter)
        
        poses.append(pose)
        
        # Compute errors if GT available
        try:
            gt_pose = reader.get_gt_pose(i)
            if gt_pose is not None:
                trans_err, rot_err, add_err = compute_pose_errors(pose, gt_pose, mesh.vertices)
                errors.append({
                    'frame': i,
                    'trans_error': trans_err,
                    'rot_error': rot_err,
                    'add_error': add_err
                })
        except:
            pass
    
    return poses, errors


def compare_tracking_results(poses_no_mask, poses_with_mask, errors_no_mask=None, errors_with_mask=None, output_dir=None):
    """
    Compare tracking results and generate report.
    
    @poses_no_mask: Poses from tracking without masks
    @poses_with_mask: Poses from tracking with masks
    @errors_no_mask: Pose errors without masks (if GT available)
    @errors_with_mask: Pose errors with masks (if GT available)
    @output_dir: Output directory for results
    """
    results = {
        'num_frames': len(poses_no_mask),
        'stability_no_mask': {},
        'stability_with_mask': {},
        'comparison': {}
    }
    
    # Compute stability metrics
    if len(poses_no_mask) > 1:
        trans_var_no, rot_var_no, f2f_trans_no, f2f_rot_no = compute_tracking_stability(poses_no_mask)
        results['stability_no_mask'] = {
            'translation_variance': float(trans_var_no) if trans_var_no is not None else None,
            'rotation_variance': float(rot_var_no) if rot_var_no is not None else None,
            'frame_to_frame_trans': float(f2f_trans_no) if f2f_trans_no is not None else None,
            'frame_to_frame_rot': float(f2f_rot_no) if f2f_rot_no is not None else None
        }
    
    if len(poses_with_mask) > 1:
        trans_var_with, rot_var_with, f2f_trans_with, f2f_rot_with = compute_tracking_stability(poses_with_mask)
        results['stability_with_mask'] = {
            'translation_variance': float(trans_var_with) if trans_var_with is not None else None,
            'rotation_variance': float(rot_var_with) if rot_var_with is not None else None,
            'frame_to_frame_trans': float(f2f_trans_with) if f2f_trans_with is not None else None,
            'frame_to_frame_rot': float(f2f_rot_with) if f2f_rot_with is not None else None
        }
    
    # Compare stability
    if results['stability_no_mask'] and results['stability_with_mask']:
        results['comparison']['stability'] = {
            'translation_variance_improvement': (
                results['stability_no_mask']['translation_variance'] - 
                results['stability_with_mask']['translation_variance']
            ) if results['stability_no_mask']['translation_variance'] and results['stability_with_mask']['translation_variance'] else None,
            'rotation_variance_improvement': (
                results['stability_no_mask']['rotation_variance'] - 
                results['stability_with_mask']['rotation_variance']
            ) if results['stability_no_mask']['rotation_variance'] and results['stability_with_mask']['rotation_variance'] else None,
            'frame_to_frame_trans_improvement': (
                results['stability_no_mask']['frame_to_frame_trans'] - 
                results['stability_with_mask']['frame_to_frame_trans']
            ) if results['stability_no_mask']['frame_to_frame_trans'] and results['stability_with_mask']['frame_to_frame_trans'] else None,
            'frame_to_frame_rot_improvement': (
                results['stability_no_mask']['frame_to_frame_rot'] - 
                results['stability_with_mask']['frame_to_frame_rot']
            ) if results['stability_no_mask']['frame_to_frame_rot'] and results['stability_with_mask']['frame_to_frame_rot'] else None
        }
    
    # Compare pose errors if GT available
    if errors_no_mask and errors_with_mask:
        avg_trans_err_no = np.mean([e['trans_error'] for e in errors_no_mask])
        avg_rot_err_no = np.mean([e['rot_error'] for e in errors_no_mask])
        avg_add_err_no = np.mean([e['add_error'] for e in errors_no_mask])
        
        avg_trans_err_with = np.mean([e['trans_error'] for e in errors_with_mask])
        avg_rot_err_with = np.mean([e['rot_error'] for e in errors_with_mask])
        avg_add_err_with = np.mean([e['add_error'] for e in errors_with_mask])
        
        results['comparison']['pose_errors'] = {
            'avg_trans_error_no_mask': float(avg_trans_err_no),
            'avg_trans_error_with_mask': float(avg_trans_err_with),
            'trans_error_improvement': float(avg_trans_err_no - avg_trans_err_with),
            'avg_rot_error_no_mask': float(avg_rot_err_no),
            'avg_rot_error_with_mask': float(avg_rot_err_with),
            'rot_error_improvement': float(avg_rot_err_no - avg_rot_err_with),
            'avg_add_error_no_mask': float(avg_add_err_no),
            'avg_add_error_with_mask': float(avg_add_err_with),
            'add_error_improvement': float(avg_add_err_no - avg_add_err_with)
        }
    
    # Save results
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        results_file = os.path.join(output_dir, 'comparison_results.json')
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        logging.info(f"Results saved to {results_file}")
        
        # Save poses
        np.save(os.path.join(output_dir, 'poses_no_mask.npy'), np.array(poses_no_mask))
        np.save(os.path.join(output_dir, 'poses_with_mask.npy'), np.array(poses_with_mask))
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Compare tracking with and without masks')
    parser.add_argument('--inputs', type=str, required=True, help='Input directory containing RGB-D images')
    parser.add_argument('--mesh_file', type=str, default=None, help='Path to mesh file')
    parser.add_argument('--outputs', type=str, default=None, help='Output directory for comparison results')
    parser.add_argument('--est_refine_iter', type=int, default=5, help='Refinement iterations for registration')
    parser.add_argument('--track_refine_iter', type=int, default=2, help='Refinement iterations for tracking')
    parser.add_argument('--debug', type=int, default=1, help='Debug level')
    parser.add_argument('--rgb_only', action='store_true', help='RGB-only mode')
    args = parser.parse_args()
    
    set_logging_format()
    set_seed(0)
    
    code_dir = os.path.dirname(os.path.realpath(__file__))
    code_dir = os.path.dirname(code_dir)  # Go up one level from experiments/
    
    # Determine output directory
    if args.outputs:
        output_dir = args.outputs
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(code_dir, 'experiments', 'mask_comparison', timestamp)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Find mesh file
    import sys
    sys.path.insert(0, code_dir)
    from run import find_mesh_file
    mesh_file = find_mesh_file(args.inputs, args.mesh_file)
    mesh = trimesh.load(mesh_file)
    
    # Initialize estimators with separate instances for proper isolation
    scorer_no_mask = ScorePredictor()
    refiner_no_mask = PoseRefinePredictor()
    glctx_no_mask = dr.RasterizeCudaContext()
    est_no_mask = FoundationPose(
        model_pts=mesh.vertices, 
        model_normals=mesh.vertex_normals, 
        mesh=mesh, 
        scorer=scorer_no_mask, 
        refiner=refiner_no_mask, 
        debug_dir=os.path.join(output_dir, 'debug_no_mask'), 
        debug=args.debug, 
        glctx=glctx_no_mask, 
        rgb_only_mode=args.rgb_only
    )
    
    scorer_with_mask = ScorePredictor()
    refiner_with_mask = PoseRefinePredictor()
    glctx_with_mask = dr.RasterizeCudaContext()
    est_with_mask = FoundationPose(
        model_pts=mesh.vertices, 
        model_normals=mesh.vertex_normals, 
        mesh=mesh, 
        scorer=scorer_with_mask, 
        refiner=refiner_with_mask, 
        debug_dir=os.path.join(output_dir, 'debug_with_mask'), 
        debug=args.debug, 
        glctx=glctx_with_mask, 
        rgb_only_mode=args.rgb_only
    )
    
    # Initialize reader
    reader = YcbineoatReader(video_dir=args.inputs, shorter_side=None, zfar=np.inf, rgb_only=args.rgb_only)
    
    logging.info("Running tracking WITHOUT masks...")
    poses_no_mask, errors_no_mask = run_tracking_sequence(
        reader, est_no_mask, mesh, 
        use_mask=False, 
        est_refine_iter=args.est_refine_iter,
        track_refine_iter=args.track_refine_iter,
        debug=args.debug,
        debug_dir=os.path.join(output_dir, 'debug_no_mask')
    )
    
    logging.info("Running tracking WITH masks...")
    poses_with_mask, errors_with_mask = run_tracking_sequence(
        reader, est_with_mask, mesh, 
        use_mask=True, 
        est_refine_iter=args.est_refine_iter,
        track_refine_iter=args.track_refine_iter,
        debug=args.debug,
        debug_dir=os.path.join(output_dir, 'debug_with_mask')
    )
    
    logging.info("Comparing results...")
    results = compare_tracking_results(
        poses_no_mask, poses_with_mask, 
        errors_no_mask, errors_with_mask,
        output_dir=output_dir
    )
    
    # Print summary
    print("\n" + "="*70)
    print("TRACKING COMPARISON RESULTS")
    print("="*70)
    print(f"Number of frames: {results['num_frames']}")
    
    if results['comparison'].get('stability'):
        print("\nStability Comparison:")
        stability = results['comparison']['stability']
        for key, value in stability.items():
            if value is not None:
                print(f"  {key}: {value:.6f}")
    
    if results['comparison'].get('pose_errors'):
        print("\nPose Error Comparison:")
        errors = results['comparison']['pose_errors']
        print(f"  Translation error (no mask): {errors['avg_trans_error_no_mask']:.6f} m")
        print(f"  Translation error (with mask): {errors['avg_trans_error_with_mask']:.6f} m")
        print(f"  Translation improvement: {errors['trans_error_improvement']:.6f} m")
        print(f"  Rotation error (no mask): {errors['avg_rot_error_no_mask']:.6f} deg")
        print(f"  Rotation error (with mask): {errors['avg_rot_error_with_mask']:.6f} deg")
        print(f"  Rotation improvement: {errors['rot_error_improvement']:.6f} deg")
        print(f"  ADD error (no mask): {errors['avg_add_error_no_mask']:.6f} m")
        print(f"  ADD error (with mask): {errors['avg_add_error_with_mask']:.6f} m")
        print(f"  ADD improvement: {errors['add_error_improvement']:.6f} m")
    
    print(f"\nResults saved to: {output_dir}")
    print("="*70)


if __name__ == '__main__':
    main()
