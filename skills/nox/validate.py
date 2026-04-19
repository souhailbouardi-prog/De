#!/usr/bin/env python3
"""
NOX Validation - Core validation logic for NOX reasoning protocol

Implements three-layer validation system:
- Layer 1: Fast rule-based pre-check (<50ms)
- Layer 2: Template-based structured reasoning (configurable)
- Layer 3: Citation verification and fact-checking (opt-in)

Performance targets:
- Disabled: <1ms overhead
- Layers 1-2: <80ms total
- All layers: <100ms total
"""

import os
import re
import sys
import time
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# Configuration paths
CONFIG_PATH = Path.home() / ".hermes" / "config.yaml"
NOX_CONFIG_KEY = "nox"


class ValidationMode(Enum):
    """Validation modes."""
    STRICT = "strict"
    BALANCED = "balanced"
    PERMISSIVE = "permissive"


class Severity(Enum):
    """Issue severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result from a single validation check."""
    passed: bool
    score: float
    issues: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LayerResult:
    """Result from a validation layer."""
    layer_name: str
    enabled: bool
    execution_time_ms: float
    result: Optional[ValidationResult] = None
    error: Optional[str] = None


@dataclass
class NOXResult:
    """Complete NOX validation result."""
    overall_score: float
    decision: str  # "pass" or "fail"
    report: Dict[str, Any]
    layer_results: Dict[str, LayerResult]
    total_time_ms: float


# ============================================================================
# Configuration Management
# ============================================================================

class NOXConfig:
    """NOX configuration manager with lazy loading."""
    
    def __init__(self):
        self._config: Optional[Dict[str, Any]] = None
        self._enabled: Optional[bool] = None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not CONFIG_PATH.exists():
            return {}
        
        try:
            with open(CONFIG_PATH, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}
    
    @property
    def enabled(self) -> bool:
        """Check if NOX is enabled (cached)."""
        if self._enabled is None:
            config = self._load_config()
            nox_config = config.get(NOX_CONFIG_KEY, {})
            self._enabled = nox_config.get("enabled", False)
        return self._enabled
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get full NOX configuration (lazy loaded)."""
        if self._config is None:
            config = self._load_config()
            self._config = config.get(NOX_CONFIG_KEY, {})
        return self._config
    
    def get_mode(self) -> ValidationMode:
        """Get validation mode."""
        mode_str = self.config.get("mode", "balanced")
        try:
            return ValidationMode(mode_str)
        except ValueError:
            return ValidationMode.BALANCED
    
    def get_layer_config(self, layer_name: str) -> Dict[str, Any]:
        """Get configuration for a specific layer."""
        layers = self.config.get("layers", {})
        return layers.get(layer_name, {})
    
    def get_thresholds(self) -> Dict[str, float]:
        """Get validation thresholds."""
        return self.config.get("thresholds", {
            "overall_score": 70,
            "logical_consistency": 80,
            "evidence_quality": 60
        })
    
    def is_layer_enabled(self, layer_name: str) -> bool:
        """Check if a layer is enabled."""
        layer_config = self.get_layer_config(layer_name)
        return layer_config.get("enabled", False)


# Global configuration singleton
_nox_config: Optional[NOXConfig] = None


def get_nox_config() -> NOXConfig:
    """Get global NOX configuration instance."""
    global _nox_config
    if _nox_config is None:
        _nox_config = NOXConfig()
    return _nox_config


def is_nox_enabled() -> bool:
    """Fast check if NOX is enabled (<1ms)."""
    return get_nox_config().enabled


# ============================================================================
# Layer 1: Rule-Based Pre-Check
# ============================================================================

class Rule:
    """Validation rule."""
    
    def __init__(self, name: str, pattern: str, severity: Severity, message: str):
        self.name = name
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.severity = severity
        self.message = message
    
    def check(self, text: str) -> Optional[Dict[str, Any]]:
        """Check if rule matches text."""
        match = self.pattern.search(text)
        if match:
            return {
                "rule": self.name,
                "severity": self.severity.value,
                "message": self.message,
                "match": match.group(0)
            }
        return None


class RuleEngine:
    """Fast rule-based validation engine."""
    
    def __init__(self):
        self.rules: List[Rule] = []
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default validation rules."""
        # Logical consistency rules
        self.rules.append(Rule(
            name="contradiction",
            pattern=r"\\b(is|are|was|were)\\s+\\w+\\s+and\\s+(is|are|was|were)\\s+not\\s+\\w+",
            severity=Severity.HIGH,
            message="Contradictory statements detected"
        ))
        
        self.rules.append(Rule(
            name="circular_reasoning",
            pattern=r"\\bbecause\\s+.*\\s+therefore\\s+.*\\s+because",
            severity=Severity.MEDIUM,
            message="Circular reasoning detected"
        ))
        
        # Claim support rules
        self.rules.append(Rule(
            name="unsupported_certainty",
            pattern=r"\\b(definitely|certainly|surely|absolutely)\\b.*\\b(because|i think|maybe)\\b",
            severity=Severity.MEDIUM,
            message="Certainty expressed without strong support"
        ))
        
        self.rules.append(Rule(
            name="speculation_as_fact",
            pattern=r"\\b(i think|maybe|possibly|probably)\\b.*\\b(is|are|will)\\b",
            severity=Severity.LOW,
            message="Speculative language presented as fact"
        ))
        
        # Knowledge boundary rules
        self.rules.append(Rule(
            name="domain_overreach",
            pattern=r"\\b(i know everything|i am an expert in all)\\b",
            severity=Severity.HIGH,
            message="Potential domain overreach detected"
        ))
        
        self.rules.append(Rule(
            name="unrealistic_capability",
            pattern=r"\\b(i can predict the future|i know what will happen)\\b",
            severity=Severity.HIGH,
            message="Unrealistic capability claim detected"
        ))
    
    def add_custom_rule(self, rule: Rule):
        """Add a custom validation rule."""
        self.rules.append(rule)
    
    def validate(self, text: str, timeout_ms: float = 50.0) -> ValidationResult:
        """
        Validate text using rule engine.
        
        Args:
            text: Text to validate
            timeout_ms: Maximum execution time in milliseconds
        
        Returns:
            ValidationResult with issues found
        """
        start_time = time.time()
        issues = []
        
        for rule in self.rules:
            # Check timeout
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms > timeout_ms:
                break
            
            issue = rule.check(text)
            if issue:
                issues.append(issue)
        
        # Calculate score based on issues
        score = self._calculate_score(issues)
        
        return ValidationResult(
            passed=len(issues) == 0,
            score=score,
            issues=issues,
            metadata={
                "rules_checked": len(self.rules),
                "issues_found": len(issues)
            }
        )
    
    def _calculate_score(self, issues: List[Dict[str, Any]]) -> float:
        """Calculate validation score from issues."""
        if not issues:
            return 100.0
        
        # Deduct points based on severity
        severity_weights = {
            "low": 5,
            "medium": 15,
            "high": 30,
            "critical": 50
        }
        
        total_deduction = sum(
            severity_weights.get(issue.get("severity", "low"), 5)
            for issue in issues
        )
        
        score = max(0.0, 100.0 - total_deduction)
        return score


