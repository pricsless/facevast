#!/bin/bash
set -e

# Update system and install dependencies
apt update && \
apt -y install git curl wget ffmpeg mesa-va-drivers

# Install Miniconda (silent mode, no prompts)
curl -LO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"

# Initialize conda and reload shell
source $HOME/miniconda/etc/profile.d/conda.sh
conda init bash
# Note: In a script, conda init may not take effect immediately

# Accept ToS so conda won't block
conda config --set channel_priority flexible  # Helps with dependency resolution
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main || true
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r || true

# Create and activate environment
conda create -n facevast "python==3.12.*" pip=25.0 -y
conda activate facevast

# Verify we're in the right environment
echo "Active environment: $CONDA_DEFAULT_ENV"


# Install CUDA + cuDNN in the activated environment
conda install -y nvidia/label/cuda-12.9.1::cuda-runtime nvidia/label/cudnn-9.10.0::cudnn

# Install TensorRT (check compatibility first)
pip install tensorrt==10.12.0.36 --extra-index-url https://pypi.nvidia.com

# Run install script inside repo
python install.py --onnxruntime cuda

# Fix numpy version (might conflict with other packages)
pip install "numpy>=1.23.5,<2.3"

python facefusion.py run --open-browser