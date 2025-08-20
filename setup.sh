#!/bin/bash
set -e

# Install system dependencies (auto yes)
apt install git-all -y

apt install curl -y

apt install ffmpeg -y

# Download Miniconda
curl -LO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Install Miniconda (batch mode, no prompts)
bash Miniconda3-latest-Linux-x86_64.sh -b

# Initialize conda
conda init --all

# Create environment (auto yes)
conda create -n facevast "python==3.12" pip=25.0 -y

# Activate environment
conda activate facevast

# Install CUDA/cuDNN (auto yes)
conda install nvidia/label/cuda-12.9.1::cuda-runtime nvidia/label/cudnn-9.10.0::cudnn -y

# Install TensorRT
pip install tensorrt==10.12.0.36 --extra-index-url https://pypi.nvidia.com

# Run install script
python install.py --onnxruntime cuda

# Reload environment
conda deactivate

conda activate facevast

# Run app
python facefusion.py run --open-browser