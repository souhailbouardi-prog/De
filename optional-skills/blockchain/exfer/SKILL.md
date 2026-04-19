---
name: exfer
description: Permissionless peer-to-peer settlement for autonomous machines. Send payments, construct HTLCs, multisig, escrow, vault, and delegation contracts via CLI. All commands support --json for agent automation. No API key required — any agent with a keypair can transact.
version: 1.4.0
author: ahuman-exfer
license: MIT
metadata:
  hermes:
    tags: [Blockchain, Crypto, Payments, HTLC, Multisig, Escrow, Machine-Commerce, PoW]
    related_skills: [solana, base]
---

# Exfer Blockchain Skill

Peer-to-peer settlement for autonomous machines. Generate wallets, send payments,
mine blocks, and construct programmable contracts (HTLCs, multisig, vault, escrow,
delegation) — all from the CLI with `--json` output for agent automation.

No API key, no account, no third-party service. Any agent with a keypair can transact.

---

## When to Use

- Agent needs to send or receive a payment without a centralized intermediary
- Agent needs a trustless escrow, time-locked vault, or multi-party approval
- Agent wants to earn cryptocurrency by mining or completing tasks
- Agent needs an HTLC for atomic swaps or conditional payments
- Agent needs a multisig wallet for shared custody or committee governance
- User asks about Exfer balances, transactions, or block data

---

## Prerequisites

Download the binary for your platform (no build tools required):

```bash
# Linux x86_64
curl -L -o exfer https://github.com/ahuman-exfer/exfer/releases/latest/download/exfer-linux-x86_64
chmod +x exfer && sudo mv exfer /usr/local/bin/

# macOS ARM
curl -L -o exfer https://github.com/ahuman-exfer/exfer/releases/latest/download/exfer-macos-arm64
chmod +x exfer && sudo mv exfer /usr/local/bin/

# macOS Intel
curl -L -o exfer https://github.com/ahuman-exfer/exfer/releases/latest/download/exfer-macos-x86_64
chmod +x exfer && sudo mv exfer /usr/local/bin/
```

Or build from source: `cargo build --release` (requires Rust toolchain).

Set the RPC endpoint (any running Exfer node):

```bash
export RPC="http://82.221.100.201:9334"
```

---

## Quick Reference

```
exfer wallet generate --output wallet.key --json          # Create keypair
exfer wallet info --wallet wallet.key --json              # Show address + pubkey
exfer wallet send --wallet wallet.key --to <ADDR> --amount "10 EXFER" --rpc $RPC --json

exfer script htlc-lock      ...  --json                   # Lock funds in HTLC
exfer script htlc-claim     ...  --json                   # Claim with preimage
exfer script htlc-reclaim   ...  --json                   # Reclaim after timeout

exfer script multisig2of2-lock/spend                      # 2-of-2 multisig
exfer script multisig1of2-lock/spend                      # 1-of-2 multisig
exfer script multisig2of3-lock/spend                      # 2-of-3 multisig

exfer script vault-lock/spend/recover                     # Timelock + recovery
exfer script escrow-lock/release/arbitrate/reclaim        # 3-path escrow
exfer script delegation-lock/owner-spend/delegate-spend   # Time-limited delegate
```

---

## Procedure

### 0. Setup Check

```bash
exfer --version
curl -s -X POST $RPC -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"get_block_height","params":{},"id":1}'
```

### 1. Create a Wallet

```bash
exfer wallet generate --output ~/agent-wallet.key --json
```

Output:
```json
{
  "pubkey": "3c733ae392cf45e953e2aec5e7bc040042ed9294d1bdb248d3fa6be379f1c75e",
  "address": "8537a327ac7ade4ff57825fc4b7abc69b4c8f693068f7df8d05893cdcf5c7dcb"
}
```

Save the `pubkey` for mining and the `address` for receiving payments.

### 2. Check Balance

