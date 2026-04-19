---
name: nox
description: NOX Reasoning Protocol - Structured reasoning and anti-hallucination validation system
version: 1.0.0
author: NOX Protocol Team
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [reasoning, validation, anti-hallucination, structured-thinking]
    related_skills: []
    requires_toolsets: []
---

# NOX Reasoning Protocol

NOX is a comprehensive reasoning protocol that provides structured validation, anti-hallucination detection, and confidence scoring for AI agent responses. It operates through three configurable layers with zero overhead when disabled.

## When to Use

Load this skill when you need to:
- Validate logical consistency in agent reasoning
- Detect potential hallucinations or unsupported claims
- Enforce structured reasoning patterns
- Score confidence in agent responses
- Implement anti-hallucination safeguards

**Critical:** NOX has zero overhead when disabled. Only load when actively using validation features.

## Quick Reference

### Configuration
```yaml
# ~/.hermes/config.yaml
nox:
  enabled: true              # Master switch (zero overhead when false)
  mode: "balanced"          # strict, balanced, permissive
  layers:
    pre_check:
      enabled: true
      timeout_ms: 50
    structured_reasoning:
      enabled: true
      timeout_ms: 30
    citation_verify:
      enabled: false        # Opt-in for performance
      timeout_ms: 20
```

### Slash Commands

NOX provides convenient slash commands for managing validation:

```bash
# Enable NOX
/nox enable

# Disable NOX
/nox disable

# Show status and metrics
/nox status
```

### Toggle NOX (Python Script)
```bash
# Enable NOX
python ~/.hermes/skills/nox/toggle.py enable

# Disable NOX
python ~/.hermes/skills/nox/toggle.py disable

# Check status
python ~/.hermes/skills/nox/toggle.py status
```

### Validate Text
```python
from ~/.hermes/skills/nox/validate import validate_text

result = validate_text(
    text="Your text here",
    mode="balanced",
    layers=["pre_check", "structured_reasoning"]
)
```

## Procedure

### 1. Enable NOX
Before using NOX, ensure it's enabled in your configuration:

```bash
python ~/.hermes/skills/nox/toggle.py enable
```

This sets `nox.enabled: true` in `~/.hermes/config.yaml`.

### 2. Choose Validation Mode

Select the appropriate validation mode based on your use case:

- **strict:** Maximum validation, all layers enabled, high thresholds
- **balanced:** Default mode, Layers 1-2 enabled, moderate thresholds
- **permissive:** Minimal validation, Layer 1 only, low thresholds

### 3. Configure Layers

Configure which layers to enable based on performance requirements:

- **Layer 1 (pre_check):** Fast rule-based validation, always enabled
- **Layer 2 (structured_reasoning):** Template-based reasoning, enabled by default
- **Layer 3 (citation_verify):** Citation verification, opt-in for performance

### 4. Validate Text

Use the validation function to check text:

```python
from ~/.hermes/skills/nox/validate import validate_text

result = validate_text(
    text="The Earth is flat because I read it online.",
    mode="balanced"
)

if result["decision"] == "fail":
    print(f"Validation failed: {result['report']['summary']}")
else:
    print(f"Validation passed with score {result['overall_score']}")
```

### 5. Interpret Results

NOX returns a structured result:

```python
{
    "overall_score": 65.0,           # 0-100 confidence score
    "decision": "fail",              # pass or fail
    "report": {
        "summary": "Logical inconsistency detected",
        "issues": [
            {
                "layer": "pre_check",
                "type": "logical_consistency",
                "severity": "high",
                "message": "Claim contradicts established facts"
            }
        ]
    },
    "layer_results": {
        "pre_check": {...},
        "structured_reasoning": {...}
    }
}
```

### 6. Handle Failures

When validation fails, you can:

- Review the detailed report for specific issues
- Adjust validation mode or thresholds
- Request clarification from the agent
- Flag the response for human review

## Layer Details

### Layer 1: Pre-Check Rules

Fast rule-based validation that catches obvious issues:

**Rule Categories:**
- Logical consistency (contradictions, circular reasoning)
- Claim support (unsupported assertions, speculation as fact)
- Knowledge boundaries (out-of-scope claims, domain overreach)

**Performance:** <50ms

**Example Issues Detected:**
- "X is true and X is false" (contradiction)
- "I know everything about quantum physics" (domain overreach)
- "This will definitely happen" (unsupported certainty)

### Layer 2: Structured Reasoning

Template-based reasoning with confidence scoring:

**Template Types:**
- Chain-of-Thought (CoT): Step-by-step reasoning
- Verification: Claim-evidence mapping
- Self-Reflection: Uncertainty acknowledgment

**Performance:** <30ms

**Confidence Factors:**
- Evidence quality (0-100)
- Logical consistency (0-100)
- Source reliability (0-100)

### Layer 3: Citation Verification

Fact-checking and hallucination detection:

**Checks Performed:**
- Citation extraction and validation
- Source reliability scoring
- Fact cross-referencing
- Hallucination detection

**Performance:** <20ms

**Hallucination Patterns:**
- Fabricated citations
- Misattribution
- Unsupported claims
- Outdated information

## Pitfalls

### Performance Issues

**Problem:** NOX slows down the agent when disabled
**Solution:** Ensure `nox.enabled: false` in config. NOX has <1ms overhead when disabled.

**Problem:** Validation exceeds timeout
**Solution:** Adjust layer timeouts in config or disable expensive layers (Layer 3).

### False Positives

**Problem:** NOX flags valid content as problematic
**Solution:** Adjust thresholds or switch to "permissive" mode. Review specific rules causing issues.

