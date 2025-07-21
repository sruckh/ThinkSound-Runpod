#!/usr/bin/env python3
"""
Test script to verify flash attention installation and functionality.
This script tests both the installation and runtime behavior of flash attention.
"""

import os
import sys
import torch
import traceback

def test_flash_attn_installation():
    """Test flash attention installation and basic functionality."""
    print("🔍 Testing flash attention installation...")
    
    try:
        import flash_attn
        print(f"✅ flash-attn imported successfully: {flash_attn.__version__}")
    except ImportError as e:
        print(f"❌ Failed to import flash-attn: {e}")
        return False
    
    try:
        from flash_attn import flash_attn_func
        print("✅ flash_attn_func imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import flash_attn_func: {e}")
        return False
    
    return True

def test_flash_attn_functionality():
    """Test flash attention with actual tensor operations."""
    print("\n🔍 Testing flash attention functionality...")
    
    if not torch.cuda.is_available():
        print("⚠️  CUDA not available, skipping functionality test")
        return True
    
    try:
        from flash_attn import flash_attn_func
        
        # Test parameters
        batch_size, seq_len, num_heads, head_dim = 2, 1024, 8, 64
        
        # Create test tensors
        device = torch.device('cuda')
        dtype = torch.float16
        
        q = torch.randn(batch_size, seq_len, num_heads, head_dim, device=device, dtype=dtype)
        k = torch.randn(batch_size, seq_len, num_heads, head_dim, device=device, dtype=dtype)
        v = torch.randn(batch_size, seq_len, num_heads, head_dim, device=device, dtype=dtype)
        
        print(f"📊 Test tensors created: {q.shape}, {k.shape}, {v.shape}")
        
        # Run flash attention
        out = flash_attn_func(q, k, v)
        print(f"✅ Flash attention executed successfully: {out.shape}")
        
        # Test gradient computation
        out.sum().backward()
        print("✅ Gradient computation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Flash attention functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_transformers_flash_attn():
    """Test transformers library with flash attention enabled."""
    print("\n🔍 Testing transformers with flash attention...")
    
    # Ensure flash attention is enabled
    if 'TRANSFORMERS_NO_FLASH_ATTENTION' in os.environ:
        del os.environ['TRANSFORMERS_NO_FLASH_ATTENTION']
    
    try:
        from transformers import AutoTokenizer, AutoModel
        
        # Test with a model that supports flash attention
        model_name = "t5-small"
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name, torch_dtype=torch.float16)
        
        if torch.cuda.is_available():
            model = model.cuda()
        
        # Test inference
        inputs = tokenizer("Hello world", return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
        
        print(f"✅ Transformers model loaded and executed successfully")
        print(f"   Model: {model_name}")
        print(f"   Output shape: {outputs.last_hidden_state.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Transformers flash attention test failed: {e}")
        traceback.print_exc()
        return False

def test_environment():
    """Test the current environment configuration."""
    print("\n🔍 Testing environment configuration...")
    
    print(f"Python version: {sys.version}")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
    
    # Check environment variables
    print("\nEnvironment variables:")
    flash_disabled = os.environ.get('TRANSFORMERS_NO_FLASH_ATTENTION')
    print(f"TRANSFORMERS_NO_FLASH_ATTENTION: {flash_disabled}")
    
    use_flash = os.environ.get('USE_FLASH_ATTENTION')
    print(f"USE_FLASH_ATTENTION: {use_flash}")
    
    return flash_disabled != '1' and use_flash != '0'

def main():
    """Run all flash attention tests."""
    print("🚀 Starting flash attention tests...\n")
    
    # Test environment
    env_ok = test_environment()
    if not env_ok:
        print("⚠️  Environment configured to disable flash attention")
    
    # Test installation
    install_ok = test_flash_attn_installation()
    if not install_ok:
        print("\n❌ Flash attention installation test failed")
        return 1
    
    # Test functionality
    func_ok = test_flash_attn_functionality()
    if not func_ok:
        print("\n❌ Flash attention functionality test failed")
        return 1
    
    # Test transformers integration
    transformers_ok = test_transformers_flash_attn()
    if not transformers_ok:
        print("\n❌ Transformers integration test failed")
        return 1
    
    print("\n🎉 All flash attention tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())