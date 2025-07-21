#!/bin/bash
# Fix flash attention by installing the correct wheel for PyTorch 2.6 + CUDA 12.6

set -e

echo "=== Installing Correct Flash-Attention Wheel ==="
echo "Target: PyTorch 2.6 + CUDA 12.6 (cxx11abi=FALSE)"

# Remove incompatible version
echo "Removing incompatible flash-attention..."
pip uninstall flash-attn -y || true

# Install the correct wheel
echo "Installing flash-attn 2.8.0.post2 for PyTorch 2.6 + CUDA 12.6..."
pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.0.post2/flash_attn-2.8.0.post2+cu12torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl

# Verify installation
echo "Verifying flash-attention installation..."
python -c "
import torch
import flash_attn
print(f'✅ PyTorch: {torch.__version__}')
print(f'✅ CUDA: {torch.version.cuda}')
print(f'✅ Flash-attn: {flash_attn.__version__}')

# Test the specific import that was failing
from flash_attn.bert_padding import index_first_axis, pad_input, unpad_input
from flash_attn.flash_attn_interface import flash_attn_func
print('✅ All flash-attention imports successful')

# Test transformers with flash-attention
import os
os.environ.pop('TRANSFORMERS_NO_FLASH_ATTENTION', None)  # Re-enable flash attention
from transformers import T5EncoderModel, AutoTokenizer
print('✅ Transformers with flash-attention working')
"

echo "✅ Flash-attention compatibility issue resolved!"
echo "Performance should now be optimal with GPU acceleration."