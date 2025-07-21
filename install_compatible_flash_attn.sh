#!/bin/bash
# Install compatible flash-attention for PyTorch 2.6 + CUDA 12.6

set -e

echo "=== Installing Compatible Flash-Attention ==="
echo "Target: PyTorch 2.6 + CUDA 12.6"

# Check current environment
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.version.cuda}')"

# Option 1: Install the exact compatible version
echo "Installing flash-attn 2.7.1.post4 for PyTorch 2.6 + CUDA 12.6..."
pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.1.post4/flash_attn-2.7.1.post4+cu12torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl

# Option 2: Install newer compatible version (recommended)
echo "Installing flash-attn 2.8.0.post2 for PyTorch 2.6 + CUDA 12.6..."
pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.0.post2/flash_attn-2.8.0.post2+cu12torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl

# Verify installation
echo "Verifying flash-attention installation..."
python -c "
import torch
import flash_attn
print(f'✅ PyTorch: {torch.__version__}')
print(f'✅ Flash-attn: {flash_attn.__version__}')
from flash_attn.flash_attn_interface import flash_attn_func
print('✅ Flash-attention symbols resolved successfully')
"

echo "✅ Compatible flash-attention installed successfully!"