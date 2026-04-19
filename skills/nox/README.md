# NOX - Night Operations eXaminer

**Structured Reasoning and Anti-Hallucination Protocol for AI Agents**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/NousResearch/hermes-agent)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)](https://www.python.org/)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Validation Modes](#validation-modes)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

NOX is a comprehensive reasoning protocol for AI agents that provides structured validation, anti-hallucination detection, and confidence scoring. It operates through three configurable layers with zero overhead when disabled.

### What NOX Does

- **Detects Logical Inconsistencies:** Identifies contradictions and circular reasoning
- **Flags Unsupported Claims:** Highlights assertions without evidence
- **Enforces Structured Reasoning:** Applies step-by-step verification templates
- **Verifies Citations:** Cross-references claims with sources
- **Detects Hallucinations:** Identifies fabricated or misattributed information
- **Scores Confidence:** Provides 0-100 confidence metrics

### Key Benefits

- **Zero Overhead When Disabled:** <1ms overhead when NOX is disabled
- **Fast Validation:** <100ms for full validation (all layers)
- **Configurable Layers:** Enable/disable layers based on performance needs
- **Simple Configuration:** YAML-based configuration
- **Cross-Platform:** Works on Linux, macOS, and Windows
- **No External Dependencies:** Uses only Python stdlib and existing Hermes tools

---

## Features

### Three-Layer Architecture

**Layer 1: Fast Pre-Check (<50ms)**
- Rule-based validation
- Logical consistency checks
- Claim support verification
- Knowledge boundary detection

**Layer 2: Structured Reasoning (configurable)**
- Template-based reasoning
- Chain-of-thought templates
- Confidence scoring
- Self-reflection templates

**Layer 3: Citation Verification (opt-in)**
- Citation extraction
- Source validation
- Fact-checking
- Hallucination detection

### Validation Modes

- **Strict:** Maximum validation, all layers enabled, high thresholds
- **Balanced:** Default mode, Layers 1-2 enabled, moderate thresholds
- **Permissive:** Minimal validation, Layer 1 only, low thresholds

### Performance Guarantees

| Configuration | Time | Notes |
|--------------|------|-------|
| Disabled | <1ms | Config check only |
| Layer 1 only | 20-40ms | Fast pre-check |
| Layers 1-2 | 50-80ms | Default mode |
| All layers | 70-100ms | Full validation |

---

## Installation

### Prerequisites

- Hermes Agent installed
- Python 3.11+
- YAML support (usually included with Python)

### Install NOX

```bash
# Navigate to NOX directory
cd ~/.hermes/skills/nox

# Run installation script
./install.sh
```

The installation script will:
- Create necessary directories
- Copy all files to appropriate locations
- Set file permissions
- Create symbolic links for easy access
- Verify installation

### Verify Installation

```bash
# Check NOX status
python3 ~/.hermes/skills/nox/toggle.py status

# Expected output:
# NOX Status: DISABLED
# Mode: balanced
# Layers:
#   - Pre-Check: disabled (50ms timeout)
#   - Structured Reasoning: disabled (30ms timeout)
#   - Citation Verification: disabled
```

---

## Quick Start

### Enable NOX

```bash
# Enable NOX with balanced mode (default)
python3 ~/.hermes/skills/nox/toggle.py enable

# Or specify a mode
python3 ~/.hermes/skills/nox/toggle.py enable strict
```

### Validate Text

```bash
# Validate a simple text
python3 ~/.hermes/skills/nox/validate.py "The sky is blue and the sky is not blue."

# Expected output:
# Decision: fail
# Overall Score: 70.0
# Total Time: 25.34ms
#
# Report: Validation failed: 1 issue(s) detected
#
# Issues:
#   - [HIGH] Contradictory statements detected
```

### Check Status

```bash
# Check current NOX status
python3 ~/.hermes/skills/nox/toggle.py status
```

### Disable NOX

```bash
# Disable NOX (zero overhead mode)
python3 ~/.hermes/skills/nox/toggle.py disable
```

---

## Configuration

### Configuration File

NOX configuration is stored in `~/.hermes/config.yaml`:

```yaml
nox:
  # Master switch - zero overhead when false
  enabled: true
  
  # Validation mode
  mode: "balanced"  # strict, balanced, permissive
  
  # Layer configuration
  layers:
    pre_check:
      enabled: true
      timeout_ms: 50
    
    structured_reasoning:
      enabled: true
      timeout_ms: 30
    
    citation_verify:
      enabled: false  # Opt-in for performance
      timeout_ms: 20
  
  # Thresholds
  thresholds:
    overall_score: 70
    logical_consistency: 80
    evidence_quality: 60
  
  # Performance settings
  performance:
    cache_enabled: true
    parallel_execution: true
    early_termination: true
```

### Configuration Options

**Master Switch (`enabled`)**
- `true`: NOX is active and validates text
- `false`: NOX is disabled with zero overhead

**Validation Mode (`mode`)**
- `strict`: Maximum validation, all layers enabled
- `balanced`: Default mode, Layers 1-2 enabled
- `permissive`: Minimal validation, Layer 1 only

**Layer Configuration (`layers`)**
- `enabled`: Enable/disable specific layer
- `timeout_ms`: Maximum execution time for layer

**Thresholds (`thresholds`)**
- `overall_score`: Minimum overall score to pass (0-100)
- `logical_consistency`: Minimum logical consistency score (0-100)
- `evidence_quality`: Minimum evidence quality score (0-100)

**Performance Settings (`performance`)**
- `cache_enabled`: Enable caching for repeated validations
- `parallel_execution`: Enable parallel execution of independent rules
- `early_termination`: Stop validation on critical failures

---

## Usage

### Command Line Interface

#### Toggle Commands

```bash
# Enable NOX
python3 ~/.hermes/skills/nox/toggle.py enable [mode]

# Disable NOX
python3 ~/.hermes/skills/nox/toggle.py disable

# Set mode
python3 ~/.hermes/skills/nox/toggle.py mode <strict|balanced|permissive>

# Enable specific layer
python3 ~/.hermes/skills/nox/toggle.py enable-layer <layer_name>

# Disable specific layer
python3 ~/.hermes/skills/nox/toggle.py disable-layer <layer_name>

# Check status
python3 ~/.hermes/skills/nox/toggle.py status
```

#### Validation Commands

```bash
# Validate text
python3 ~/.hermes/skills/nox/validate.py "Your text here"

# Validate with specific mode
python3 ~/.hermes/skills/nox/validate.py "Your text here" --mode strict

# Validate with specific layers
python3 ~/.hermes/skills/nox/validate.py "Your text here" --layers pre_check structured_reasoning
```

### Python API

#### Basic Usage

```python
from ~/.hermes/skills/nox/validate import validate_text, is_nox_enabled

# Check if NOX is enabled
if is_nox_enabled():
    # Validate text
    result = validate_text(
        text="The Earth is flat because I read it online.",
        mode="balanced"
    )
    
    # Check result
    if result.decision == "fail":
        print(f"Validation failed: {result.report['summary']}")
        for issue in result.report['issues']:
            print(f"  - [{issue['severity'].upper()}] {issue['message']}")
    else:
        print(f"Validation passed with score {result.overall_score:.1f}")
```

#### Advanced Usage

```python
from ~/.hermes/skills/nox/validate import validate_text, get_nox_config

# Get configuration
config = get_nox_config()

# Validate with custom layers
result = validate_text(
    text="Your text here",
    mode="strict",
    layers=["pre_check", "structured_reasoning", "citation_verify"]
)

# Access layer results
for layer_name, layer_result in result.layer_results.items():
    if layer_result.enabled and layer_result.result:
        print(f"{layer_name}: {layer_result.result.score:.1f}")
        print(f"  Time: {layer_result.execution_time_ms:.2f}ms")
        if layer_result.result.issues:
            for issue in layer_result.result.issues:
                print(f"  - {issue['message']}")
```

#### Integration with Agent Hooks

```python
from ~/.hermes/skills/nox/validate import validate_text, is_nox_enabled

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

---

## Validation Modes

### Strict Mode

Maximum validation with all layers enabled and high thresholds.

**Configuration:**
```yaml
nox:
  enabled: true
  mode: "strict"
  layers:
    pre_check:
      enabled: true
      timeout_ms: 50
    structured_reasoning:
      enabled: true
      timeout_ms: 30
    citation_verify:
      enabled: true
      timeout_ms: 20
  thresholds:
    overall_score: 85
    logical_consistency: 90
    evidence_quality: 75
```

**Use Cases:**
- Critical applications requiring high confidence
- Research validation
- Fact-checking important claims
- Production systems with strict quality requirements

**Performance:** 70-100ms

### Balanced Mode

Default mode with Layers 1-2 enabled and moderate thresholds.

**Configuration:**
```yaml
nox:
  enabled: true
  mode: "balanced"
  layers:
    pre_check:
      enabled: true
      timeout_ms: 50
    structured_reasoning:
      enabled: true
      timeout_ms: 30
    citation_verify:
      enabled: false
      timeout_ms: 20
  thresholds:
    overall_score: 70
    logical_consistency: 80
    evidence_quality: 60
```

**Use Cases:**
- General-purpose validation
- Everyday agent interactions
- Balanced performance and accuracy
- Default mode for most users

**Performance:** 50-80ms

### Permissive Mode

Minimal validation with Layer 1 only and low thresholds.

**Configuration:**
```yaml
nox:
  enabled: true
  mode: "permissive"
  layers:
    pre_check:
      enabled: true
      timeout_ms: 50
    structured_reasoning:
      enabled: false
      timeout_ms: 30
    citation_verify:
      enabled: false
      timeout_ms: 20
  thresholds:
    overall_score: 50
    logical_consistency: 60
    evidence_quality: 40
```

**Use Cases:**
- Fast validation with minimal overhead
- Casual interactions
- Prototyping and development
- Performance-critical applications

**Performance:** 20-40ms

---

## Performance

### Performance Targets

| Configuration | Time | Notes |
|--------------|------|-------|
| Disabled | <1ms | Config check only |
| Layer 1 only | 20-40ms | Fast pre-check |
| Layers 1-2 | 50-80ms | Default mode |
| All layers | 70-100ms | Full validation |

### Optimization Tips

1. **Disable Unused Layers:** Only enable layers you need
2. **Use Permissive Mode:** For fast validation, use permissive mode
3. **Adjust Timeouts:** Increase timeouts if validation is failing
4. **Enable Caching:** Enable cache for repeated validations
5. **Use Balanced Mode:** For most use cases, balanced mode is optimal

### Performance Monitoring

NOX includes built-in performance monitoring:

```python
result = validate_text("Your text here")

# Check total time
print(f"Total time: {result.total_time_ms:.2f}ms")

# Check layer times
for layer_name, layer_result in result.layer_results.items():
    if layer_result.enabled:
        print(f"{layer_name}: {layer_result.execution_time_ms:.2f}ms")
```

---

## Troubleshooting

### NOX Not Loading

**Symptom:** NOX functions not available

**Diagnosis:**
```bash
python3 ~/.hermes/skills/nox/toggle.py status
```

**Solution:**
- Ensure NOX is enabled
- Check config file syntax
- Verify file permissions
- Reinstall NOX using install.sh

### Validation Always Fails

**Symptom:** All text fails validation

**Diagnosis:**
- Check thresholds are too high
- Review specific rules causing issues

**Solution:**
- Lower thresholds in config
- Switch to "permissive" mode
- Review and adjust rules

### Performance Degradation

**Symptom:** Agent responses slow down

**Diagnosis:**
- Check layer execution times
- Monitor total validation time

**Solution:**
- Disable Layer 3 (citation_verify)
- Increase timeouts
- Use "permissive" mode

### Import Errors

**Symptom:** Cannot import NOX modules

**Diagnosis:**
- Check Python path
- Verify file permissions

**Solution:**
- Reinstall NOX using install.sh
- Check Python version (3.11+)
- Verify file permissions

### Configuration Errors

**Symptom:** Changes to config don't take effect

**Diagnosis:**
- Check config file syntax
- Verify YAML format

**Solution:**
- Validate YAML syntax
- Restart agent session
- Check file permissions

---

## Contributing

We welcome contributions to NOX! Please see the [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone Hermes Agent repository
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent

# Install dependencies
uv venv venv --python 3.11
source venv/bin/activate
uv pip install -e ".[all,dev]"

# Navigate to NOX skill
cd skills/nox

# Run tests
pytest tests/

# Run linting
pylint nox/
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for all functions
- Add tests for new features
- Update documentation

### Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

---

## License

MIT License - See [LICENSE](LICENSE) file for details

---

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/NousResearch/hermes-agent/issues
- Discord: https://discord.gg/NousResearch
- Documentation: See [SPEC.md](SPEC.md) and [SKILL.md](SKILL.md)

---

## Acknowledgments

NOX is part of the Hermes Agent project by Nous Research.

Special thanks to:
- The Hermes Agent team
- The Nous Research community
- All contributors and testers

---

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.
