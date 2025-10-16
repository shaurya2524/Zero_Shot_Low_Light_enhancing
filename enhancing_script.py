#!/usr/bin/env python3
"""
Zero-Shot Image Enhancement Pipeline

This script provides multiple enhancement methods for low-light images using
intrinsic image decomposition (reflectance and shading components).

Methods available:
- Multi-Scale Retinex (MSR) - State-of-the-art low-light enhancement
- Structure-aware enhancement with edge-preserving filters
- Gamma correction enhancement
- CLAHE (Contrast Limited Adaptive Histogram Equalization)
- Simple reconstruction

Author: Enhanced by Cascade AI
Date: 2024
"""

import cv2
import numpy as np
from pathlib import Path
import sys
import argparse
from tqdm import tqdm

def enhance_shading_map(shading, params):
    """
    Enhances the shading map using a structure-aware decomposition method.
    
    This method separates the shading into base illumination and detail layers,
    enhances only the base layer, then recombines them for better results.
    
    Args:
        shading (np.ndarray): Input shading map (grayscale)
        params (dict): Enhancement parameters containing 'lambda', 'sigma', 'gamma'
        
    Returns:
        np.ndarray: Enhanced shading map
    """
    # Parameters for the filter and enhancement
    lambda_val = params.get('lambda', 6000.0)
    sigma_color = params.get('sigma', 15.0)
    gamma = params.get('gamma', 1.5)

    # 1. Decompose: Extract the large-scale structure (base illumination) using a fast, edge-preserving filter.
    try:
        base_illumination = cv2.ximgproc.fastGlobalSmootherFilter(shading, shading, lambda_val, sigma_color)
    except AttributeError:
        print("\nError: `cv2.ximgproc.fastGlobalSmootherFilter` not found.")
        print("Please ensure you have the full OpenCV package installed: `pip install opencv-contrib-python`")
        sys.exit(1)

    # Work in the log domain for better separation and recombination
    shading_log = np.log1p(shading.astype(np.float32))
    base_log = np.log1p(base_illumination.astype(np.float32))
    
    # 2. Calculate the detail layer
    detail_log = shading_log - base_log

    # 3. Enhance only the base illumination layer
    base_float = base_illumination.astype(np.float32) / 255.0
    enhanced_base_float = np.power(base_float, gamma)
    enhanced_base_log = np.log1p(enhanced_base_float * 255.0)

    # 4. Recombine the enhanced base with the original detail layer
    final_shading_log = enhanced_base_log + detail_log
    final_shading = np.expm1(final_shading_log)
    
    # 5. Normalize the result to the full 0-255 range for consistency
    enhanced_shading_norm = cv2.normalize(final_shading, None, 0, 255, cv2.NORM_MINMAX)
    
    return enhanced_shading_norm.astype(np.uint8)


def reconstruct_from_components_structured(reflectance_path, shading_path, params, brightness_factor=1.0):
    """
    Reconstructs an image using the STRUCTURE-AWARE ENHANCED shading map and applies a brightness factor.
    """
    reflectance = cv2.imread(str(reflectance_path), cv2.IMREAD_COLOR)
    shading = cv2.imread(str(shading_path), cv2.IMREAD_GRAYSCALE)
    if reflectance is None or shading is None:
        print(f"Warning: Could not read {reflectance_path} or {shading_path}")
        return None

    # Apply the structure-aware enhancement to the shading map
    enhanced_shading = enhance_shading_map(shading, params)
    
    reflectance_float = reflectance.astype(np.float32) / 255.0
    shading_float = enhanced_shading.astype(np.float32) / 255.0
    
    shading_broadcastable = shading_float[..., np.newaxis]
    reconstructed_float = reflectance_float * shading_broadcastable
    
    # Apply the final brightness factor
    brightened_float = reconstructed_float * brightness_factor
    
    return np.clip(brightened_float * 255, 0, 255).astype(np.uint8)


def reconstruct_with_gamma_correction(reflectance_path, shading_path, gamma, brightness_factor=1.0):
    """
    Reconstructs an image by applying a simple gamma correction to the ORIGINAL shading map.
    """
    reflectance = cv2.imread(str(reflectance_path), cv2.IMREAD_COLOR)
    shading = cv2.imread(str(shading_path), cv2.IMREAD_GRAYSCALE)

    if reflectance is None or shading is None:
        print(f"Error: Could not load components. Check paths: {reflectance_path}, {shading_path}")
        return None

    # Apply simple gamma correction to the shading map
    shading_float = shading.astype(np.float32) / 255.0
    enhanced_shading_float = np.power(shading_float, gamma)
    
    reflectance_float = reflectance.astype(np.float32) / 255.0
    shading_broadcastable = enhanced_shading_float[..., np.newaxis]
    
    reconstructed_float = reflectance_float * shading_broadcastable
    
    # Apply the final brightness factor
    brightened_float = reconstructed_float * brightness_factor
    
    return np.clip(brightened_float * 255, 0, 255).astype(np.uint8)


