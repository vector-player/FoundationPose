#!/usr/bin/env python3
"""
Depth Image Comparison Tool

This script compares depth images from two directories and generates:
- Statistical metrics (MSE, MAE, SSIM, etc.)
- Visual comparison diagrams
- Difference heatmaps
- Summary report
"""

import argparse
import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr
import json
from tqdm import tqdm


def load_depth_image(img_path, is_reference=False):
    """
    Load depth image, handling different formats.
    
    Args:
        img_path: Path to the depth image
        is_reference: If True, expects 16-bit grayscale. If False, expects RGB colorized depth.
    
    Returns:
        Normalized depth array (0-1 range) and original depth values
    """
    img = cv2.imread(str(img_path), cv2.IMREAD_UNCHANGED)
    
    if img is None:
        return None, None
    
    if is_reference:
        # Reference images are 16-bit grayscale
        depth = img.astype(np.float32)
        # Normalize to 0-1 range
        depth_normalized = depth / depth.max() if depth.max() > 0 else depth
        return depth_normalized, depth
    else:
        # Generated images are RGB colorized depth maps
        # Convert RGB to grayscale
        if len(img.shape) == 3:
            # Convert RGB to grayscale (using luminance formula)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        depth = gray.astype(np.float32)
        # Normalize to 0-1 range
        depth_normalized = depth / 255.0 if depth.max() > 0 else depth
        return depth_normalized, depth


def calculate_metrics(depth1, depth2):
    """
    Calculate various comparison metrics between two depth images.
    
    Args:
        depth1: First depth image (normalized 0-1)
        depth2: Second depth image (normalized 0-1)
    
    Returns:
        Dictionary of metrics
    """
    # Ensure same shape
    if depth1.shape != depth2.shape:
        # Resize depth2 to match depth1
        depth2 = cv2.resize(depth2, (depth1.shape[1], depth1.shape[0]), interpolation=cv2.INTER_LINEAR)
    
    # Flatten for some calculations
    flat1 = depth1.flatten()
    flat2 = depth2.flatten()
    
    # Remove invalid pixels (zeros or NaNs)
    valid_mask = (flat1 > 0) & (flat2 > 0) & ~np.isnan(flat1) & ~np.isnan(flat2)
    valid1 = flat1[valid_mask]
    valid2 = flat2[valid_mask]
    
    if len(valid1) == 0:
        return {
            'mse': np.nan,
            'mae': np.nan,
            'rmse': np.nan,
            'ssim': np.nan,
            'psnr': np.nan,
            'correlation': np.nan,
            'valid_pixels': 0,
            'total_pixels': len(flat1)
        }
    
    # Mean Squared Error
    mse = np.mean((valid1 - valid2) ** 2)
    
    # Mean Absolute Error
    mae = np.mean(np.abs(valid1 - valid2))
    
    # Root Mean Squared Error
    rmse = np.sqrt(mse)
    
    # Structural Similarity Index
    try:
        # Reshape masks back to image shape
        mask_2d = valid_mask.reshape(depth1.shape)
        ref_masked = depth1.copy()
        gen_masked = depth2.copy()
        ref_masked[~mask_2d] = 0
        gen_masked[~mask_2d] = 0
        ssim_value = ssim(ref_masked, gen_masked, data_range=1.0)
        if np.isnan(ssim_value):
            ssim_value = None
    except Exception as e:
        ssim_value = None
    
    # Peak Signal-to-Noise Ratio
    try:
        psnr_value = psnr(valid1, valid2, data_range=1.0)
    except:
        psnr_value = np.nan
    
    # Correlation coefficient
    correlation = np.corrcoef(valid1, valid2)[0, 1] if len(valid1) > 1 else np.nan
    
    return {
        'mse': float(mse),
        'mae': float(mae),
        'rmse': float(rmse),
        'ssim': float(ssim_value) if not np.isnan(ssim_value) else None,
        'psnr': float(psnr_value) if not np.isnan(psnr_value) else None,
        'correlation': float(correlation) if not np.isnan(correlation) else None,
        'valid_pixels': int(len(valid1)),
        'total_pixels': int(len(flat1))
    }


