#!/bin/bash
# Definitive flash attention fix for RunPod container
export TRANSFORMERS_NO_FLASH_ATTENTION=1
export FLASH_ATTENTION_SKIP_CUDA_BUILD=1

echo "Applying flash attention compatibility fix..."
echo "TRANSFORMERS_NO_FLASH_ATTENTION=$TRANSFORMERS_NO_FLASH_ATTENTION"
echo "FLASH_ATTENTION_SKIP_CUDA_BUILD=$FLASH_ATTENTION_SKIP_CUDA_BUILD"

# Start the application
exec python3 app.py "$@"
