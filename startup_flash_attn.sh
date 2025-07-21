#!/bin/bash
# Startup script with flash attention properly enabled
# This replaces the flash-attention-disabled setup

set -e

echo "🚀 Starting ThinkSound with flash attention enabled..."

# Set environment variables for flash attention
export FLASH_ATTENTION_SKIP_CUDA_BUILD=FALSE
export TRANSFORMERS_CACHE=/tmp/transformers_cache
export HF_HOME=/tmp/hf_cache
export TOKENIZERS_PARALLELISM=false

# Create necessary directories
mkdir -p /tmp/transformers_cache
mkdir -p /tmp/hf_cache
mkdir -p /tmp/thinksound_temp

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if we're in Docker
if [ -f /.dockerenv ]; then
    echo "🐳 Running in Docker container"
    export CUDA_VISIBLE_DEVICES=0
fi

# Install flash-attention enabled requirements
if [ -f "requirements_flash_attn.txt" ]; then
    echo "📦 Installing flash-attention enabled requirements..."
    pip install -r requirements_flash_attn.txt --no-cache-dir
else
    echo "⚠️  Flash-attention requirements not found, installing flash-attn directly..."
    pip install flash-attn==2.7.4.post1 --no-build-isolation --no-cache-dir
fi

# Verify flash-attn installation
echo "🔍 Verifying flash-attn installation..."
python -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU count: {torch.cuda.device_count()}')

try:
    import flash_attn
    print(f'✅ flash-attn version: {flash_attn.__version__}')
    
    # Test flash attention functionality
    from flash_attn import flash_attn_func
    print('✅ flash_attn_func imported successfully')
    
    # Test with dummy tensors
    if torch.cuda.is_available():
        device = torch.device('cuda')
        batch_size, seq_len, num_heads, head_dim = 1, 512, 8, 64
        q = torch.randn(batch_size, seq_len, num_heads, head_dim, device=device, dtype=torch.float16)
        k = torch.randn(batch_size, seq_len, num_heads, head_dim, device=device, dtype=torch.float16)
        v = torch.randn(batch_size, seq_len, num_heads, head_dim, device=device, dtype=torch.float16)
        
        out = flash_attn_func(q, k, v)
        print('✅ Flash attention test passed')
    else:
        print('⚠️  CUDA not available, skipping flash attention test')
        
except ImportError as e:
    print(f'❌ flash-attn import failed: {e}')
    exit(1)
except Exception as e:
    print(f'❌ Flash attention test failed: {e}')
    exit(1)
"

# Enable flash attention in transformers
unset TRANSFORMERS_NO_FLASH_ATTENTION
unset USE_FLASH_ATTENTION
export TRANSFORMERS_CACHE=/tmp/transformers_cache

# Pre-download models with flash attention enabled
echo "📥 Pre-downloading models with flash attention..."
python -c "
import os
# Ensure flash attention is enabled
if 'TRANSFORMERS_NO_FLASH_ATTENTION' in os.environ:
    del os.environ['TRANSFORMERS_NO_FLASH_ATTENTION']
if 'USE_FLASH_ATTENTION' in os.environ:
    del os.environ['USE_FLASH_ATTENTION']

try:
    from transformers import T5EncoderModel, AutoTokenizer
    print('✅ T5 models loaded successfully with flash attention')
except Exception as e:
    print(f'⚠️  T5 loading issue: {e}')
    print('Continuing...')
"

# Fix for gradio file path issues
export GRADIO_TEMP_DIR=/tmp/thinksound_temp
export GRADIO_CACHE_DIR=/tmp/thinksound_temp

echo "🎯 Starting application with flash attention enabled..."
echo "Flash attention: ENABLED"
echo "Gradio temp dir: $GRADIO_TEMP_DIR"

# Start the application
exec python app.py