def create_comparison_visualization(img1, img2, diff, metrics, output_path):
    """
    Create a comprehensive visualization comparing two depth images.
    
    Args:
        img1: First depth image
        img2: Second depth image
        diff: Difference image
        metrics: Dictionary of metrics
        output_path: Path to save the visualization
    """
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Depth Image Comparison', fontsize=16, fontweight='bold')
    
    # Original depth (reference)
    im1 = axes[0, 0].imshow(img1, cmap='viridis', vmin=0, vmax=1)
    axes[0, 0].set_title('Reference Depth (16-bit grayscale)', fontsize=12)
    axes[0, 0].axis('off')
    plt.colorbar(im1, ax=axes[0, 0], fraction=0.046)
    
    # Generated depth
    im2 = axes[0, 1].imshow(img2, cmap='viridis', vmin=0, vmax=1)
    axes[0, 1].set_title('Generated Depth (RGB colorized)', fontsize=12)
    axes[0, 1].axis('off')
    plt.colorbar(im2, ax=axes[0, 1], fraction=0.046)
    
    # Absolute difference
    im3 = axes[0, 2].imshow(np.abs(diff), cmap='hot', vmin=0, vmax=1)
    axes[0, 2].set_title('Absolute Difference', fontsize=12)
    axes[0, 2].axis('off')
    plt.colorbar(im3, ax=axes[0, 2], fraction=0.046)
    
    # Difference heatmap
    im4 = axes[1, 0].imshow(diff, cmap='RdBu_r', vmin=-1, vmax=1)
    axes[1, 0].set_title('Difference (Reference - Generated)', fontsize=12)
    axes[1, 0].axis('off')
    plt.colorbar(im4, ax=axes[1, 0], fraction=0.046)
    
    # Histogram comparison
    axes[1, 1].hist(img1.flatten(), bins=50, alpha=0.5, label='Reference', color='blue', density=True)
    axes[1, 1].hist(img2.flatten(), bins=50, alpha=0.5, label='Generated', color='red', density=True)
    axes[1, 1].set_title('Depth Value Distribution', fontsize=12)
    axes[1, 1].set_xlabel('Normalized Depth Value')
    axes[1, 1].set_ylabel('Density')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    # Metrics text
    axes[1, 2].axis('off')
    ssim_str = f"{metrics['ssim']:.4f}" if metrics['ssim'] is not None else 'N/A'
    psnr_str = f"{metrics['psnr']:.2f}" if metrics['psnr'] is not None else 'N/A'
    corr_str = f"{metrics['correlation']:.4f}" if metrics['correlation'] is not None else 'N/A'
    
    metrics_text = f"""
    Comparison Metrics:
    
    MSE:  {metrics['mse']:.6f}
    MAE:  {metrics['mae']:.6f}
    RMSE: {metrics['rmse']:.6f}
    
    SSIM: {ssim_str}
    PSNR: {psnr_str}
    
    Correlation: {corr_str}
    
    Valid Pixels: {metrics['valid_pixels']:,} / {metrics['total_pixels']:,}
    Coverage: {100*metrics['valid_pixels']/metrics['total_pixels']:.1f}%
    """
    axes[1, 2].text(0.1, 0.5, metrics_text, fontsize=11, family='monospace',
                    verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def compare_directories(ref_dir, gen_dir, output_dir, sample_size=None):
    """
    Compare depth images from two directories.
    
    Args:
        ref_dir: Directory containing reference depth images
        gen_dir: Directory containing generated depth images
        output_dir: Directory to save comparison results
        sample_size: Number of images to compare (None for all)
    """
    ref_path = Path(ref_dir)
    gen_path = Path(gen_dir)
    output_path = Path(output_dir)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get list of common files
    ref_files = set([f.name for f in ref_path.glob('*.png')])
    gen_files = set([f.name for f in gen_path.glob('*.png')])
    common_files = sorted(list(ref_files & gen_files))
    
    if sample_size:
        common_files = common_files[:sample_size]
    
    print(f"Found {len(common_files)} common depth images to compare")
    
    all_metrics = []
    failed_files = []
    
    # Create comparison directory
    comparison_dir = output_path / 'comparisons'
    comparison_dir.mkdir(exist_ok=True)
    
    # Process each image pair
    for filename in tqdm(common_files, desc="Comparing images"):
        ref_img_path = ref_path / filename
        gen_img_path = gen_path / filename
        
        try:
            # Load images
            ref_normalized, ref_raw = load_depth_image(ref_img_path, is_reference=True)
            gen_normalized, gen_raw = load_depth_image(gen_img_path, is_reference=False)
            
            if ref_normalized is None or gen_normalized is None:
                failed_files.append(filename)
                continue
            
            # Calculate metrics
            metrics = calculate_metrics(ref_normalized, gen_normalized)
            metrics['filename'] = filename
            all_metrics.append(metrics)
            
            # Calculate difference
            if ref_normalized.shape != gen_normalized.shape:
                gen_normalized = cv2.resize(gen_normalized, 
                                           (ref_normalized.shape[1], ref_normalized.shape[0]),
                                           interpolation=cv2.INTER_LINEAR)
            
            diff = ref_normalized - gen_normalized
            
            # Create visualization
            vis_path = comparison_dir / f"{Path(filename).stem}_comparison.png"
            create_comparison_visualization(ref_normalized, gen_normalized, diff, metrics, vis_path)
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            failed_files.append(filename)
    
    # Calculate aggregate statistics
    if all_metrics:
        aggregate = {
            'total_images': len(all_metrics),
            'failed_images': len(failed_files),
            'mean_mse': np.nanmean([m['mse'] for m in all_metrics if m['mse'] is not None]),
            'mean_mae': np.nanmean([m['mae'] for m in all_metrics if m['mae'] is not None]),
            'mean_rmse': np.nanmean([m['rmse'] for m in all_metrics if m['rmse'] is not None]),
            'mean_ssim': np.nanmean([m['ssim'] for m in all_metrics if m['ssim'] is not None]),
            'mean_psnr': np.nanmean([m['psnr'] for m in all_metrics if m['psnr'] is not None]),
            'mean_correlation': np.nanmean([m['correlation'] for m in all_metrics if m['correlation'] is not None]),
        }
        
        # Create summary visualization
        create_summary_visualization(all_metrics, aggregate, output_path / 'summary_statistics.png')
        
        # Save detailed metrics JSON
        with open(output_path / 'detailed_metrics.json', 'w') as f:
            json.dump({
                'aggregate': aggregate,
                'per_image': all_metrics,
                'failed_files': failed_files
            }, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("COMPARISON SUMMARY")
        print("="*60)
        print(f"Total images compared: {aggregate['total_images']}")
        print(f"Failed images: {aggregate['failed_images']}")
        print(f"\nAverage Metrics:")
        print(f"  MSE:  {aggregate['mean_mse']:.6f}")
        print(f"  MAE:  {aggregate['mean_mae']:.6f}")
        print(f"  RMSE: {aggregate['mean_rmse']:.6f}")
        ssim_val = aggregate['mean_ssim']
        psnr_val = aggregate['mean_psnr']
        corr_val = aggregate['mean_correlation']
        if not np.isnan(ssim_val):
            print(f"  SSIM: {ssim_val:.4f}")
        else:
            print("  SSIM: N/A")
        if not np.isnan(psnr_val):
            print(f"  PSNR: {psnr_val:.2f}")
        else:
            print("  PSNR: N/A")
        if not np.isnan(corr_val):
            print(f"  Correlation: {corr_val:.4f}")
        else:
            print("  Correlation: N/A")
        print(f"\nResults saved to: {output_path}")
        print("="*60)
    else:
        print("No images were successfully compared!")


def create_summary_visualization(all_metrics, aggregate, output_path):
    """Create a summary visualization of all comparison metrics."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Depth Image Comparison - Summary Statistics', fontsize=16, fontweight='bold')
    
    # Extract metrics
    mse_values = [m['mse'] for m in all_metrics if m['mse'] is not None]
    mae_values = [m['mae'] for m in all_metrics if m['mae'] is not None]
    ssim_values = [m['ssim'] for m in all_metrics if m['ssim'] is not None]
    correlation_values = [m['correlation'] for m in all_metrics if m['correlation'] is not None]
    
    # MSE distribution
    axes[0, 0].hist(mse_values, bins=30, edgecolor='black', alpha=0.7)
    axes[0, 0].axvline(aggregate['mean_mse'], color='red', linestyle='--', linewidth=2, label=f'Mean: {aggregate["mean_mse"]:.6f}')
    axes[0, 0].set_title('MSE Distribution', fontsize=12)
    axes[0, 0].set_xlabel('Mean Squared Error')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # MAE distribution
    axes[0, 1].hist(mae_values, bins=30, edgecolor='black', alpha=0.7, color='orange')
    axes[0, 1].axvline(aggregate['mean_mae'], color='red', linestyle='--', linewidth=2, label=f'Mean: {aggregate["mean_mae"]:.6f}')
    axes[0, 1].set_title('MAE Distribution', fontsize=12)
    axes[0, 1].set_xlabel('Mean Absolute Error')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # SSIM distribution
    if ssim_values:
        axes[1, 0].hist(ssim_values, bins=30, edgecolor='black', alpha=0.7, color='green')
        axes[1, 0].axvline(aggregate['mean_ssim'], color='red', linestyle='--', linewidth=2, label=f'Mean: {aggregate["mean_ssim"]:.4f}')
        axes[1, 0].set_title('SSIM Distribution', fontsize=12)
        axes[1, 0].set_xlabel('Structural Similarity Index')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
    
    # Correlation distribution
    if correlation_values:
        axes[1, 1].hist(correlation_values, bins=30, edgecolor='black', alpha=0.7, color='purple')
        axes[1, 1].axvline(aggregate['mean_correlation'], color='red', linestyle='--', linewidth=2, label=f'Mean: {aggregate["mean_correlation"]:.4f}')
        axes[1, 1].set_title('Correlation Distribution', fontsize=12)
        axes[1, 1].set_xlabel('Correlation Coefficient')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='Compare depth images from two directories')
    parser.add_argument('--ref-dir', type=str, required=True,
                       help='Directory containing reference depth images (16-bit grayscale)')
    parser.add_argument('--gen-dir', type=str, required=True,
                       help='Directory containing generated depth images (RGB colorized)')
    parser.add_argument('--output-dir', type=str, required=True,
                       help='Output directory for comparison results')
    parser.add_argument('--sample-size', type=int, default=None,
                       help='Number of images to compare (None for all)')
    
    args = parser.parse_args()
    
    compare_directories(
        ref_dir=args.ref_dir,
        gen_dir=args.gen_dir,
        output_dir=args.output_dir,
        sample_size=args.sample_size
    )


if __name__ == '__main__':
    main()

