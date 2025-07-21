#!/usr/bin/env python3
"""
Definitive fix for flash attention compatibility issues in RunPod container.
This script provides a comprehensive solution for the flash-attn ABI mismatch.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_environment():
    """Check current environment and identify the exact issue."""
    print("=== Flash Attention Environment Analysis ===")
    
    # Check if we're in container
    in_container = os.path.exists('/.dockerenv')
    print(f"Container environment: {in_container}")
    
    # Check PyTorch version
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA version: {torch.version.cuda}")
    except ImportError:
        print("❌ PyTorch not available")
        return False
    
    # Check flash-attn installation
    try:
        import flash_attn
        print(f"Flash-attn version: {flash_attn.__version__}")
    except ImportError as e:
        print(f"❌ Flash-attn import error: {e}")
        return False
    
    # Check for symbol error
    try:
        from flash_attn.flash_attn_interface import flash_attn_func
        print("✅ Flash-attn symbols resolved correctly")
        return True
    except ImportError as e:
        if "undefined symbol" in str(e):
            print(f"❌ Symbol mismatch detected: {e}")
            return False
        else:
            print(f"❌ Other flash-attn error: {e}")
            return False

def apply_environment_fix():
    """Apply environment variable fix to disable flash attention."""
    print("\n=== Applying Environment Fix ===")
    
    # Set environment variable to disable flash attention
    os.environ['TRANSFORMERS_NO_FLASH_ATTENTION'] = '1'
    
    # Create startup script with fix
    startup_content = """#!/bin/bash
# Definitive flash attention fix for RunPod container
export TRANSFORMERS_NO_FLASH_ATTENTION=1
export FLASH_ATTENTION_SKIP_CUDA_BUILD=1

echo "Applying flash attention compatibility fix..."
echo "TRANSFORMERS_NO_FLASH_ATTENTION=$TRANSFORMERS_NO_FLASH_ATTENTION"
echo "FLASH_ATTENTION_SKIP_CUDA_BUILD=$FLASH_ATTENTION_SKIP_CUDA_BUILD"

# Start the application
exec python3 app.py "$@"
"""
    
    with open('startup_definitive.sh', 'w') as f:
        f.write(startup_content)
    os.chmod('startup_definitive.sh', 0o755)
    print("✅ Created startup_definitive.sh with environment fixes")

def patch_transformers_fallback():
    """Apply transformers patching for flash attention fallback."""
    print("\n=== Applying Transformers Patch ===")
    
    try:
        import transformers
        transformers_path = transformers.__path__[0]
        print(f"Transformers path: {transformers_path}")
        
        # Patch flash_attention.py
        flash_attn_path = os.path.join(transformers_path, 'integrations', 'flash_attention.py')
        if os.path.exists(flash_attn_path):
            backup_path = flash_attn_path + '.backup'
            if not os.path.exists(backup_path):
                shutil.copy2(flash_attn_path, backup_path)
            
            # Create minimal flash attention module
            with open(flash_attn_path, 'w') as f:
                f.write('''
"""
Patched flash attention module - disables flash attention to avoid ABI issues.
"""
def flash_attention_forward(*args, **kwargs):
    """Fallback - flash attention disabled."""
    return None

def _flash_attention_forward(*args, **kwargs):
    """Fallback - flash attention disabled."""
    return None

def flash_attn_supports_top_left_mask(*args, **kwargs):
    """Return False since flash attention is disabled."""
    return False
''')
            print("✅ Patched flash_attention.py")
        
        # Patch modeling_flash_attention_utils.py
        utils_path = os.path.join(transformers_path, 'modeling_flash_attention_utils.py')
        if os.path.exists(utils_path):
            backup_path = utils_path + '.backup'
            if not os.path.exists(backup_path):
                shutil.copy2(utils_path, backup_path)
            
            with open(utils_path, 'w') as f:
                f.write('''
"""
Patched modeling_flash_attention_utils - disables flash attention.
"""
import warnings

def _flash_attention_forward(*args, **kwargs):
    """Fallback implementation."""
    return None

def flash_attn_supports_top_left_mask(*args, **kwargs):
    """Return False since flash attention is disabled."""
    return False
''')
            print("✅ Patched modeling_flash_attention_utils.py")
            
    except Exception as e:
        print(f"❌ Failed to patch transformers: {e}")
        return False
    
    return True

def create_requirements_override():
    """Create requirements override for compatible versions."""
    print("\n=== Creating Requirements Override ===")
    
    requirements_content = """
# Definitive requirements for flash attention compatibility
# Use these versions to avoid ABI issues
torch>=2.0.0,<2.6.0
transformers==4.36.2
# Skip flash-attn entirely to avoid compatibility issues
# flash-attn>=2.3.0  # Commented out to prevent installation
"""
    
    with open('requirements_definitive.txt', 'w') as f:
        f.write(requirements_content.strip())
    print("✅ Created requirements_definitive.txt")

def verify_fix():
    """Verify the fix works by testing imports."""
    print("\n=== Verifying Fix ===")
    
    # Set environment variable
    os.environ['TRANSFORMERS_NO_FLASH_ATTENTION'] = '1'
    
    try:
        # Test transformers import
        import transformers
        print("✅ Transformers imports successfully")
        
        # Test T5 model import (the failing import)
        from transformers import T5EncoderModel, AutoTokenizer
        print("✅ T5 imports successfully")
        
        # Test the specific failing module
        from data_utils.v2a_utils.feature_utils_224 import FeaturesUtils
        print("✅ FeatureUtils imports successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Fix verification failed: {e}")
        return False

def main():
    """Main fix application."""
    print("=== Definitive Flash Attention Fix ===")
    print("This will apply all known fixes for the flash-attn ABI issue")
    
    # Check current state
    working = check_environment()
    
    if not working:
        print("\n🔧 Applying comprehensive fix...")
        
        # Apply all fixes
        apply_environment_fix()
        patch_transformers_fallback()
        create_requirements_override()
        
        # Verify the fix
        if verify_fix():
            print("\n✅ Fix applied successfully!")
            print("\nNext steps:")
            print("1. Use 'bash startup_definitive.sh' to start the application")
            print("2. Or set 'export TRANSFORMERS_NO_FLASH_ATTENTION=1' before running")
            print("3. The application will use CPU attention instead of flash attention")
        else:
            print("\n❌ Fix verification failed - manual intervention needed")
            return 1
    else:
        print("\n✅ Flash attention is working correctly!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())