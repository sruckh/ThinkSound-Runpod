#!/bin/bash

set -e

# Install git-lfs if not present
if ! command -v git-lfs &> /dev/null; then
    apt-get update
    apt-get install -y git-lfs
fi

git lfs install

# Download models if ckpts directory doesn't exist
if [ ! -d "ckpts" ]; then
    if [ -n "$HF_TOKEN" ]; then
        git -c "credential.helper=!f() { echo username=x-access-token; echo password=$HF_TOKEN; }; f" clone https://huggingface.co/liuhuadai/ThinkSound ckpts
    else
        git clone https://huggingface.co/liuhuadai/ThinkSound ckpts
    fi
fi

# Install thinksound in editable mode
cd /app
pip install -e .

# Install compatible flash-attention for PyTorch 2.6 (after all other dependencies)
pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.1.post4/flash_attn-2.7.1.post4+cu12torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl

# Start the Gradio app
cd /app
python3 app.py