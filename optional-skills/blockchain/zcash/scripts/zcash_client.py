#!/usr/bin/env python3
"""Zcash blockchain client for Hermes agent. Wraps the zcash-mcp MCP server."""

import json
import subprocess
import sys


def run_mcp_tool(tool_name: str, args: dict) -> dict:
    """Call a zcash-mcp tool via npx."""
    cmd = ["npx", "@frontiercompute/zcash-mcp", "--tool", tool_name, "--args", json.dumps(args)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {"error": result.stderr.strip()}
    except Exception as e:
        return {"error": str(e)}


def get_blockchain_info() -> dict:
    return run_mcp_tool("get_blockchain_info", {})


def decode_memo(memo_hex: str) -> dict:
    return run_mcp_tool("decode_memo", {"memo": memo_hex})


def verify_proof(leaf_hash: str) -> dict:
    return run_mcp_tool("get_receipt", {"leaf_hash": leaf_hash})


def get_health() -> dict:
    return run_mcp_tool("get_health", {})


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: zcash_client.py <command> [args...]")
        print("Commands: info, health, memo <hex>, verify <leaf_hash>")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "info":
        print(json.dumps(get_blockchain_info(), indent=2))
    elif cmd == "health":
        print(json.dumps(get_health(), indent=2))
    elif cmd == "memo" and len(sys.argv) > 2:
        print(json.dumps(decode_memo(sys.argv[2]), indent=2))
    elif cmd == "verify" and len(sys.argv) > 2:
        print(json.dumps(verify_proof(sys.argv[2]), indent=2))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
