#!/usr/bin/env python3
"""
Fix for flash attention import issues in transformers.
This script patches the transformers library to avoid flash attention imports.
"""

import os
import sys
import importlib.util

def patch_transformers_no_flash_attn():
    """Patch transformers to disable flash attention imports."""
    
    # Create a custom flash_attention.py that doesn't import flash_attn
    flash_attention_content = '''
"""
Patched flash attention module that avoids importing flash_attn.
This prevents the undefined symbol error with flash_attn_2_cuda.
"""

def flash_attention_forward(*args, **kwargs):
    """No-op flash attention forward."""
    raise NotImplementedError("Flash attention is disabled to avoid CUDA compatibility issues")

def _flash_attention_forward(*args, **kwargs):
    """No-op flash attention forward."""
    raise NotImplementedError("Flash attention is disabled to avoid CUDA compatibility issues")

def flash_attn_supports_top_left_mask(*args, **kwargs):
    """Return False since flash attention is disabled."""
    return False
'''
    
    # Find transformers installation path
    try:
        import transformers
        transformers_path = transformers.__path__[0]
    except ImportError:
        print("Transformers not found")
        return False
    
    # Path to flash attention file
    flash_attn_path = os.path.join(transformers_path, 'integrations', 'flash_attention.py')
    
    # Create backup
    if os.path.exists(flash_attn_path):
        backup_path = flash_attn_path + '.backup'
        if not os.path.exists(backup_path):
            import shutil
            shutil.copy2(flash_attn_path, backup_path)
    
    # Write patched version
    try:
        os.makedirs(os.path.dirname(flash_attn_path), exist_ok=True)
        with open(flash_attn_path, 'w') as f:
            f.write(flash_attention_content)
        print(f"Successfully patched {flash_attn_path}")
        return True
    except Exception as e:
        print(f"Failed to patch flash attention: {e}")
        return False

def patch_modeling_flash_attention_utils():
    """Patch modeling_flash_attention_utils to avoid flash_attn imports."""
    
    patch_content = '''
"""
Patched modeling_flash_attention_utils that avoids flash_attn imports.
"""
import warnings
import torch

def _flash_attention_forward(*args, **kwargs):
    """No-op implementation."""
    raise NotImplementedError("Flash attention is disabled")

def flash_attn_supports_top_left_mask(*args, **kwargs):
    """Return False since flash attention is disabled."""
    return False

# Create dummy classes to avoid import errors
class FlashAttentionKwargs:
    pass

def flash_attention_forward(*args, **kwargs):
    """No-op implementation."""
    raise NotImplementedError("Flash attention is disabled")
'''
    
    try:
        import transformers
        transformers_path = transformers.__path__[0]
        target_path = os.path.join(transformers_path, 'modeling_flash_attention_utils.py')
        
        if os.path.exists(target_path):
            backup_path = target_path + '.backup'
            if not os.path.exists(backup_path):
                import shutil
                shutil.copy2(target_path, backup_path)
        
        with open(target_path, 'w') as f:
            f.write(patch_content)
        print(f"Successfully patched {target_path}")
        return True
    except Exception as e:
        print(f"Failed to patch modeling_flash_attention_utils: {e}")
        return False

if __name__ == "__main__":
    print("Patching transformers to fix flash attention issues...")
    patch1 = patch_transformers_no_flash_attn()
    patch2 = patch_modeling_flash_attention_utils()
    
    if patch1 or patch2:
        print("Transformers patched successfully. Restart your application.")
    else:
        print("No patches applied or patches failed.")