#!/bin/bash
# Fixed startup script that handles flash attention issues and gradio problems

set -e

echo "🚀 Starting ThinkSound with fixes..."

# Set environment variables to disable flash attention
export FLASH_ATTENTION_SKIP_CUDA_BUILD=TRUE
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

# Install fixed requirements if they exist
if [ -f "requirements_fixed.txt" ]; then
    echo "📦 Installing fixed requirements..."
    pip install -r requirements_fixed.txt --no-cache-dir
else
    echo "⚠️  Fixed requirements not found, using existing environment"
fi

# Upgrade gradio to requested version
echo "⬆️  Upgrading gradio..."
pip install gradio==4.44.1 --upgrade --no-cache-dir

# Install xformers as flash attention alternative
echo "🔧 Installing xformers for attention optimization..."
pip install xformers --no-cache-dir || echo "⚠️  xformers installation failed, continuing without it"

# Set environment to avoid flash attention
export TRANSFORMERS_NO_FLASH_ATTENTION=1
export USE_FLASH_ATTENTION=0

# Pre-download models to avoid runtime issues
echo "📥 Pre-downloading models..."
python -c "
import os
os.environ['TRANSFORMERS_NO_FLASH_ATTENTION'] = '1'
try:
    from transformers import T5EncoderModel, AutoTokenizer
    print('✅ T5 models loaded successfully')
except Exception as e:
    print(f'⚠️  T5 loading issue: {e}')
    print('Continuing with reduced functionality...')
"

# Fix for gradio file path issues
export GRADIO_TEMP_DIR=/tmp/thinksound_temp
export GRADIO_CACHE_DIR=/tmp/thinksound_temp

echo "🎯 Starting application..."
echo "Environment configured to avoid flash attention issues"
echo "Gradio temp dir: $GRADIO_TEMP_DIR"

# Start the application
exec python app.py