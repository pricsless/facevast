#!/bin/bash
set -e

# Update system and install dependencies
apt update && \
apt -y install git curl wget ffmpeg mesa-va-drivers

# Install Miniconda (silent mode, no prompts)
curl -LO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"

# Initialize conda
source $HOME/miniconda/etc/profile.d/conda.sh
conda init --all

# Initialize conda
source $HOME/miniconda/etc/profile.d/conda.sh
conda init --all

# Accept ToS so conda won't block
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

# Create env (auto yes)
conda create -n facevast "python==3.12.*" pip=25.0 -y

# Install CUDA + cuDNN (auto yes)
conda install -y nvidia/label/cuda-12.9.1::cuda-runtime nvidia/label/cudnn-9.10.0::cudnn

# Install TensorRT
pip install tensorrt==10.0.1 --extra-index-url https://pypi.nvidia.com

# Run install script inside repo
python install.py --onnxruntime cuda

# Fix numpy version
pip install "numpy>=1.23.5,<2.3"

# Run app
python facefusion.py run --open-browser