# Quick Start Guide

<div align="center">

**Intrinsic Images in the Wild - Zero-Shot Enhancement Pipeline**

[Main Documentation](README.md) • [Comprehensive Guide](README_COMPREHENSIVE.md)

</div>

---

## Overview

This guide will help you get started with the **Intrinsic Images in the Wild** decomposition pipeline and the **Zero-Shot Enhancement** system for processing images into reflectance and shading components.

**Dataset**: The results shown in this repository were obtained using the **MVTV (Multi-View Television) dataset**, demonstrating the effectiveness of the pipeline on real-world low-light video frames.

## One-Time Setup

### Prerequisites
- **Ubuntu/Debian** system recommended
- **Python 2.7** for decomposition (core algorithm)
- **Python 3.9+** for enhancement pipeline
- **Anaconda/Miniconda** for environment management

### Automated Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-repo/intrinsic-enhancement.git
cd intrinsic-enhancement

# 2. Run the automated setup script
chmod +x setup.sh
./setup.sh

# 3. Verify installation
python -c "import numpy; import scipy; print('Core algorithm ready')"
conda activate enhancement_env
python -c "import cv2; import cv2.ximgproc; print('Enhancement pipeline ready')"
```

**What the setup script does:**
- Installs system dependencies (Eigen3, OpenCV)
- Creates conda environments (`intrinsic_env`, `enhancement_env`)
- Installs Python packages and compiles C++ extensions
- Verifies the installation

## Processing Images

### Option 1: Batch Processing (Recommended)

Process multiple images in parallel for better performance:

```bash
# 1. Activate the intrinsic environment
conda activate intrinsic_env

# 2. Navigate to decomposition directory
cd decomposition/

# 3. Run parallel processing
./multi_images.sh ../images/ ../output/ ../shading_reflectance/ 4

# Parameters:
# ../images/           - Input directory with images
# ../output/           - Output directory for results
# ../shading_reflectance/ - Directory for decomposed components
# 4                    - Number of parallel processes
```

### Option 2: Single Image Processing

For processing individual images with more control:

```bash
# Step 1: Decompose image into reflectance and shading
conda activate intrinsic_env
cd decomposition/
python decompose.py ../images/your_image.png

# Step 2: Apply zero-shot enhancement
conda activate enhancement_env
cd ..
python enhancing_script.py \
    --input_dir shading_reflectance/ \
    --output_dir results/ \
    --brightness 9.0 \
    --contrast 1.2
```

## View Results

### Output Structure

The pipeline generates several output directories:

| Directory | Purpose | Contents |
|-----------|---------|----------|
| `msr_enhanced/` | **Best results** | MSR-enhanced final images |
| `shading_reflectance/` | Decomposition | `-r.png` (reflectance), `-s.png` (shading) |
| `enhanced/` | Structure-aware | Enhanced with structure preservation |
| `reconstructed/` | Simple reconstruction | Basic reflectance × shading |
| `gamma_enhanced/` | Gamma correction | Gamma-corrected images |
| `clahe_enhanced/` | CLAHE | Contrast-limited adaptive histogram equalization |

## Quick Commands Reference

| Command | Environment | Purpose |
|---------|-------------|---------|
| `./setup.sh` | Any | Complete installation |
| `conda activate intrinsic_env` | Any | Switch to decomposition environment |
| `conda activate enhancement_env` | Any | Switch to enhancement environment |
| `./multi_images.sh <input> <output> <components> <threads>` | intrinsic_env | Batch processing |

## Configuration

### Environment Variables

```bash
# Set default directories (optional)
export INTRINSIC_DATA_DIR=/path/to/data
export ENHANCEMENT_MODELS_DIR=/path/to/models

# Performance tuning
export OMP_NUM_THREADS=8  # For parallel processing
```

### Custom Parameters

Edit configuration files to customize:
- **`bell2014/params.json`** - Algorithm parameters (if exists)
- **`enhancing_script.py`** - Enhancement settings (via command-line arguments)
- **`bell2014/multi_images.sh`** - Batch processing options

## Troubleshooting

### Common Issues

**Python versions conflict**
```bash
# Decomposition needs Python 2.7
conda create -n intrinsic_env python=2.7
# Enhancement needs Python 3.9+
conda create -n enhancement_env python=3.9
```

**OpenCV installation issues**
```bash
pip install opencv-contrib-python==4.5.5.64
# Or for Python 2.7 compatibility:
pip install opencv-python==4.2.0.34
```

**Eigen3 not found**
```bash
# Ubuntu/Debian
sudo apt-get install libeigen3-dev

# CentOS/RHEL
sudo yum install eigen3-devel

# macOS with Homebrew
brew install eigen
```

**Terminal app error in batch script**
```bash
# Edit multi_images.sh and change TERMINAL_APP variable
TERMINAL_APP="gnome-terminal"  # or your preferred terminal
```

### Performance Tips

- Use SSD storage for large image datasets
- Increase parallel processes for multi-core systems
- Batch similar sized images for optimal memory usage
- Clean output directories before large batch runs

## Resources & Documentation

- **[Comprehensive Documentation](README_COMPREHENSIVE.md)** - Detailed technical guide
- **[Research Paper](http://intrinsic.cs.cornell.edu)** - Original SIGGRAPH 2014 paper
- **[Intrinsic Images Dataset](http://intrinsic.cs.cornell.edu/)** - Intrinsic Images in the Wild benchmark

---

<div align="center">

For detailed usage examples and advanced configuration, see [README_COMPREHENSIVE.md](README_COMPREHENSIVE.md)

</div>
