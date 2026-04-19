#!/usr/bin/env python3
"""Hermes health check — verify critical import chains and environment."""
import sys
import os

def check_imports():
    """Verify all critical import chains work."""
    errors = []
    
    # Tier 1: Gateway-critical (must pass)
    try:
        from tools.environments.base import _load_json_store
    except ImportError as e:
        errors.append(f"[CRITICAL] tools.environments.base: {e}")
    
    try:
        from hermes_constants import is_termux
    except ImportError as e:
        errors.append(f"[CRITICAL] hermes_constants: {e}")
    
    try:
        from tools.terminal_tool import cleanup_vm
    except ImportError as e:
        errors.append(f"[CRITICAL] tools.terminal_tool: {e}")
    
    try:
        from tools.browser_tool import cleanup_browser
    except ImportError as e:
        errors.append(f"[WARNING] tools.browser_tool: {e}")
    
    # Tier 2: Agent features (should pass)
    try:
        import tools.file_tools
    except ImportError as e:
        errors.append(f"[WARNING] tools.file_tools: {e}")
    
    try:
        import tools.web_tools
    except ImportError as e:
        errors.append(f"[WARNING] tools.web_tools: {e}")
    
    try:
        from tools.delegate_tool import delegate_task
    except ImportError as e:
        errors.append(f"[WARNING] tools.delegate_tool: {e}")
    
    return errors

def check_pycache():
    """Count stale pycache directories."""
    import subprocess
    result = subprocess.run(
        ["find", ".", "-type", "d", "-name", "__pycache__",
         "-not", "-path", "./venv/*",
         "-not", "-path", "./.git/*",
         "-not", "-path", "./node_modules/*"],
        capture_output=True, text=True
    )
    dirs = [d for d in result.stdout.strip().split('\n') if d]
    return len(dirs)

if __name__ == "__main__":
    errors = check_imports()
    pycache_count = check_pycache()
    
    if errors:
        print("IMPORT ISSUES FOUND:")
        for e in errors:
            print(f"  {e}")
        print(f"\nFix: cd ~/.hermes/hermes-agent && find . -type d -name __pycache__ -not -path './venv/*' -exec rm -rf {{}} +")
        sys.exit(1)
    else:
        print(f"All imports OK. Project __pycache__ dirs: {pycache_count}")
        sys.exit(0)
