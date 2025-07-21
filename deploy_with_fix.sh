#!/bin/bash
# Definitive deployment script for flash attention fix
# Based on JOURNAL.md findings and existing fixes

set -e

echo "=== ThinkSound Flash Attention Fix Deployment ==="
echo "Based on ERROR:ERR-2025-07-21-002 resolution"

# Step 1: Environment setup
echo "Setting up environment variables..."
export TRANSFORMERS_NO_FLASH_ATTENTION=1
export FLASH_ATTENTION_SKIP_CUDA_BUILD=1
export PYTHONPATH=/app:$PYTHONPATH

# Step 2: Verify we're in the right directory
cd /app
echo "Working directory: $(pwd)"

# Step 3: Apply existing fixes
echo "Applying existing fixes..."

# Use the fixed requirements
if [ -f "requirements_fixed.txt" ]; then
    echo "Installing fixed requirements..."
    pip install -r requirements_fixed.txt
fi

# Install the project
echo "Installing ThinkSound project..."
pip install -e .

# Step 4: Apply transformers patches
echo "Applying transformers patches..."
python3 fix_flash_attention.py

# Step 5: Verify the fix
echo "Verifying the fix..."
python3 -c "
import os
os.environ['TRANSFORMERS_NO_FLASH_ATTENTION'] = '1'

try:
    from transformers import T5EncoderModel, AutoTokenizer
    print('✅ Transformers imports successful')
    
    from data_utils.v2a_utils.feature_utils_224 import FeaturesUtils
    print('✅ FeatureUtils imports successful')
    
    print('✅ All imports working - flash attention disabled successfully')
except Exception as e:
    print(f'❌ Import failed: {e}')
    exit(1)
"

# Step 6: Start the application
echo "Starting ThinkSound application..."
echo "Using startup_fixed.sh with flash attention disabled..."
exec bash startup_fixed.sh