#!/usr/bin/env python3
"""
Comprehensive fix script for ThinkSound application issues:
1. Flash attention import errors
2. Gradio file path errors
3. Dependency compatibility issues
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    return True

def install_fixed_requirements():
    """Install fixed requirements with compatible versions."""
    print("📦 Installing fixed requirements...")
    
    requirements_file = "requirements_fixed.txt"
    if not os.path.exists(requirements_file):
        print("❌ requirements_fixed.txt not found")
        return False
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", requirements_file, 
            "--no-cache-dir", "--upgrade"
        ], check=True)
        print("✅ Fixed requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def patch_flash_attention():
    """Patch transformers to avoid flash attention issues."""
    print("🔧 Patching flash attention issues...")
    
    try:
        import transformers
        transformers_path = transformers.__path__[0]
        
        # Patch flash attention integration
        flash_attn_path = os.path.join(transformers_path, 'integrations', 'flash_attention.py')
        if os.path.exists(flash_attn_path):
            backup_path = flash_attn_path + '.backup'
            if not os.path.exists(backup_path):
                shutil.copy2(flash_attn_path, backup_path)
            
            # Create patched version
            patched_content = '''"""
Patched flash attention module that avoids flash_attn imports.
This prevents undefined symbol errors with flash_attn_2_cuda.
"""

def flash_attention_forward(*args, **kwargs):
    """No-op flash attention forward."""
    raise NotImplementedError("Flash attention disabled for compatibility")

def _flash_attention_forward(*args, **kwargs):
    """No-op flash attention forward."""
    raise NotImplementedError("Flash attention disabled for compatibility")

def flash_attn_supports_top_left_mask(*args, **kwargs):
    """Return False since flash attention is disabled."""
    return False
'''
            
            with open(flash_attn_path, 'w') as f:
                f.write(patched_content)
            print("✅ Flash attention patched successfully")
            return True
            
    except ImportError as e:
        print(f"⚠️  Transformers not available: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Could not patch flash attention: {e}")
        return False

def create_gradio_fix():
    """Create fix for gradio file path issues."""
    print("🎯 Creating gradio file path fix...")
    
    # Create a wrapper script that handles file paths correctly
    wrapper_content = '''#!/usr/bin/env python3
"""
Gradio wrapper that fixes file path issues
"""
import os
import tempfile
import sys
from pathlib import Path

# Set up environment variables for gradio
os.environ['GRADIO_TEMP_DIR'] = '/tmp/thinksound_gradio'
os.environ['GRADIO_CACHE_DIR'] = '/tmp/thinksound_gradio'
os.environ['TRANSFORMERS_NO_FLASH_ATTENTION'] = '1'

# Create temp directories
temp_dir = '/tmp/thinksound_gradio'
os.makedirs(temp_dir, exist_ok=True)

# Import and run the main app
sys.path.insert(0, str(Path(__file__).parent))
from app import demo

if __name__ == "__main__":
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=os.getenv("GRADIO_SHARE", "false").lower() == "true"
    )
'''
    
    with open('run_fixed.py', 'w') as f:
        f.write(wrapper_content)
    
    # Make it executable
    os.chmod('run_fixed.py', 0o755)
    print("✅ Gradio fix created as run_fixed.py")

def verify_installation():
    """Verify that the fixes are working."""
    print("🔍 Verifying installation...")
    
    try:
        # Test basic imports
        import torch
        print(f"✅ PyTorch {torch.__version__} loaded")
        
        import transformers
        print(f"✅ Transformers {transformers.__version__} loaded")
        
        import gradio
        print(f"✅ Gradio {gradio.__version__} loaded")
        
        # Test that we can import without flash attention
        os.environ['TRANSFORMERS_NO_FLASH_ATTENTION'] = '1'
        from transformers import T5EncoderModel, AutoTokenizer
        print("✅ Transformers models can be imported without flash attention")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main fix application."""
    print("🚀 Applying comprehensive fixes for ThinkSound...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install fixed requirements
    if not install_fixed_requirements():
        print("⚠️  Using existing environment (requirements install failed)")
    
    # Patch flash attention
    patch_flash_attention()
    
    # Create gradio fix
    create_gradio_fix()
    
    # Verify installation
    if verify_installation():
        print("\n✅ All fixes applied successfully!")
        print("\nTo run the application:")
        print("1. Use: python run_fixed.py")
        print("2. Or: bash startup_fixed.sh")
        print("\nThe application should now start without flash attention errors.")
    else:
        print("\n⚠️  Some fixes may not have applied correctly, but continuing...")

if __name__ == "__main__":
    main()