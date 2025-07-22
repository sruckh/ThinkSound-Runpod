# Engineering Journal

## 2025-07-22 05:09

### Extract Latents Hanging Issue Resolution
- **What**: Fixed extract_latents.py hanging without CPU/GPU usage
- **Why**: Script was hanging during model loading and DataLoader initialization
- **How**: 
  - Added comprehensive logging and progress monitoring throughout the pipeline
  - Implemented model warmup to prevent initialization delays
  - Fixed DataLoader multiprocessing issues by setting num_workers=0
  - Added timeout handling and proper error recovery mechanisms
  - Enhanced GPU memory monitoring and automatic cleanup
  - Added detailed error messages and debugging information
- **Issues**: Model loading delays causing apparent hanging, DataLoader multiprocessing conflicts
- **Result**: extract_latents.py now runs reliably with visible progress and proper error handling

### Flash-Attention Dynamic Installation
- **What**: Implemented dynamic flash-attention installation based on environment
- **Why**: Fixed wheel installation failures and compatibility issues
- **How**: 
  - Removed flash-attention from requirements.txt to prevent conflicts
  - Created startup_definitive.sh with dynamic wheel detection
  - Added proper CUDA/PyTorch version detection
  - Implemented fallback mechanisms for different environments
  - Added verification steps after installation
- **Issues**: Hard-coded wheel URLs causing installation failures
- **Result**: Flash-attention now installs correctly based on environment configuration

## 2025-07-22 02:32

### Flash-Attention Wheel Update to 2.8.0.post2
- **What**: Updated project to use flash_attn-2.8.0.post2 wheel from GitHub release
- **Why**: To ensure compatibility with PyTorch 2.6 and CUDA 12.6 and leverage the latest improvements
- **How**: 
  - Updated Dockerfile to download and install the new wheel
  - Simplified install_compatible_flash_attn.sh to install only the specified wheel
  - Updated startup_flash_attn.sh to use the new version
  - Updated requirements_flash_attn.txt to specify the new version
- **Issues**: None
- **Result**: Project now uses the specified wheel version

### Documentation Update
- **What**: Updated JOURNAL.md and TASKS.md to reflect the wheel upgrade
- **Why**: Maintain accurate project documentation
- **How**: 
  - Added journal entry for the wheel upgrade
  - Updated TASKS.md to mark the task complete
- **Issues**: None
- **Result**: Documentation now reflects the current state of the project

## 2025-07-21 19:46

### Flash Attention Compatibility Resolution - Final Implementation
- **What**: Completed comprehensive flash attention compatibility fix for containerized deployment
- **Why**: Resolved critical "undefined symbol" errors preventing application startup
- **How**: 
  - Disabled flash attention via TRANSFORMERS_NO_FLASH_ATTENTION=1
  - Updated requirements to transformers 4.36.2 for compatibility
  - Created comprehensive fix utilities (apply_fixes.py, deploy_with_fix.sh)
  - Added proper error handling for missing flash attention
  - Updated container startup scripts for robust deployment
- **Issues**: flash_attn library incompatible with PyTorch 2.6 + CUDA 12.6 ABI
- **Result**: Application now starts successfully with CPU fallback, all features functional
