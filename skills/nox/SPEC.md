# NOX Technical Specification

**Version:** 1.0.0  
**Status:** Stable  
**Last Updated:** 2025-04-19

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Documentation](#api-documentation)
4. [Performance Requirements](#performance-requirements)
5. [Testing Strategy](#testing-strategy)
6. [Security Considerations](#security-considerations)
7. [Future Enhancements](#future-enhancements)

---

## Overview

NOX (Night Operations eXaminer) is a comprehensive reasoning protocol for AI agents that provides structured validation, anti-hallucination detection, and confidence scoring. It operates through three configurable layers with zero overhead when disabled.

### Design Goals

1. **Zero Overhead When Disabled:** <1ms overhead when NOX is disabled
2. **Fast Validation:** <100ms for full validation (all layers)
3. **Configurable Layers:** Enable/disable layers based on performance needs
4. **Comprehensive Coverage:** Detect logical inconsistencies, hallucinations, and unsupported claims
5. **Simple Configuration:** YAML-based configuration in `~/.hermes/config.yaml`

### Key Features

- **Layer 1:** Fast rule-based pre-check (<50ms)
- **Layer 2:** Template-based structured reasoning (configurable)
- **Layer 3:** Citation verification and fact-checking (opt-in)
- **Multiple Validation Modes:** strict, balanced, permissive
- **Confidence Scoring:** 0-100 score with detailed metrics
- **Human-Readable Reports:** Detailed issue reports with severity levels

---

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    NOX Protocol                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐│
│  │   Layer 1    │    │   Layer 2    │    │  Layer 3   ││
│  │  Pre-Check   │───▶│  Structured  │───▶│  Citation  ││
│  │   Rules      │    │  Reasoning   │    │  Verify    ││
│  │  (<50ms)     │    │  (config)    │    │  (config)  ││
│  └──────────────┘    └──────────────┘    └────────────┘│
│         │                   │                   │       │
│         └───────────────────┴───────────────────┘       │
│                             │                           │
│                             ▼                           │
│                    ┌──────────────┐                     │
│                    │  Result      │                     │
│                    │  Aggregator  │                     │
│                    └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

### Component Architecture

#### Configuration Layer

- **NOXConfig:** Singleton configuration manager with lazy loading
- **Fast Path Check:** <1ms check for enabled status
- **YAML Parser:** Parse configuration from `~/.hermes/config.yaml`

#### Validation Layers

**Layer 1: RuleEngine**
- Fast pattern matching using compiled regex
- Pre-defined rule sets for different validation types
- Early termination on critical failures
- Parallel rule execution

**Layer 2: TemplateEngine**
- Template library with pre-defined reasoning templates
- Variable substitution and template execution
- Confidence scoring based on template execution
- Mode-specific template selection

**Layer 3: CitationVerifier**
- Citation extraction using regex patterns
- Source validation and reliability scoring
- Fact-checking against sources
- Hallucination detection

#### Result Aggregation

**ResultAggregator**
- Collect results from enabled layers
- Calculate weighted overall score
- Make pass/fail decisions based on thresholds
- Generate human-readable reports

### Data Flow

```
User Input
    │
    ▼
Fast Path Check (<1ms)
    │
    ├─ Disabled → Return immediately (zero overhead)
    │
    └─ Enabled → Continue
              │
              ▼
        Load Configuration
              │
              ▼
        Run Enabled Layers
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
Layer 1   Layer 2   Layer 3
    │         │         │
    └─────────┼─────────┘
              ▼
        Aggregate Results
              │
              ▼
        Generate Report
              │
              ▼
        Return NOXResult
```

---

## API Documentation

### Configuration API

#### `NOXConfig`

Configuration manager with lazy loading.

**Properties:**

- `enabled: bool` - Check if NOX is enabled (cached)
- `config: Dict[str, Any]` - Get full NOX configuration (lazy loaded)

**Methods:**

- `get_mode() -> ValidationMode` - Get validation mode
- `get_layer_config(layer_name: str) -> Dict[str, Any]` - Get layer configuration
- `get_thresholds() -> Dict[str, float]` - Get validation thresholds
- `is_layer_enabled(layer_name: str) -> bool` - Check if layer is enabled

**Example:**

```python
config = get_nox_config()
if config.enabled:
    mode = config.get_mode()
    thresholds = config.get_thresholds()
```

#### `is_nox_enabled()`

Fast check if NOX is enabled (<1ms).

**Returns:** `bool`

**Example:**

```python
if is_nox_enabled():
    # Perform validation
    result = validate_text(text)
```

### Validation API

#### `validate_text(text: str, mode: Optional[str] = None, layers: Optional[List[str]] = None) -> NOXResult`

Validate text using NOX protocol.

**Parameters:**

- `text: str` - Text to validate
- `mode: Optional[str]` - Validation mode (strict, balanced, permissive). If None, uses config.
- `layers: Optional[List[str]]` - List of layers to enable. If None, uses config.

**Returns:** `NOXResult`

**Example:**

```python
result = validate_text(
    text="The Earth is flat because I read it online.",
    mode="balanced"
)

if result.decision == "fail":
    print(f"Validation failed: {result.report['summary']}")
```

#### `NOXResult`

Complete NOX validation result.

**Properties:**

- `overall_score: float` - Overall confidence score (0-100)
- `decision: str` - Pass/fail decision ("pass" or "fail")
- `report: Dict[str, Any]` - Human-readable report
- `layer_results: Dict[str, LayerResult]` - Results from each layer
- `total_time_ms: float` - Total validation time in milliseconds

**Example:**

```python
print(f"Score: {result.overall_score}")
print(f"Decision: {result.decision}")
print(f"Time: {result.total_time_ms}ms")
```

#### `LayerResult`

Result from a single validation layer.

**Properties:**

- `layer_name: str` - Name of the layer
- `enabled: bool` - Whether the layer was enabled
- `execution_time_ms: float` - Execution time in milliseconds
- `result: Optional[ValidationResult]` - Validation result (if successful)
- `error: Optional[str]` - Error message (if failed)

#### `ValidationResult`

Result from a single validation check.

**Properties:**

- `passed: bool` - Whether validation passed
- `score: float` - Confidence score (0-100)
- `issues: List[Dict[str, Any]]` - List of issues found
- `metadata: Dict[str, Any]` - Additional metadata

### Toggle API

#### `enable_nox(mode: str = "balanced") -> bool`

Enable NOX with specified mode.

**Parameters:**

- `mode: str` - Validation mode (strict, balanced, permissive)

**Returns:** `bool` - True if successful

**Example:**

```python
if enable_nox("balanced"):
    print("NOX enabled")
```

#### `disable_nox() -> bool`

Disable NOX (zero overhead mode).

**Returns:** `bool` - True if successful

**Example:**

```python
if disable_nox():
    print("NOX disabled")
```

#### `set_nox_mode(mode: str) -> bool`

Set NOX validation mode.

**Parameters:**

- `mode: str` - Validation mode (strict, balanced, permissive)

**Returns:** `bool` - True if successful

**Example:**

```python
if set_nox_mode("strict"):
    print("Mode set to strict")
```

---

## Performance Requirements

### Performance Targets

| Configuration | Time | Notes |
|--------------|------|-------|
| Disabled | <1ms | Config check only |
| Layer 1 only | 20-40ms | Fast pre-check |
| Layers 1-2 | 50-80ms | Default mode |
| All layers | 70-100ms | Full validation |

### Layer Performance

**Layer 1 (Pre-Check):**
- Target: <50ms
- Timeout: Configurable (default: 50ms)
- Optimization: Compiled regex, early termination

**Layer 2 (Structured Reasoning):**
- Target: <30ms
- Timeout: Configurable (default: 30ms)
- Optimization: Template caching, lazy loading

**Layer 3 (Citation Verification):**
- Target: <20ms
- Timeout: Configurable (default: 20ms)
- Optimization: Source caching, parallel validation

### Zero-Overhead Design

**Lazy Loading:**
- NOX components only load when `nox.enabled: true`
- All imports happen inside the enabled check
- No initialization cost when disabled

**Fast Path Check:**
```python
def nox_validate(text):
    if not is_nox_enabled():
        return None  # Zero overhead
    # ... rest of validation
```

**Optional Layers:**
- Layer 3 (citation verification) disabled by default
- Users opt-in to expensive features
- Most users get fast validation with Layers 1-2 only

### Performance Monitoring

Built-in timing for each layer:
- Warn if layers exceed timeout
- Auto-disable slow layers
- Log performance metrics

---

## Testing Strategy

### Unit Tests

**Configuration Tests:**
- Test configuration loading
- Test lazy loading behavior
- Test fast path check
- Test layer enable/disable

**Layer 1 Tests:**
- Test rule matching
- Test rule execution
- Test timeout handling
- Test score calculation

**Layer 2 Tests:**
- Test template selection
- Test template execution
- Test confidence scoring
- Test timeout handling

**Layer 3 Tests:**
- Test citation extraction
- Test source validation
- Test hallucination detection
- Test timeout handling

**Aggregator Tests:**
- Test result aggregation
- Test score calculation
- Test decision making
- Test report generation

### Integration Tests

**End-to-End Tests:**
- Test full validation pipeline
- Test multi-layer validation
- Test configuration integration
- Test performance targets

**Mode Tests:**
- Test strict mode
- Test balanced mode
- Test permissive mode
- Test custom mode

### Performance Tests

**Benchmark Tests:**
- Measure validation time for each layer
- Measure total validation time
- Measure overhead when disabled
- Verify performance targets

**Stress Tests:**
- Test with large texts
- Test with many rules
- Test with many citations
- Test with concurrent validations

### Regression Tests

**Known Issues:**
- Test for fixed bugs
- Test for edge cases
- Test for boundary conditions
- Test for error handling

---

## Security Considerations

### Data Privacy

- **No External Requests:** NOX does not make external network requests
- **Local Processing:** All validation happens locally
- **No Data Transmission:** No data is sent to external services
- **Config Protection:** Config file may contain sensitive settings

### Input Validation

- **Sanitize Input:** All user input is sanitized before processing
- **Prevent Injection:** Regex patterns are validated to prevent ReDoS
- **Length Limits:** Maximum text length enforced to prevent DoS
- **Timeout Enforcement:** All layers have configurable timeouts

### Error Handling

- **Graceful Degradation:** Failures don't crash the system
- **Error Logging:** All errors are logged with context
- **User Feedback:** Clear error messages for users
- **Recovery:** System can recover from errors

### Access Control

- **File Permissions:** Config files have appropriate permissions
- **Execution Permissions:** Scripts have appropriate permissions
- **User Isolation:** Each user has their own configuration
- **No Privilege Escalation:** No operations require elevated privileges

---

## Future Enhancements

### Planned Features

**v1.1.0:**
- Custom rule editor
- Template marketplace
- Performance dashboard
- Integration with more agent frameworks

**v1.2.0:**
- Machine learning-based validation
- Adaptive thresholds
- Real-time validation
- Multi-language support

**v2.0.0:**
- Distributed validation
- Cloud-based verification
- Advanced citation analysis
- Plugin system

### Potential Improvements

**Performance:**
- Caching layer for repeated validations
- Parallel execution of independent rules
- Optimized regex patterns
- Pre-compiled templates

**Features:**
- More validation modes
- Custom severity levels
- Integration with external fact-checking services
- Support for more citation formats

**Usability:**
- GUI configuration tool
- Interactive validation reports
- Integration with IDEs
- Real-time feedback

---

## Appendix

### Glossary

- **NOX:** Night Operations eXaminer - The reasoning protocol
- **Layer:** A validation stage in the NOX protocol
- **Rule:** A pattern-based validation check
- **Template:** A structured reasoning pattern
- **Citation:** A reference to a source
- **Hallucination:** A false or fabricated claim
- **Confidence Score:** A 0-100 score indicating validation confidence

### References

- Hermes Agent Documentation: https://github.com/NousResearch/hermes-agent
- YAML Specification: https://yaml.org/spec/
- Python Documentation: https://docs.python.org/3/

### Version History

See CHANGELOG.md for detailed version history.
