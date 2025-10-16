#!/bin/bash

# Zero-Shot Image Enhancement Setup Script
# This script automates the setup process for the enhancement pipeline

set -e  # Exit on any error

echo "🚀 Zero-Shot Image Enhancement Setup"
echo "===================================="

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "❌ Error: Conda is not installed. Please install Anaconda or Miniconda first."
    exit 1
fi

echo "✅ Conda found"

# Install system dependencies
echo "📦 Installing system dependencies..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    sudo apt-get update
    sudo apt-get install -y libeigen3-dev build-essential
    echo "✅ Linux dependencies installed"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew &> /dev/null; then
        brew install eigen
        echo "✅ macOS dependencies installed"
    else
        echo "❌ Error: Homebrew not found. Please install Homebrew first."
        exit 1
    fi
else
    echo "⚠️  Warning: Unsupported OS. Please install Eigen3 manually."
fi

# Create intrinsic decomposition environment
echo "🔧 Creating intrinsic_env environment..."
conda create -n intrinsic_env python=2.7 -y
echo "✅ intrinsic_env created"

# Create enhancement environment
echo "🔧 Creating enhancement_env environment..."
conda create -n enhancement_env python=3.9 -y
echo "✅ enhancement_env created"

# Setup intrinsic environment
echo "📚 Setting up intrinsic decomposition environment..."
eval "$(conda shell.bash hook)"
conda activate intrinsic_env

cd decomposition/

# Install packages one by one for Python 2.7 compatibility
echo "Installing Python 2.7 compatible packages..."
pip install Pillow
pip install cython==0.19.2
pip install numpy==1.8.0
pip install scipy==0.13.2
pip install scikit-image==0.9.3
pip install scikit-learn==0.14.1

# Compile C++ extensions
echo "🔨 Compiling C++ extensions..."
cd krahenbuhl2013/
make
cd ../..

conda deactivate
echo "✅ Intrinsic environment setup complete"

# Setup enhancement environment
echo "📚 Setting up enhancement environment..."
conda activate enhancement_env

pip install opencv-contrib-python numpy scipy scikit-image tqdm pathlib

conda deactivate
echo "✅ Enhancement environment setup complete"

# Test installations
echo "🧪 Testing installations..."

# Test intrinsic decomposition
echo "Testing intrinsic decomposition..."
conda activate intrinsic_env
cd decomposition/
if python -c "import numpy; import scipy; import skimage; print('Intrinsic dependencies OK')"; then
    echo "✅ Intrinsic environment test passed"
else
    echo "❌ Intrinsic environment test failed"
    exit 1
fi
cd ..
conda deactivate

# Test enhancement
echo "Testing enhancement pipeline..."
conda activate enhancement_env
if python -c "import cv2; import cv2.ximgproc; import numpy; print('Enhancement dependencies OK')"; then
    echo "✅ Enhancement environment test passed"
else
    echo "❌ Enhancement environment test failed"
    exit 1
fi
conda deactivate

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. Place your images in the 'images/' directory"
echo "2. Run the pipeline:"
echo "   conda activate intrinsic_env"
echo "   cd decomposition/"
echo "   ./multi_images.sh ../images/ ../output/ ../shading_reflectance/ 4"
echo ""
echo "Or for single image enhancement:"
echo "   conda activate enhancement_env"
echo "   python enhancing_script.py --input_dir shading_reflectance/ --output_dir results/"
echo ""
echo "📖 See README_COMPREHENSIVE.md for detailed usage instructions"