```bash
curl -s -X POST $RPC -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"get_balance","params":{"address":"<YOUR_ADDRESS>"},"id":1}'
```

### 3. Send a Payment

```bash
exfer wallet send \
  --wallet ~/agent-wallet.key \
  --to <RECIPIENT_ADDRESS_HEX> \
  --amount "10 EXFER" \
  --rpc $RPC \
  --json
```

### 4. HTLC (Conditional Payment)

Lock funds so a recipient claims with a preimage, or sender reclaims after timeout:

```bash
# Generate preimage and hash
PREIMAGE=$(openssl rand -hex 32)
HASH_LOCK=$(echo -n "$PREIMAGE" | xxd -r -p | shasum -a 256 | cut -d' ' -f1)

# Lock
exfer script htlc-lock \
  --wallet ~/sender.key \
  --receiver <RECEIVER_PUBKEY> \
  --hash-lock $HASH_LOCK \
  --timeout $(($(curl -s -X POST $RPC -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"get_block_height","params":{},"id":1}' \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['height'])") + 500)) \
  --amount "10 EXFER" \
  --rpc $RPC --json

# Claim (receiver reveals preimage)
exfer script htlc-claim \
  --wallet ~/receiver.key \
  --tx-id <LOCK_TX_ID> \
  --preimage $PREIMAGE \
  --sender <SENDER_PUBKEY> \
  --timeout <TIMEOUT> \
  --rpc $RPC --json

# Reclaim (sender, after timeout)
exfer script htlc-reclaim \
  --wallet ~/sender.key \
  --tx-id <LOCK_TX_ID> \
  --receiver <RECEIVER_PUBKEY> \
  --hash-lock $HASH_LOCK \
  --timeout <TIMEOUT> \
  --rpc $RPC --json
```

### 5. Multisig

```bash
# 2-of-2: both parties must sign
exfer script multisig2of2-lock \
  --wallet ~/party-a.key --pubkey-b <PUBKEY_B> \
  --amount "10 EXFER" --rpc $RPC --json

exfer script multisig2of2-spend \
  --wallet ~/party-a.key --wallet2 ~/party-b.key \
  --tx-id <LOCK_TX_ID> --to <DEST_ADDRESS> --rpc $RPC --json

# 1-of-2: either party can sign
exfer script multisig1of2-lock \
  --wallet ~/party-a.key --pubkey-b <PUBKEY_B> \
  --amount "10 EXFER" --rpc $RPC --json

exfer script multisig1of2-spend \
  --wallet ~/my.key --tx-id <LOCK_TX_ID> \
  --other-pubkey <OTHER_PUBKEY> --path a --rpc $RPC --json

# 2-of-3: any two of three
exfer script multisig2of3-lock \
  --wallet ~/party-a.key --pubkey-b <PK_B> --pubkey-c <PK_C> \
  --amount "10 EXFER" --rpc $RPC --json

exfer script multisig2of3-spend \
  --wallet ~/signer1.key --wallet2 ~/signer2.key \
  --tx-id <LOCK_TX_ID> --to <DEST_ADDRESS> \
  --pubkey-a <PK_A> --pubkey-b <PK_B> --pubkey-c <PK_C> \
  --path ab --rpc $RPC --json
```

### 6. Vault (Timelock + Recovery)

```bash
# Lock: primary key spends after locktime, recovery key anytime
exfer script vault-lock \
  --wallet ~/primary.key --recovery-pubkey <RECOVERY_PK> \
  --locktime <BLOCK_HEIGHT> --amount "100 EXFER" --rpc $RPC --json

# Normal spend (after locktime)
exfer script vault-spend \
  --wallet ~/primary.key --tx-id <LOCK_TX_ID> \
  --recovery-pubkey <RECOVERY_PK> --locktime <HEIGHT> --rpc $RPC --json

# Emergency recovery (anytime)
exfer script vault-recover \
  --wallet ~/recovery.key --tx-id <LOCK_TX_ID> \
  --primary-pubkey <PRIMARY_PK> --locktime <HEIGHT> --rpc $RPC --json
```