def reconstruct_from_components_simple(reflectance_path, shading_path, brightness_factor=1.0):
    """
    Reconstructs an image using the ORIGINAL shading map with no enhancement.
    """
    reflectance = cv2.imread(str(reflectance_path), cv2.IMREAD_COLOR)
    shading = cv2.imread(str(shading_path), cv2.IMREAD_GRAYSCALE)
    if reflectance is None or shading is None:
        print(f"Warning: Could not read {reflectance_path} or {shading_path}")
        return None

    reflectance_float = reflectance.astype(np.float32) / 255.0
    shading_float = shading.astype(np.float32) / 255.0
    
    shading_broadcastable = shading_float[..., np.newaxis]
    reconstructed_float = reflectance_float * shading_broadcastable
    
    # Apply the final brightness factor
    brightened_float = reconstructed_float * brightness_factor
    
    return np.clip(brightened_float * 255, 0, 255).astype(np.uint8)


def reconstruct_with_clahe_enhancement(reflectance_path, shading_path, clahe_params, brightness_factor=1.0):
    """
    Reconstructs an image by applying CLAHE to the ORIGINAL shading map.
    """
    reflectance = cv2.imread(str(reflectance_path), cv2.IMREAD_COLOR)
    shading = cv2.imread(str(shading_path), cv2.IMREAD_GRAYSCALE)

    if reflectance is None or shading is None:
        print(f"Error: Could not load components. Check paths: {reflectance_path}, {shading_path}")
        return None

    # Create a CLAHE object (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=clahe_params['clip_limit'], tileGridSize=clahe_params['tile_grid'])
    
    # Apply CLAHE to the shading map to enhance local contrast
    enhanced_shading = clahe.apply(shading)

    reflectance_float = reflectance.astype(np.float32) / 255.0
    shading_float = enhanced_shading.astype(np.float32) / 255.0
    
    shading_broadcastable = shading_float[..., np.newaxis]
    reconstructed_float = reflectance_float * shading_broadcastable
    
    # Apply the final brightness factor
    brightened_float = reconstructed_float * brightness_factor
    
    return np.clip(brightened_float * 255, 0, 255).astype(np.uint8)


def multi_scale_retinex(shading, sigmas):
    """
    Applies Multi-Scale Retinex enhancement to the shading map.
    
    MSR is a state-of-the-art method for low-light image enhancement that
    simulates the human visual system's ability to perceive constant colors
    under varying illumination conditions.
    
    Args:
        shading (np.ndarray): Input shading map
        sigmas (list): List of sigma values for different scales
        
    Returns:
        np.ndarray: MSR enhanced shading map
    """
    shading_log = np.log1p(shading.astype(np.float32))
    retinex = np.zeros_like(shading_log)

    for sigma in sigmas:
        # Kernel size must be odd
        k_size = int(6 * sigma + 1)
        if k_size % 2 == 0:
            k_size += 1
        
        blurred_log = cv2.GaussianBlur(shading_log, (k_size, k_size), sigma)
        retinex += shading_log - blurred_log
    
    retinex /= len(sigmas)
    enhanced_shading = np.expm1(retinex)
    
    # Normalize to full 0-255 range
    return cv2.normalize(enhanced_shading, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)


def reconstruct_with_msr_enhancement(reflectance_path, shading_path, msr_sigmas, brightness_factor=1.0):
    """
    Reconstructs an image using a Multi-Scale Retinex enhanced shading map.
    This is a state-of-the-art method for superior low-light enhancement.
    """
    reflectance = cv2.imread(str(reflectance_path), cv2.IMREAD_COLOR)
    shading = cv2.imread(str(shading_path), cv2.IMREAD_GRAYSCALE)

    if reflectance is None or shading is None:
        print(f"Error: Could not load components. Check paths: {reflectance_path}, {shading_path}")
        return None

    # Apply Multi-Scale Retinex to the shading map
    enhanced_shading = multi_scale_retinex(shading, msr_sigmas)

    reflectance_float = reflectance.astype(np.float32) / 255.0
    shading_float = enhanced_shading.astype(np.float32) / 255.0
    
    shading_broadcastable = shading_float[..., np.newaxis]
    reconstructed_float = reflectance_float * shading_broadcastable
    
    # Apply the final brightness factor
    brightened_float = reconstructed_float * brightness_factor
    
    return np.clip(brightened_float * 255, 0, 255).astype(np.uint8)


