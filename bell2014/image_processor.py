import cv2
import numpy as np
import os
import argparse
from pathlib import Path

# --- Image Processing Functions (from your provided code) ---

def reconstruct_from_components_enhance(reflectance_path, shading_path, output_path):
    """
    Reconstructs an original color image from its color reflectance and grayscale shading.
    """
    reflectance = cv2.imread(reflectance_path, cv2.IMREAD_COLOR)
    shading = cv2.imread(shading_path, cv2.IMREAD_GRAYSCALE)

    if reflectance is None or shading is None:
        print(f"Error: Could not load components for enhancement. Check paths: {reflectance_path}, {shading_path}")
        return

    reflectance_float = reflectance.astype(np.float32) / 255.0
    shading_float = shading.astype(np.float32) / 255.0
    shading_broadcastable = shading_float[..., np.newaxis]

    reconstructed_float = reflectance_float * shading_broadcastable
    reconstructed_uint8 = np.clip(reconstructed_float * 255, 0, 255).astype(np.uint8)

    cv2.imwrite(output_path, reconstructed_uint8)
    print(f"    -> Saved enhanced reconstruction: {Path(output_path).name}")

def reconstruct_from_components(reflectance_path, shading_path, output_path, darkening_factor=2.0):
    """
    Reconstructs an original color image and applies a darkening factor.
    """
    reflectance = cv2.imread(reflectance_path, cv2.IMREAD_COLOR)
    shading = cv2.imread(shading_path, cv2.IMREAD_GRAYSCALE)

    if reflectance is None or shading is None:
        print(f"Error: Could not load components for reconstruction. Check paths: {reflectance_path}, {shading_path}")
        return

    reflectance_float = reflectance.astype(np.float32) / 255.0
    shading_float = shading.astype(np.float32) / 255.0
    shading_broadcastable = shading_float[..., np.newaxis]

    reconstructed_float = reflectance_float * shading_broadcastable
    final_float = reconstructed_float * darkening_factor
    reconstructed_uint8 = np.clip(final_float * 255, 0, 255).astype(np.uint8)

    cv2.imwrite(output_path, reconstructed_uint8)
    print(f"    -> Saved darkened reconstruction: {Path(output_path).name}")

def brighten_image(image_path, output_path, factor=4.0):
    """
    Brightens an image by a given factor.
    """
    original_image = cv2.imread(image_path)

    if original_image is None:
        print(f"Error: Could not load original image for brightening at {image_path}")
        return

    image_16bit = np.int16(original_image)
    brightened_image_16bit = image_16bit * factor
    brightened_image_clipped = np.clip(brightened_image_16bit, 0, 255)
    final_image = np.uint8(brightened_image_clipped)

    cv2.imwrite(output_path, final_image)
    print(f"    -> Saved brightened image: {Path(output_path).name}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Processes decomposed image components to generate final output images.")
    parser.add_argument('--original_image', type=str, required=True, help='Path to the original source image.')
    parser.add_argument('--reflectance_image', type=str, required=True, help='Path to the reflectance component image (-r.png).')
    parser.add_argument('--shading_image', type=str, required=True, help='Path to the shading component image (-s.png).')
    parser.add_argument('--output_dir', type=str, required=True, help='Path to the directory where processed images will be saved.')
    
    args = parser.parse_args()

    # Get the base name of the original file to create new filenames
    base_name = Path(args.original_image).stem

    # Define the full paths for the three output files
    output_reconstructed = os.path.join(args.output_dir, f"{base_name}_reconstructed.png")
    output_enhanced = os.path.join(args.output_dir, f"{base_name}_enhanced.png")
    output_brightened = os.path.join(args.output_dir, f"{base_name}_brightened.jpg")

    # Run all three processing steps
    reconstruct_from_components(args.reflectance_image, args.shading_image, output_reconstructed)
    reconstruct_from_components_enhance(args.reflectance_image, args.shading_image, output_enhanced)
    brighten_image(args.original_image, output_brightened)