# ============================================================================
# Layer 2: Template-Based Structured Reasoning
# ============================================================================

class Template:
    """Reasoning template."""
    
    def __init__(self, name: str, description: str, mode: ValidationMode, steps: List[Dict[str, Any]]):
        self.name = name
        self.description = description
        self.mode = mode
        self.steps = steps
    
    def execute(self, text: str) -> List[Dict[str, Any]]:
        """Execute template on text."""
        results = []
        
        for step in self.steps:
            step_num = step.get("step", 0)
            instruction = step.get("instruction", "")
            output_type = step.get("output_type", "text")
            
            # In a real implementation, this would use LLM to execute the step
            # For now, we'll simulate the structure
            result = {
                "step": step_num,
                "instruction": instruction,
                "output_type": output_type,
                "text": text,  # In real implementation, this would be the LLM output
                "completed": True
            }
            results.append(result)
        
        return results


class TemplateEngine:
    """Template-based structured reasoning engine."""
    
    def __init__(self):
        self.templates: Dict[str, Template] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default reasoning templates."""
        # Basic CoT template
        self.templates["basic_cot"] = Template(
            name="basic_cot",
            description="Basic chain-of-thought reasoning",
            mode=ValidationMode.BALANCED,
            steps=[
                {
                    "step": 1,
                    "instruction": "Identify the core question or claim",
                    "output_type": "text"
                },
                {
                    "step": 2,
                    "instruction": "Break down into sub-questions",
                    "output_type": "list"
                },
                {
                    "step": 3,
                    "instruction": "Provide reasoning for each sub-question",
                    "output_type": "structured"
                },
                {
                    "step": 4,
                    "instruction": "Synthesize into final answer",
                    "output_type": "text"
                }
            ]
        )
        
        # Verification template
        self.templates["verification"] = Template(
            name="verification",
            description="Claim-evidence verification",
            mode=ValidationMode.STRICT,
            steps=[
                {
                    "step": 1,
                    "instruction": "Identify all claims made",
                    "output_type": "list"
                },
                {
                    "step": 2,
                    "instruction": "Map each claim to supporting evidence",
                    "output_type": "structured"
                },
                {
                    "step": 3,
                    "instruction": "Evaluate evidence quality",
                    "output_type": "structured"
                },
                {
                    "step": 4,
                    "instruction": "Identify unsupported claims",
                    "output_type": "list"
                }
            ]
        )
        
        # Self-reflection template
        self.templates["self_reflection"] = Template(
            name="self_reflection",
            description="Uncertainty acknowledgment and boundary declaration",
            mode=ValidationMode.PERMISSIVE,
            steps=[
                {
                    "step": 1,
                    "instruction": "Identify areas of uncertainty",
                    "output_type": "list"
                },
                {
                    "step": 2,
                    "instruction": "Declare knowledge boundaries",
                    "output_type": "text"
                },
                {
                    "step": 3,
                    "instruction": "Consider alternative perspectives",
                    "output_type": "list"
                }
            ]
        )
    
    def select_template(self, mode: ValidationMode) -> Optional[Template]:
        """Select appropriate template for mode."""
        # Select template based on mode
        if mode == ValidationMode.STRICT:
            return self.templates.get("verification")
        elif mode == ValidationMode.BALANCED:
            return self.templates.get("basic_cot")
        elif mode == ValidationMode.PERMISSIVE:
            return self.templates.get("self_reflection")
        return None
    
    def apply_template(self, text: str, mode: ValidationMode, timeout_ms: float = 30.0) -> ValidationResult:
        """
        Apply reasoning template to text.
        
        Args:
            text: Text to process
            mode: Validation mode
            timeout_ms: Maximum execution time in milliseconds
        
        Returns:
            ValidationResult with structured reasoning
        """
        start_time = time.time()
        
        template = self.select_template(mode)
        if not template:
            return ValidationResult(
                passed=True,
                score=100.0,
                issues=[],
                metadata={"error": "No template available for mode"}
            )
        
        # Execute template
        steps = template.execute(text)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(steps)
        
        # Check timeout
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > timeout_ms:
            return ValidationResult(
                passed=False,
                score=confidence,
                issues=[{
                    "type": "timeout",
                    "severity": "medium",
                    "message": f"Template execution exceeded timeout: {elapsed_ms:.2f}ms"
                }],
                metadata={
                    "template": template.name,
                    "steps_completed": len(steps),
                    "execution_time_ms": elapsed_ms
                }
            )
        
        return ValidationResult(
            passed=True,
            score=confidence,
            issues=[],
            metadata={
                "template": template.name,
                "structured_reasoning": steps,
                "confidence_factors": {
                    "evidence_quality": confidence,
                    "logical_consistency": confidence,
                    "source_reliability": confidence
                }
            }
        )
    
    def _calculate_confidence(self, steps: List[Dict[str, Any]]) -> float:
        """Calculate confidence score from template execution."""
        # In a real implementation, this would analyze the quality of reasoning
        # For now, return a reasonable default
        return 75.0


# ============================================================================
# Layer 3: Citation Verification
# ============================================================================

class CitationVerifier:
    """Citation verification and fact-checking engine."""
    
    def __init__(self):
        self.source_types = {
            "peer_reviewed": 100,
            "academic_journal": 90,
            "reputable_news": 80,
            "government": 85,
            "industry_report": 70,
            "blog_post": 40,
            "social_media": 20,
            "unknown": 0
        }
    
    def extract_citations(self, text: str) -> List[Dict[str, Any]]:
        """Extract citations from text."""
        citations = []
        
        # Common citation patterns
        patterns = [
            r"\\[(\\d+)\\]",  # [1], [2], etc.
            r"\\(([^)]+\\s+\\d{4})\\)",  # (Smith 2023)
            r"\\[([^]]+\\s+\\d{4})\\]",  # [Smith 2023]
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                citations.append({
                    "text": match.group(0),
                    "position": match.start(),
                    "type": self._detect_citation_type(match.group(0))
                })
        
        return citations
    
    def _detect_citation_type(self, citation_text: str) -> str:
        """Detect citation type."""
        if re.match(r"\\[\\d+\\]", citation_text):
            return "numeric"
        elif re.search(r"\\d{4}", citation_text):
            return "author_year"
        else:
            return "unknown"
    
    def validate_sources(self, citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate citation sources."""
        validated = []
        
        for citation in citations:
            # In a real implementation, this would check actual sources
            # For now, simulate validation
            validated.append({
                **citation,
                "valid": True,
                "reliability_score": 75.0,
                "accessible": True
            })
        
        return validated
    
    def detect_hallucinations(self, text: str, citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect potential hallucinations."""
        hallucinations = []
        
        # Check for claims without citations
        sentences = re.split(r"[.!?]+", text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 50:  # Only check substantive sentences
                has_citation = any(
                    citation["position"] >= text.find(sentence) and
                    citation["position"] <= text.find(sentence) + len(sentence)
                    for citation in citations
                )
                
                if not has_citation:
                    hallucinations.append({
                        "type": "unsupported_claim",
                        "severity": "medium",
                        "message": "Claim without citation",
                        "text": sentence
                    })
        
        return hallucinations
    
    def verify(self, text: str, timeout_ms: float = 20.0) -> ValidationResult:
        """
        Verify citations and detect hallucinations.
        
        Args:
            text: Text to verify
            timeout_ms: Maximum execution time in milliseconds
        
        Returns:
            ValidationResult with citation verification results
        """
        start_time = time.time()
        
        # Extract citations
        citations = self.extract_citations(text)
        
        # Validate sources
        validated = self.validate_sources(citations)
        
        # Detect hallucinations
        hallucinations = self.detect_hallucinations(text, citations)
        
        # Calculate score
        score = self._calculate_score(validated, hallucinations)
        
        # Check timeout
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > timeout_ms:
            return ValidationResult(
                passed=False,
                score=score,
                issues=[{
                    "type": "timeout",
                    "severity": "medium",
                    "message": f"Citation verification exceeded timeout: {elapsed_ms:.2f}ms"
                }],
                metadata={
                    "citations_found": len(citations),
                    "hallucinations_detected": len(hallucinations)
                }
            )
        
        # Combine issues
        issues = []
        for h in hallucinations:
            issues.append(h)
        
        return ValidationResult(
            passed=len(hallucinations) == 0,
            score=score,
            issues=issues,
            metadata={
                "citations_found": len(citations),
                "citations_validated": len(validated),
                "hallucinations_detected": len(hallucinations),
                "citation_quality": validated
            }
        )
    
    def _calculate_score(self, validated: List[Dict[str, Any]], hallucinations: List[Dict[str, Any]]) -> float:
        """Calculate verification score."""
        if not validated:
            return 50.0
        
        # Average reliability score
        avg_reliability = sum(
            v.get("reliability_score", 50)
            for v in validated
        ) / len(validated)
        
        # Deduct for hallucinations
        hallucination_penalty = len(hallucinations) * 20
        
        score = max(0.0, avg_reliability - hallucination_penalty)
        return score


# ============================================================================
# Result Aggregator
# ============================================================================

class ResultAggregator:
    """Aggregate results from all validation layers."""
    
    def __init__(self):
        self.layer_weights = {
            "pre_check": 0.4,
            "structured_reasoning": 0.4,
            "citation_verify": 0.2
        }
    
    def aggregate(self, layer_results: Dict[str, LayerResult], thresholds: Dict[str, float]) -> NOXResult:
        """
        Aggregate results from all layers.
        
        Args:
            layer_results: Results from each layer
            thresholds: Validation thresholds
        
        Returns:
            Complete NOX validation result
        """
        # Collect active layer results
        active_results = {
            name: result
            for name, result in layer_results.items()
            if result.enabled and result.result is not None
        }
        
        # Calculate weighted overall score
        overall_score = self._calculate_weighted_score(active_results)
        
        # Make pass/fail decision
        decision = self._make_decision(overall_score, active_results, thresholds)
        
        # Generate report
        report = self._generate_report(active_results, decision)
        
        # Calculate total time
        total_time = sum(
            result.execution_time_ms
            for result in layer_results.values()
        )
        
        return NOXResult(
            overall_score=overall_score,
            decision=decision,
            report=report,
            layer_results=layer_results,
            total_time_ms=total_time
        )
    
    def _calculate_weighted_score(self, active_results: Dict[str, LayerResult]) -> float:
        """Calculate weighted overall score."""
        if not active_results:
            return 100.0
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for layer_name, result in active_results.items():
            weight = self.layer_weights.get(layer_name, 0.33)
            score = result.result.score if result.result else 0.0
            
            weighted_sum += weight * score
            total_weight += weight
        
        if total_weight == 0:
            return 100.0
        
        return weighted_sum / total_weight
    
    def _make_decision(self, overall_score: float, active_results: Dict[str, LayerResult], thresholds: Dict[str, float]) -> str:
        """Make pass/fail decision."""
        # Check overall threshold
        overall_threshold = thresholds.get("overall_score", 70)
        if overall_score < overall_threshold:
            return "fail"
        
        # Check layer-specific thresholds
        for layer_name, result in active_results.items():
            if result.result:
                layer_threshold = thresholds.get(layer_name, 70)
                if result.result.score < layer_threshold:
                    return "fail"
        
        return "pass"
    
    def _generate_report(self, active_results: Dict[str, LayerResult], decision: str) -> Dict[str, Any]:
        """Generate human-readable report."""
        # Collect all issues
        all_issues = []
        for result in active_results.values():
            if result.result and result.result.issues:
                for issue in result.result.issues:
                    all_issues.append({
                        **issue,
                        "layer": result.layer_name
                    })
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 3))
        
        # Generate summary
        if decision == "fail":
            if all_issues:
                summary = f"Validation failed: {len(all_issues)} issue(s) detected"
            else:
                summary = "Validation failed: Score below threshold"
        else:
            summary = "Validation passed"
        
        return {
            "summary": summary,
            "issues": all_issues,
            "issues_by_severity": self._group_by_severity(all_issues)
        }
    
    def _group_by_severity(self, issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group issues by severity."""
        grouped = {}
        for issue in issues:
            severity = issue.get("severity", "low")
            if severity not in grouped:
                grouped[severity] = []
            grouped[severity].append(issue)
        return grouped


# ============================================================================
# Main Validation Function
# ============================================================================

def validate_text(
    text: str,
    mode: Optional[str] = None,
    layers: Optional[List[str]] = None
) -> NOXResult:
    """
    Validate text using NOX protocol.
    
    Args:
        text: Text to validate
        mode: Validation mode (strict, balanced, permissive). If None, uses config.
        layers: List of layers to enable. If None, uses config.
    
    Returns:
        Complete NOX validation result
    """
    start_time = time.time()
    
    # Fast path check - zero overhead when disabled
    if not is_nox_enabled():
        return NOXResult(
            overall_score=100.0,
            decision="pass",
            report={"summary": "NOX disabled - no validation performed"},
            layer_results={},
            total_time_ms=0.0
        )
    
    # Get configuration
    config = get_nox_config()
    validation_mode = ValidationMode(mode) if mode else config.get_mode()
    thresholds = config.get_thresholds()
    
    # Initialize layer engines
    rule_engine = RuleEngine()
    template_engine = TemplateEngine()
    citation_verifier = CitationVerifier()
    aggregator = ResultAggregator()
    
    # Determine which layers to run
    layer_names = ["pre_check", "structured_reasoning", "citation_verify"]
    if layers:
        layer_names = [name for name in layer_names if name in layers]
    
    # Run each layer
    layer_results = {}
    
    for layer_name in layer_names:
        layer_start = time.time()
        layer_config = config.get_layer_config(layer_name)
        layer_enabled = layer_config.get("enabled", False)
        timeout_ms = layer_config.get("timeout_ms", 50)
        
        if not layer_enabled:
            layer_results[layer_name] = LayerResult(
                layer_name=layer_name,
                enabled=False,
                execution_time_ms=0.0
            )
            continue
        
        try:
            if layer_name == "pre_check":
                result = rule_engine.validate(text, timeout_ms)
            elif layer_name == "structured_reasoning":
                result = template_engine.apply_template(text, validation_mode, timeout_ms)
            elif layer_name == "citation_verify":
                result = citation_verifier.verify(text, timeout_ms)
            else:
                result = None
            
            layer_time = (time.time() - layer_start) * 1000
            
            layer_results[layer_name] = LayerResult(
                layer_name=layer_name,
                enabled=True,
                execution_time_ms=layer_time,
                result=result
            )
        except Exception as e:
            layer_time = (time.time() - layer_start) * 1000
            layer_results[layer_name] = LayerResult(
                layer_name=layer_name,
                enabled=True,
                execution_time_ms=layer_time,
                error=str(e)
            )
    
    # Aggregate results
    nox_result = aggregator.aggregate(layer_results, thresholds)
    
    # Add total time
    nox_result.total_time_ms = (time.time() - start_time) * 1000
    
    return nox_result


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI interface for validation."""
    if len(sys.argv) < 2:
        print("Usage: validate.py <text>")
        sys.exit(1)
    
    text = " ".join(sys.argv[1:])
    
    result = validate_text(text)
    
    print(f"Decision: {result.decision}")
    print(f"Overall Score: {result.overall_score:.1f}")
    print(f"Total Time: {result.total_time_ms:.2f}ms")
    print(f"\\nReport: {result.report['summary']}")
    
    if result.report.get("issues"):
        print("\\nIssues:")
        for issue in result.report["issues"]:
            print(f"  - [{issue['severity'].upper()}] {issue['message']}")


if __name__ == "__main__":
    main()