def run_inference(input_dir, output_dir, params, brightness_factor, simple_gamma, clahe_params, msr_sigmas):
    """
    Processes all images, creating five versions including the new MSR method.
    """
    input_path = Path(input_dir)
    base_output_path = Path(output_dir)
    
    # Create separate directories for the five types of output
    enhanced_dir = base_output_path / 'enhanced'
    reconstructed_dir = base_output_path / 'reconstructed'
    gamma_enhanced_dir = base_output_path / 'gamma_enhanced'
    clahe_enhanced_dir = base_output_path / 'clahe_enhanced'
    msr_enhanced_dir = base_output_path / 'msr_enhanced' # New directory
    enhanced_dir.mkdir(parents=True, exist_ok=True)
    reconstructed_dir.mkdir(parents=True, exist_ok=True)
    gamma_enhanced_dir.mkdir(parents=True, exist_ok=True)
    clahe_enhanced_dir.mkdir(parents=True, exist_ok=True)
    msr_enhanced_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"--- Starting Inference ---")
    print(f"Input Directory: {input_path}")
    print(f"Output Directories:")
    print(f"  - MSR Enhanced:        {msr_enhanced_dir}")
    print(f"  - Structured Enhanced: {enhanced_dir}")
    print(f"  - Gamma Enhanced:      {gamma_enhanced_dir}")
    print(f"  - CLAHE Enhanced:      {clahe_enhanced_dir}")
    print(f"  - Reconstructed:       {reconstructed_dir}")
    print(f"Structured Params: λ={params['lambda']}, γ={params['gamma']}, σ={params['sigma']}")
    print(f"Simple Gamma Param: γ={simple_gamma}")
    print(f"CLAHE Params: Clip Limit={clahe_params['clip_limit']}, Tile Size={clahe_params['tile_grid']}")
    print(f"MSR Sigmas: {msr_sigmas}")
    print(f"Brightness Factor: {brightness_factor}")

    reflectance_files = sorted(list(input_path.glob('*-r.png')))
    
    if not reflectance_files:
        print(f"Error: No reflectance files ('*-r.png') found in '{input_dir}'.")
        sys.exit(1)

    print(f"\nFound {len(reflectance_files)} image pairs to process.")
    
    for r_path in tqdm(reflectance_files, desc="Processing images", ncols=100):
        base_name = r_path.stem.removesuffix('-r')
        s_path = input_path / f"{base_name}-s.png"
        
        if not s_path.exists():
            print(f"Warning: Shading file not found for {r_path.name}, skipping.")
            continue
            
        # 1. Generate and save the new MSR-ENHANCED image
        msr_image = reconstruct_with_msr_enhancement(r_path, s_path, msr_sigmas, brightness_factor)
        if msr_image is not None:
            msr_save_path = msr_enhanced_dir / f"{base_name}_msr_enhanced.png"
            cv2.imwrite(str(msr_save_path), msr_image)

        # 2. Generate and save the STRUCTURE-AWARE ENHANCED image
        enhanced_image = reconstruct_from_components_structured(r_path, s_path, params, brightness_factor=brightness_factor)
        if enhanced_image is not None:
            enhanced_save_path = enhanced_dir / f"{base_name}_enhanced.png"
            cv2.imwrite(str(enhanced_save_path), enhanced_image)

        # 3. Generate and save the simple GAMMA-ENHANCED image
        gamma_enhanced_image = reconstruct_with_gamma_correction(r_path, s_path, simple_gamma, brightness_factor)
        if gamma_enhanced_image is not None:
            gamma_save_path = gamma_enhanced_dir / f"{base_name}_gamma_enhanced.png"
            cv2.imwrite(str(gamma_save_path), gamma_enhanced_image)

        # 4. Generate and save the CLAHE-ENHANCED image
        clahe_image = reconstruct_with_clahe_enhancement(r_path, s_path, clahe_params, brightness_factor)
        if clahe_image is not None:
            clahe_save_path = clahe_enhanced_dir / f"{base_name}_clahe_enhanced.png"
            cv2.imwrite(str(clahe_save_path), clahe_image)

        # 5. Generate and save the simple RECONSTRUCTED image
        reconstructed_image = reconstruct_from_components_simple(r_path, s_path, brightness_factor=brightness_factor)
        if reconstructed_image is not None:
            reconstructed_save_path = reconstructed_dir / f"{base_name}_reconstructed.png"
            cv2.imwrite(str(reconstructed_save_path), reconstructed_image)

    print("\n--- Inference Complete ---")
    print(f"✅ MSR enhanced images saved to '{msr_enhanced_dir}'")
    print(f"✅ Enhanced images saved to '{enhanced_dir}'")
    print(f"✅ Gamma enhanced images saved to '{gamma_enhanced_dir}'")
    print(f"✅ CLAHE enhanced images saved to '{clahe_enhanced_dir}'")
    print(f"✅ Reconstructed images saved to '{reconstructed_dir}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Apply image enhancement and reconstruction to a directory of image maps."
    )
    parser.add_argument(
        '--input_dir', 
        type=str, 
        required=True, 
        help="Path to the directory containing input images (*-r.png, *-s.png)."
    )
    parser.add_argument(
        '--output_dir', 
        type=str, 
        required=True, 
        help="Path to the base directory where output sub-folders will be saved."
    )
    parser.add_argument(
        '--brightness', 
        type=float, 
        default=9.0, 
        help="Brightness factor to apply to all final images. Default is 2.0."
    )
    # Arguments for the structured enhancement
    parser.add_argument(
        '--lambda', 
        dest='lambda_val',
        type=float, 
        default=6000.0, 
        help="Lambda for the structured enhancement filter. Default is 6000.0."
    )
    parser.add_argument(
        '--gamma', 
        type=float, 
        default=1.5, 
        help="Gamma for the structured enhancement method. Default is 1.5."
    )
    parser.add_argument(
        '--sigma', 
        type=float, 
        default=15.0, 
        help="Sigma color for the structured enhancement filter. Default is 15.0."
    )
    # Argument for the simple gamma enhancement
    parser.add_argument(
        '--simple_gamma',
        type=float,
        default=1.7,
        help="Gamma value for the simple enhancement method. Default is 1.7."
    )
    # Arguments for the CLAHE enhancement
    parser.add_argument(
        '--clahe_clip_limit',
        type=float,
        default=2.0,
        help="Clip limit for CLAHE. Controls contrast enhancement. Default is 2.0."
    )
    parser.add_argument(
        '--clahe_tile_grid',
        type=str,
        default="8,8",
        help="Tile grid size for CLAHE, as 'rows,cols'. Default is '8,8'."
    )
    # NEW Arguments for the MSR enhancement
    parser.add_argument(
        '--msr_sigmas',
        type=str,
        default="15,80,250",
        help="Comma-separated sigma values for MSR scales. Default is '15,80,250'."
    )
    args = parser.parse_args()

    # --- DEPENDENCY CHECK ---
    try:
        from tqdm import tqdm
    except ImportError:
        print("Error: 'tqdm' library not found. Please install it using: pip install tqdm")
        sys.exit(1)
        
    try:
        import cv2.ximgproc
    except (ImportError, AttributeError):
        print("\nError: `cv2.ximgproc` module not found or incomplete.")
        print("Please ensure you have the full OpenCV package installed:")
        print("1. `pip uninstall -y opencv-python opencv-python-headless`")
        print("2. `pip install opencv-contrib-python`")
        sys.exit(1)

    # --- RUN INFERENCE ---
    structured_params = {
        'lambda': args.lambda_val,
        'gamma': args.gamma,
        'sigma': args.sigma
    }
    
    # Parse tile grid size for CLAHE
    try:
        tile_rows, tile_cols = map(int, args.clahe_tile_grid.split(','))
    except ValueError:
        print("Error: Invalid format for --clahe_tile_grid. Please use 'rows,cols', e.g., '8,8'.")
        sys.exit(1)

    clahe_params = {
        'clip_limit': args.clahe_clip_limit,
        'tile_grid': (tile_rows, tile_cols)
    }

    # Parse sigma values for MSR
    try:
        msr_sigmas = list(map(int, args.msr_sigmas.split(',')))
    except ValueError:
        print("Error: Invalid format for --msr_sigmas. Please use comma-separated integers, e.g., '15,80,250'.")
        sys.exit(1)
    
    run_inference(args.input_dir, args.output_dir, structured_params, args.brightness, args.simple_gamma, clahe_params, msr_sigmas)


