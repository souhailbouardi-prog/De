#!/usr/bin/env python3
"""
NOX Toggle - Enable/disable NOX reasoning protocol

Provides fast toggle operations for NOX with zero overhead when disabled.
Performance target: <50ms for toggle operations.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


# Configuration paths
CONFIG_PATH = Path.home() / ".hermes" / "config.yaml"
NOX_CONFIG_KEY = "nox"


def load_config() -> Dict[str, Any]:
    """Load Hermes configuration file."""
    if not CONFIG_PATH.exists():
        return {}
    
    try:
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        return {}


def save_config(config: Dict[str, Any]) -> bool:
    """Save Hermes configuration file."""
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        print(f"Error saving config: {e}", file=sys.stderr)
        return False


def get_nox_config() -> Dict[str, Any]:
    """Get NOX configuration from Hermes config."""
    config = load_config()
    return config.get(NOX_CONFIG_KEY, {})


def is_nox_enabled() -> bool:
    """Check if NOX is enabled (fast check)."""
    nox_config = get_nox_config()
    return nox_config.get("enabled", False)


def get_nox_mode() -> str:
    """Get current NOX mode."""
    nox_config = get_nox_config()
    return nox_config.get("mode", "balanced")


def get_layer_config() -> Dict[str, Any]:
    """Get layer configuration."""
    nox_config = get_nox_config()
    return nox_config.get("layers", {})


def enable_nox(mode: str = "balanced") -> bool:
    """
    Enable NOX with specified mode.
    
    Args:
        mode: Validation mode (strict, balanced, permissive)
    
    Returns:
        True if successful, False otherwise
    """
    config = load_config()
    
    # Set default NOX configuration
    if NOX_CONFIG_KEY not in config:
        config[NOX_CONFIG_KEY] = {}
    
    nox_config = config[NOX_CONFIG_KEY]
    nox_config["enabled"] = True
    nox_config["mode"] = mode
    
    # Set default layer configuration
    if "layers" not in nox_config:
        nox_config["layers"] = {
            "pre_check": {
                "enabled": True,
                "timeout_ms": 50
            },
            "structured_reasoning": {
                "enabled": True,
                "timeout_ms": 30
            },
            "citation_verify": {
                "enabled": False,
                "timeout_ms": 20
            }
        }
    
    # Set default thresholds
    if "thresholds" not in nox_config:
        nox_config["thresholds"] = {
            "overall_score": 70,
            "logical_consistency": 80,
            "evidence_quality": 60
        }
    
    # Set default performance settings
    if "performance" not in nox_config:
        nox_config["performance"] = {
            "cache_enabled": True,
            "parallel_execution": True,
            "early_termination": True
        }
    
    return save_config(config)


def disable_nox() -> bool:
    """
    Disable NOX (zero overhead mode).
    
    Returns:
        True if successful, False otherwise
    """
    config = load_config()
    
    if NOX_CONFIG_KEY in config:
        config[NOX_CONFIG_KEY]["enabled"] = False
    
    return save_config(config)


def set_nox_mode(mode: str) -> bool:
    """
    Set NOX validation mode.
    
    Args:
        mode: Validation mode (strict, balanced, permissive)
    
    Returns:
        True if successful, False otherwise
    """
    valid_modes = ["strict", "balanced", "permissive"]
    if mode not in valid_modes:
        print(f"Invalid mode: {mode}. Valid modes: {', '.join(valid_modes)}", file=sys.stderr)
        return False
    
    config = load_config()
    
    if NOX_CONFIG_KEY not in config:
        config[NOX_CONFIG_KEY] = {}
    
    config[NOX_CONFIG_KEY]["mode"] = mode
    
    # Adjust layer configuration based on mode
    nox_config = config[NOX_CONFIG_KEY]
    
    if mode == "strict":
        # Enable all layers
        if "layers" not in nox_config:
            nox_config["layers"] = {}
        nox_config["layers"]["pre_check"] = {"enabled": True, "timeout_ms": 50}
        nox_config["layers"]["structured_reasoning"] = {"enabled": True, "timeout_ms": 30}
        nox_config["layers"]["citation_verify"] = {"enabled": True, "timeout_ms": 20}
        # High thresholds
        if "thresholds" not in nox_config:
            nox_config["thresholds"] = {}
        nox_config["thresholds"]["overall_score"] = 85
        nox_config["thresholds"]["logical_consistency"] = 90
        nox_config["thresholds"]["evidence_quality"] = 75
    
    elif mode == "balanced":
        # Enable Layers 1-2 only
        if "layers" not in nox_config:
            nox_config["layers"] = {}
        nox_config["layers"]["pre_check"] = {"enabled": True, "timeout_ms": 50}
        nox_config["layers"]["structured_reasoning"] = {"enabled": True, "timeout_ms": 30}
        nox_config["layers"]["citation_verify"] = {"enabled": False, "timeout_ms": 20}
        # Moderate thresholds
        if "thresholds" not in nox_config:
            nox_config["thresholds"] = {}
        nox_config["thresholds"]["overall_score"] = 70
        nox_config["thresholds"]["logical_consistency"] = 80
        nox_config["thresholds"]["evidence_quality"] = 60
    
    elif mode == "permissive":
        # Enable Layer 1 only
        if "layers" not in nox_config:
            nox_config["layers"] = {}
        nox_config["layers"]["pre_check"] = {"enabled": True, "timeout_ms": 50}
        nox_config["layers"]["structured_reasoning"] = {"enabled": False, "timeout_ms": 30}
        nox_config["layers"]["citation_verify"] = {"enabled": False, "timeout_ms": 20}
        # Low thresholds
        if "thresholds" not in nox_config:
            nox_config["thresholds"] = {}
        nox_config["thresholds"]["overall_score"] = 50
        nox_config["thresholds"]["logical_consistency"] = 60
        nox_config["thresholds"]["evidence_quality"] = 40
    
    return save_config(config)


def enable_layer(layer_name: str) -> bool:
    """
    Enable a specific NOX layer.
    
    Args:
        layer_name: Layer name (pre_check, structured_reasoning, citation_verify)
    
    Returns:
        True if successful, False otherwise
    """
    valid_layers = ["pre_check", "structured_reasoning", "citation_verify"]
    if layer_name not in valid_layers:
        print(f"Invalid layer: {layer_name}. Valid layers: {', '.join(valid_layers)}", file=sys.stderr)
        return False
    
    config = load_config()
    
    if NOX_CONFIG_KEY not in config:
        config[NOX_CONFIG_KEY] = {}
    if "layers" not in config[NOX_CONFIG_KEY]:
        config[NOX_CONFIG_KEY]["layers"] = {}
    
    config[NOX_CONFIG_KEY]["layers"][layer_name] = {"enabled": True}
    
    return save_config(config)


def disable_layer(layer_name: str) -> bool:
    """
    Disable a specific NOX layer.
    
    Args:
        layer_name: Layer name (pre_check, structured_reasoning, citation_verify)
    
    Returns:
        True if successful, False otherwise
    """
    valid_layers = ["pre_check", "structured_reasoning", "citation_verify"]
    if layer_name not in valid_layers:
        print(f"Invalid layer: {layer_name}. Valid layers: {', '.join(valid_layers)}", file=sys.stderr)
        return False
    
    config = load_config()
    
    if NOX_CONFIG_KEY in config and "layers" in config[NOX_CONFIG_KEY]:
        if layer_name in config[NOX_CONFIG_KEY]["layers"]:
            config[NOX_CONFIG_KEY]["layers"][layer_name]["enabled"] = False
    
    return save_config(config)


def print_status() -> None:
    """Print current NOX status."""
    enabled = is_nox_enabled()
    mode = get_nox_mode()
    layers = get_layer_config()
    
    print(f"NOX Status: {'ENABLED' if enabled else 'DISABLED'}")
    print(f"Mode: {mode}")
    print("Layers:")
    
    layer_names = {
        "pre_check": "Pre-Check",
        "structured_reasoning": "Structured Reasoning",
        "citation_verify": "Citation Verification"
    }
    
    for layer_key, layer_name in layer_names.items():
        layer_config = layers.get(layer_key, {})
        layer_enabled = layer_config.get("enabled", False)
        timeout = layer_config.get("timeout_ms", "N/A")
        status = "enabled" if layer_enabled else "disabled"
        print(f"  - {layer_name}: {status} ({timeout}ms timeout)")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: toggle.py <command> [args]")
        print("")
        print("Commands:")
        print("  enable [mode]    Enable NOX (default mode: balanced)")
        print("  disable           Disable NOX")
        print("  mode <mode>       Set validation mode (strict, balanced, permissive)")
        print("  enable-layer <layer>  Enable specific layer")
        print("  disable-layer <layer> Disable specific layer")
        print("  status            Show current status")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "enable":
        mode = sys.argv[2] if len(sys.argv) > 2 else "balanced"
        if enable_nox(mode):
            print(f"NOX enabled with mode: {mode}")
            sys.exit(0)
        else:
            print("Failed to enable NOX", file=sys.stderr)
            sys.exit(1)
    
    elif command == "disable":
        if disable_nox():
            print("NOX disabled")
            sys.exit(0)
        else:
            print("Failed to disable NOX", file=sys.stderr)
            sys.exit(1)
    
    elif command == "mode":
        if len(sys.argv) < 3:
            print("Usage: toggle.py mode <strict|balanced|permissive>", file=sys.stderr)
            sys.exit(1)
        mode = sys.argv[2]
        if set_nox_mode(mode):
            print(f"NOX mode set to: {mode}")
            sys.exit(0)
        else:
            print("Failed to set NOX mode", file=sys.stderr)
            sys.exit(1)
    
    elif command == "enable-layer":
        if len(sys.argv) < 3:
            print("Usage: toggle.py enable-layer <layer>", file=sys.stderr)
            sys.exit(1)
        layer = sys.argv[2]
        if enable_layer(layer):
            print(f"Layer '{layer}' enabled")
            sys.exit(0)
        else:
            print(f"Failed to enable layer '{layer}'", file=sys.stderr)
            sys.exit(1)
    
    elif command == "disable-layer":
        if len(sys.argv) < 3:
            print("Usage: toggle.py disable-layer <layer>", file=sys.stderr)
            sys.exit(1)
        layer = sys.argv[2]
        if disable_layer(layer):
            print(f"Layer '{layer}' disabled")
            sys.exit(0)
        else:
            print(f"Failed to disable layer '{layer}'", file=sys.stderr)
            sys.exit(1)
    
    elif command == "status":
        print_status()
        sys.exit(0)
    
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
