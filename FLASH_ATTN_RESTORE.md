# Flash Attention Restoration Guide

## Overview
This document provides instructions for restoring flash attention functionality to ThinkSound after it was disabled due to compatibility issues.

## Background
Flash attention was previously disabled in the containerized environment due to compatibility issues with PyTorch 2.6 + CUDA 12.6. The system was using xformers as a fallback, but flash attention provides better performance for transformer models.

## Environment Requirements
- **Python**: 3.10+
- **PyTorch**: 2.6.0
- **CUDA**: 12.6
- **flash-attn**: 2.8.0.post2 (compatible with PyTorch 2.6 + CUDA 12.6)

## Files Created

### 1. `requirements_flash_attn.txt`
Updated requirements file that includes flash-attn 2.8.0.post2 and compatible versions of all dependencies.

### 2. `startup_flash_attn.sh`
New startup script that properly enables flash attention instead of disabling it. Key changes:
- Removes `TRANSFORMERS_NO_FLASH_ATTENTION=1`
- Removes `USE_FLASH_ATTENTION=0`
- Installs flash-attn 2.8.0.post2 from pre-compiled wheel
- Includes verification tests for flash attention functionality

### 3. `test_flash_attn.py`
Comprehensive test script to verify flash attention installation and functionality:
- Tests flash-attn import
- Tests tensor operations with flash attention
- Tests transformers integration
- Provides detailed error reporting

## Installation Instructions

### Method 1: Using the new startup script
```bash
# Make the script executable
chmod +x startup_flash_attn.sh

# Run with flash attention enabled
./startup_flash_attn.sh
```

### Method 2: Manual installation
```bash
# Install flash-attn directly
pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.0.post2/flash_attn-2.8.0.post2+cu12torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl --no-build-isolation

# Update environment variables
unset TRANSFORMERS_NO_FLASH_ATTENTION
unset USE_FLASH_ATTENTION

# Install updated requirements
pip install -r requirements_flash_attn.txt
```

### Method 3: Docker deployment
Update your Dockerfile or docker-compose to use the new startup script:
```dockerfile
COPY startup_flash_attn.sh /app/
RUN chmod +x /app/startup_flash_attn.sh
CMD ["/app/startup_flash_attn.sh"]
```

## Verification Steps

### 1. Run the test script
```bash
python test_flash_attn.py
```

Expected output:
```
🚀 Starting flash attention tests...

🔍 Testing environment configuration...
Python version: 3.10.x
PyTorch version: 2.6.0
CUDA available: True
CUDA version: 12.6
GPU count: 1
  GPU 0: NVIDIA A100...

🔍 Testing flash attention installation...
✅ flash-attn imported successfully: 2.8.0.post2
✅ flash_attn_func imported successfully

🔍 Testing flash attention functionality...
📊 Test tensors created: torch.Size([2, 1024, 8, 64])
✅ Flash attention executed successfully: torch.Size([2, 1024, 8, 64])
✅ Gradient computation successful

🔍 Testing transformers with flash attention...
✅ Transformers model loaded and executed successfully

🎉 All flash attention tests passed!
```

### 2. Verify in application
Run your ThinkSound application and check:
- No flash attention import errors
- Improved inference speed (especially for longer sequences)
- Memory usage optimization

## Troubleshooting

### Common Issues

#### 1. CUDA version mismatch
If you get CUDA-related errors:
```bash
# Check CUDA version
python -c "import torch; print(torch.version.cuda)"

# Ensure CUDA 12.6 is available
nvidia-smi
```

#### 2. PyTorch version mismatch
Flash-attn 2.8.0.post2 requires PyTorch 2.6.0:
```bash
# Check PyTorch version
python -c "import torch; print(torch.__version__)"
```

#### 3. Build issues
If flash-attn fails to build:
```bash
# Install with no build isolation
pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.0.post2/flash_attn-2.8.0.post2+cu12torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl --no-build-isolation --no-cache-dir

# Ensure CUDA toolkit is available
nvcc --version
```

#### 4. Memory issues
Flash attention requires significant GPU memory:
- Ensure sufficient GPU memory is available
- Reduce batch size if encountering OOM errors
- Use gradient checkpointing for large models

### Performance Comparison

| Metric | Without Flash Attention | With Flash Attention |
|--------|------------------------|---------------------|
| Memory Usage | Higher | Lower (especially for long sequences) |
| Speed | Slower | Faster (2-4x for long sequences) |
| Max Sequence Length | Limited by memory | Significantly increased |

## Rollback Instructions
If issues arise, you can quickly revert to the fallback setup:

```bash
# Use the original fixed startup script
./startup_fixed.sh

# Or manually disable flash attention
export TRANSFORMERS_NO_FLASH_ATTENTION=1
export USE_FLASH_ATTENTION=0
```

## Support
For issues with flash attention restoration:
1. Run `python test_flash_attn.py` for detailed diagnostics
2. Check the troubleshooting section above
3. Verify CUDA and PyTorch versions match requirements
4. Ensure sufficient GPU memory is available