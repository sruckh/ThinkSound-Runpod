#!/usr/bin/env python3
"""
Diagnostic script to check for required imports in the RunPod container.
This will help identify which packages are missing and need to be included
in the container image.
"""

import sys
import subprocess

def check_import(module_name, pip_name=None):
    """Check if a module can be imported."""
    pip_name = pip_name or module_name
    try:
        __import__(module_name)
        print(f"✅ {module_name} - Available")
        return True
    except ImportError:
        print(f"❌ {module_name} - Missing (install with: pip install {pip_name})")
        return False

def main():
    print("=== ThinkSound Import Diagnostics ===")
    print("Checking for required packages in the RunPod container...\n")
    
    # Core dependencies
    results = {
        'gradio': check_import('gradio'),
        'cv2': check_import('cv2', 'opencv-python'),
        'torch': check_import('torch'),
        'torchvision': check_import('torchvision'),
        'torchaudio': check_import('torchaudio'),
        'numpy': check_import('numpy'),
        'librosa': check_import('librosa'),
        'transformers': check_import('transformers'),
    }
    
    print("\n=== Summary ===")
    missing = [name for name, available in results.items() if not available]
    
    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        print("\nTo fix these issues:")
        print("1. Add these packages to your RunPod container image")
        print("2. Or use a container that includes these dependencies")
        print("3. Or install them in your container startup script")
    else:
        print("✅ All required packages are available!")
    
    return len(missing) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)