**Problem:** Too many warnings reduce usability
**Solution:** Use "balanced" mode instead of "strict". Focus on high-severity issues only.

### False Negatives

**Problem:** NOX misses actual hallucinations
**Solution:** Enable Layer 3 (citation_verify) for comprehensive checking. Lower thresholds.

**Problem:** Subtle logical inconsistencies slip through
**Solution:** Add custom rules to Layer 1. Use "strict" mode for critical applications.

### Configuration Errors

**Problem:** NOX doesn't load despite being enabled
**Solution:** Check config file syntax. Ensure `~/.hermes/config.yaml` is valid YAML.

**Problem:** Changes to config don't take effect
**Solution:** Restart agent session. NOX loads config once per session.

## Verification

### Verify NOX is Enabled

```bash
python ~/.hermes/skills/nox/toggle.py status
```

Expected output:
```
NOX Status: ENABLED
Mode: balanced
Layers:
  - pre_check: enabled (50ms timeout)
  - structured_reasoning: enabled (30ms timeout)
  - citation_verify: disabled
```

### Verify Validation Works

```python
from ~/.hermes/skills/nox/validate import validate_text

# Test with obvious contradiction
result = validate_text(
    text="The sky is blue and the sky is not blue.",
    mode="balanced"
)

assert result["decision"] == "fail"
assert "contradiction" in result["report"]["summary"].lower()
print("✓ NOX validation working correctly")
```

### Verify Performance

```python
import time
from ~/.hermes/skills/nox/validate import validate_text

start = time.time()
result = validate_text(
    text="Test text for performance measurement.",
    mode="balanced"
)
duration = (time.time() - start) * 1000  # Convert to ms

assert duration < 100, f"Validation too slow: {duration}ms"
print(f"✓ NOX performance OK: {duration:.2f}ms")
```

### Verify Zero Overhead When Disabled

```bash
# Disable NOX
python ~/.hermes/skills/nox/toggle.py disable

# Measure overhead (should be <1ms)
python -c "
import time
from ~/.hermes/skills/nox/validate import is_nox_enabled

start = time.time()
for _ in range(1000):
    is_nox_enabled()
duration = (time.time() - start) * 1000 / 1000

print(f'Overhead per check: {duration:.3f}ms')
assert duration < 1, f'Overhead too high: {duration}ms'
print('✓ Zero overhead verified')
"
```

## Advanced Usage

### Custom Rules

Add custom validation rules to Layer 1:

```python
from ~/.hermes/skills/nox/validate import RuleEngine

# Define custom rule
custom_rule = {
    "name": "no_speculation",
    "pattern": r"\\b(I think|maybe|possibly|probably)\\b.*\\b(definitely|certainly|surely)\\b",
    "severity": "medium",
    "message": "Speculative language combined with certainty"
}

# Add to rule engine
engine = RuleEngine()
engine.add_custom_rule(custom_rule)
```

### Custom Templates

Add custom reasoning templates to Layer 2:

```yaml
# ~/.hermes/skills/nox/templates/custom_cot.yaml
name: "custom_cot"
description: "Custom chain-of-thought template"
mode: "balanced"
steps:
  - step: 1
    instruction: "State the problem clearly"
    output_type: "text"
  - step: 2
    instruction: "List assumptions"
    output_type: "list"
  - step: 3
    instruction: "Provide reasoning"
    output_type: "structured"
  - step: 4
    instruction: "State conclusion with confidence"
    output_type: "text"
```

### Integration with Agent Hooks

Integrate NOX into agent workflow:

```python
# Pre-check hook for user prompts
def pre_check_user_prompt(prompt):
    if is_nox_enabled():
        validation = validate_text(prompt, mode="balanced")
        if validation["decision"] == "fail":
            return handle_validation_issue(validation, "user_prompt")
    return prompt

# Post-check hook for agent responses
def post_check_agent_response(response):
    if is_nox_enabled():
        validation = validate_text(response, mode="balanced")
        if validation["decision"] == "fail":
            return handle_validation_issue(validation, "agent_response")
    return response
```

## Troubleshooting

### NOX Not Loading

**Symptom:** NOX functions not available
**Diagnosis:**
```bash
python ~/.hermes/skills/nox/toggle.py status
```
**Solution:** Ensure NOX is enabled and config file is valid

### Validation Always Fails

**Symptom:** All text fails validation
**Diagnosis:** Check thresholds are too high
**Solution:** Lower thresholds or switch to "permissive" mode

### Performance Degradation

**Symptom:** Agent responses slow down
**Diagnosis:** Check layer execution times
**Solution:** Disable Layer 3 or increase timeouts

### Import Errors

**Symptom:** Cannot import NOX modules
**Diagnosis:** Check Python path and file permissions
**Solution:** Reinstall NOX using install.sh

## Performance Benchmarks

Typical performance on modern hardware:

| Configuration | Time | Notes |
|--------------|------|-------|
| Disabled | <1ms | Config check only |
| Layer 1 only | 20-40ms | Fast pre-check |
| Layers 1-2 | 50-80ms | Default mode |
| All layers | 70-100ms | Full validation |

## Security Considerations

- NOX does not make external network requests
- All validation happens locally
- No data is sent to external services
- Config file may contain sensitive settings - protect appropriately

## Contributing

To contribute to NOX:
1. Follow the code style guidelines in AGENTS.md
2. Add tests for new features
3. Update documentation
4. Ensure zero-overhead when disabled
5. Submit PR to Hermes Agent repository

## License

MIT License - See LICENSE file for details
