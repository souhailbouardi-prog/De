---
name: zcash
description: Query Zcash blockchain data, decode shielded memos, verify ZAP1 attestation proofs, check wallet attestation history, and create attestation events. Connects to Zebra RPC and the ZAP1 attestation API. Privacy-preserving by default.
version: 1.2.1
author: Zk-nd3r
license: MIT
metadata:
  hermes:
    tags: [Zcash, Blockchain, Crypto, Privacy, ZEC, Shielded, MCP, Attestation, BLAKE2b]
    related_skills: [base, solana]
---

# Zcash Blockchain Skill

22 tools for interacting with the Zcash privacy blockchain and ZAP1 attestation protocol.

Built on the `@frontiercompute/zcash-mcp` MCP server (2,480 downloads/month).

## When to Use

- User asks for Zcash blockchain info (block height, network status, mempool)
- User wants to decode a shielded memo from a transaction
- User wants to verify a ZAP1 attestation proof (leaf hash, Merkle inclusion)
- User wants to check attestation history for a wallet or agent
- User wants to create a lifecycle attestation event
- User asks about Zcash shielded transactions or privacy features

## Setup

Requires Node.js 18+. No API key needed for read operations.

```bash
npm install -g @frontiercompute/zcash-mcp
```

Or add to your MCP config:

```json
{
  "mcpServers": {
    "zcash": {
      "command": "npx",
      "args": ["@frontiercompute/zcash-mcp"]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| get_blockchain_info | Current chain height, network, sync status |
| get_block | Block details by height or hash |
| get_raw_transaction | Transaction data with shielded components |
| get_mempool_info | Mempool size and fee estimates |
| decode_memo | Decode shielded memo (hex or base64) |
| get_treestate | Orchard/Sapling note commitment tree state |
| verify_proof | Verify a ZAP1 Merkle inclusion proof |
| get_attestation_history | Attestation events for a wallet hash |
| create_attestation | Create a lifecycle attestation event |
| get_receipt | Fetch proof bundle for a leaf hash |
| get_balance | Attestation and anchor status for a wallet |
| sign_mpc | Sign via Ika 2PC-MPC (split-key custody) |
| get_stats | Protocol statistics (leaves, anchors, types) |
| get_health | Scanner and node health status |
| send_transaction | Broadcast a raw transaction |
| get_address_txids | Transaction history for an address |
| get_address_utxos | Unspent outputs for an address |
| create_invoice | Generate a ZAP1 payment invoice |
| get_invoice | Check invoice status |
| verify_evm | Verify attestation on Ethereum (EIP-152) |
| get_network_info | Peer connections and network state |
| get_mining_info | Mining difficulty and hashrate |

## Links

- npm: https://www.npmjs.com/package/@frontiercompute/zcash-mcp
- GitHub: https://github.com/Frontier-Compute/zcash-mcp
- Verify page: https://verify.frontiercompute.cash
- API: https://api.frontiercompute.cash/health
