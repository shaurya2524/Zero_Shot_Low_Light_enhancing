#!/bin/bash

# =================================================================================
# Image Processing Pipeline Script (Multi-Terminal, Auto-Closing Version)
#
# This script processes images in parallel batches, opening a new terminal
# window for each process that closes automatically upon completion.
# =================================================================================

# --- Step 0: Configuration ---

# !!! EDIT THESE THREE LINES IF NEEDED !!!
DECOMPOSE_ENV="intrinsic_env"
PROCESS_ENV="hackathon_2"
# Change this to your terminal app. Common options: "konsole", "xterm", "terminator"
TERMINAL_APP="gnome-terminal"

# This function contains the actual work for a single image.
process_image() {
    local original_image_path="$1"
    local output_dir="$2"
    local intermediate_dir="$3"

    echo "===================================================="
    echo "Worker PID: $$"
    echo "Processing Image: $(basename "$original_image_path")"
    echo "===================================================="
    echo ""

    # Initialize Conda for this worker's shell
    eval "$(conda shell.bash hook)"

    local filename=$(basename -- "$original_image_path")
    local base_name="${filename%.*}"
    local current_input_dir=$(dirname "$original_image_path")
    
    # Paths where decompose.py will create the files
    local initial_reflectance_file="$current_input_dir/${base_name}-r.png"
    local initial_shading_file="$current_input_dir/${base_name}-s.png"
    
    # Final destination paths for the intermediate files
    local final_reflectance_file="$intermediate_dir/${base_name}-r.png"
    local final_shading_file="$intermediate_dir/${base_name}-s.png"

    echo "  [1/6] Activating '$DECOMPOSE_ENV' and running decomposition..."
    (
        conda activate "$DECOMPOSE_ENV"
        python decompose.py "$original_image_path"
    )
    
    if [ ! -f "$initial_reflectance_file" ] || [ ! -f "$initial_shading_file" ]; then
      echo "  ERROR: Decomposition failed. Intermediate files not found."
      return 1 # Return a non-zero exit code for failure
    fi
    
    echo "  [2/6] Moving intermediate files to '$intermediate_dir'..."
    mv "$initial_reflectance_file" "$final_reflectance_file"
    mv "$initial_shading_file" "$final_shading_file"
    
    echo "  [3/6] Activating '$PROCESS_ENV' and running processing..."
    (
        conda activate "$PROCESS_ENV"
        python image_processor.py \
          --original_image "$original_image_path" \
          --reflectance_image "$final_reflectance_file" \
          --shading_image "$final_shading_file" \
          --output_dir "$output_dir"
    )

    echo "  [4/6] Organizing final output files..."
    # NOTE: This assumes 'image_processor.py' creates files with these exact names.
    # If your python script uses different names, you must update them here.
    mv "$output_dir/${base_name}-brightened.png" "$output_dir/brightened/" 2>/dev/null || echo "    - Brightened file not found."
    mv "$output_dir/${base_name}-enhanced.png" "$output_dir/enhanced/" 2>/dev/null || echo "    - Enhanced file not found."
    mv "$output_dir/${base_name}-reconstructed.png" "$output_dir/reconstructed/" 2>/dev/null || echo "    - Reconstructed file not found."

    echo "  [5/6] Intermediate files saved in '$intermediate_dir'."
    echo "  [6/6] Done."
    echo ""
    echo "SUCCESS: Processing complete for $filename"
}


# =================================================================================
# --- SCRIPT LOGIC: DO NOT EDIT BELOW THIS LINE ---
# =================================================================================

# If the first argument is '--worker', run in worker mode.
if [ "$1" == "--worker" ]; then
    # In worker mode, call the function. The terminal will close automatically
    # as soon as the function finishes.
    process_image "$2" "$3" "$4"

# Otherwise, run in manager mode.
else
    # --- Manager Mode: Orchestrate the workers ---
    INPUT_DIR=$1
    OUTPUT_DIR=$2
    INTERMEDIATE_DIR=$3
    MAX_PARALLEL_JOBS=${4:-8}

    if [ -z "$INPUT_DIR" ] || [ -z "$OUTPUT_DIR" ] || [ -z "$INTERMEDIATE_DIR" ]; then
      echo "Usage: $0 <input_directory> <output_directory> <intermediate_directory> [max_parallel_jobs]"
      exit 1
    fi

    if ! command -v $TERMINAL_APP &> /dev/null; then
        echo "Error: Terminal application '$TERMINAL_APP' not found."
        echo "Please edit the TERMINAL_APP variable in this script."
        exit 1
    fi

    echo "Creating output directories..."
    mkdir -p "$OUTPUT_DIR/brightened"
    mkdir -p "$OUTPUT_DIR/enhanced"
    mkdir -p "$OUTPUT_DIR/reconstructed"
    mkdir -p "$INTERMEDIATE_DIR"
    
    echo "Starting image processing pipeline in Manager Mode..."
    echo "A new terminal will open for each of the $MAX_PARALLEL_JOBS parallel jobs."

    # Read all found image files into a sorted array
    mapfile -t images < <(find "$INPUT_DIR" -maxdepth 1 -type f | sort)
    total_images=${#images[@]}
    echo "Found $total_images images to process."

    # Loop through the images array in steps of MAX_PARALLEL_JOBS
    for (( i=0; i<total_images; i+=MAX_PARALLEL_JOBS )); do
        # Get the slice of images for the current batch
        batch=("${images[@]:i:MAX_PARALLEL_JOBS}")
        
        echo ""
        echo "----------------------------------------------------"
        echo "Processing Batch: ($((i / MAX_PARALLEL_JOBS + 1)))"
        
        pids=() # Array to hold the PIDs of the terminal windows
        for image_file in "${batch[@]}"; do
            filename=$(basename -- "$image_file")
            echo "  -> Launching worker for: $filename"
            
            # FIXED: Added the '--wait' flag to the terminal command.
            # This forces the script to wait for the terminal to close before continuing.
            # This is the key to making the batch processing work correctly.
            $TERMINAL_APP --wait --title="Processing: $filename" -- bash -c "$0 --worker '$image_file' '$OUTPUT_DIR' '$INTERMEDIATE_DIR'" &
            pids+=($!) # Save the PID of the new terminal process
        done
        
        echo "Waiting for batch to complete..."
        wait "${pids[@]}" # Wait for all PIDs in the pids array to complete
        echo "Batch complete."
    done

    echo "----------------------------------------------------"
    echo ""
    echo "Pipeline complete! All batches finished."
fi