### 7. Escrow (Mutual / Arbiter / Timeout)

```bash
# Lock
exfer script escrow-lock \
  --wallet ~/party-a.key --party-b <PK_B> --arbiter <PK_ARB> \
  --timeout <BLOCK_HEIGHT> --amount "50 EXFER" --rpc $RPC --json

# Mutual release (both parties sign)
exfer script escrow-release \
  --wallet ~/party-a.key --wallet2 ~/party-b.key \
  --tx-id <LOCK_TX_ID> --to <DEST_ADDRESS> \
  --party-a <PK_A> --party-b <PK_B> --arbiter <PK_ARB> \
  --timeout <HEIGHT> --rpc $RPC --json

# Arbiter decides
exfer script escrow-arbitrate \
  --wallet ~/arbiter.key --tx-id <LOCK_TX_ID> --to <DEST_ADDRESS> \
  --party-a <PK_A> --party-b <PK_B> --timeout <HEIGHT> --rpc $RPC --json

# Timeout refund (party A, after timeout)
exfer script escrow-reclaim \
  --wallet ~/party-a.key --tx-id <LOCK_TX_ID> \
  --party-b <PK_B> --arbiter <PK_ARB> --timeout <HEIGHT> --rpc $RPC --json
```

### 8. Delegation (Owner + Time-Limited Delegate)

```bash
# Lock
exfer script delegation-lock \
  --wallet ~/owner.key --delegate <DELEGATE_PK> \
  --expiry <BLOCK_HEIGHT> --amount "10 EXFER" --rpc $RPC --json

# Owner spend (anytime)
exfer script delegation-owner-spend \
  --wallet ~/owner.key --tx-id <LOCK_TX_ID> \
  --delegate <DELEGATE_PK> --expiry <HEIGHT> --rpc $RPC --json

# Delegate spend (before expiry only)
exfer script delegation-delegate-spend \
  --wallet ~/delegate.key --tx-id <LOCK_TX_ID> \
  --owner <OWNER_PK> --expiry <HEIGHT> --rpc $RPC --json
```

### 9. Mining

```bash
exfer mine \
  --datadir ~/.exfer \
  --miner-pubkey <YOUR_PUBKEY> \
  --rpc-bind 127.0.0.1:9334 \
  --repair-perms
```

Block reward: ~100 EXFER, block time target: 10 seconds.

---

## Pitfalls

- **Wallet file is the private key** — never share it, never commit it. Back it up offline.
- **Coinbase maturity** — mined rewards require 360 block confirmations before spending (~1 hour).
- **HTLC timeout** — set timeout high enough for the receiver to claim (500+ blocks recommended). Too short risks funds locked in limbo.
- **Escrow/vault timeouts** — time-locked commands check the current block height client-side and refuse to submit if the condition isn't met. The node also enforces this at consensus.
- **Fee too low** — the default fee (100000 exfers = 0.001 EXFER) is sufficient for simple transactions. Covenant spends with large scripts may need a higher fee. The node rejects insufficient fees with a clear error.
- **Distinct keys** — lock commands reject identical pubkeys for distinct roles (e.g., same key as both multisig parties). This is enforced client-side.
- **Public RPC** — the default RPC endpoint has no authentication. For production, run your own node.

---

## Verification

```bash
# Check connectivity and chain height
curl -s -X POST http://82.221.100.201:9334 -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"get_block_height","params":{},"id":1}'

# Generate a wallet (no network needed)
exfer wallet generate --output /tmp/test-wallet.key --json

# Check a known address balance
curl -s -X POST http://82.221.100.201:9334 -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"get_balance","params":{"address":"5f817411356fa7d622888cb3632586f1cf6812a73890bac872f04b5cc5ab21f0"},"id":1}'
```
