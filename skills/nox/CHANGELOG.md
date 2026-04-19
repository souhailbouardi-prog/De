# NOX Changelog

All notable changes to NOX will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Custom rule editor
- Template marketplace
- Performance dashboard
- Integration with more agent frameworks

---

## [1.0.0] - 2025-04-19

### Added
- Initial release of NOX reasoning protocol
- Layer 1: Fast rule-based pre-check
- Layer 2: Template-based structured reasoning
- Layer 3: Citation verification and fact-checking
- Three validation modes: strict, balanced, permissive
- Zero-overhead design when disabled
- YAML-based configuration
- Confidence scoring system (0-100)
- Human-readable validation reports
- Toggle CLI for enable/disable operations
- Validation CLI for text validation
- Comprehensive documentation (SKILL.md, SPEC.md, README.md)
- Installation script (install.sh)
- Performance monitoring and timeout enforcement
- Cross-platform support (Linux, macOS, Windows)

### Performance
- Disabled mode: <1ms overhead
- Layer 1 only: 20-40ms
- Layers 1-2: 50-80ms
- All layers: 70-100ms

### Documentation
- SKILL.md: Complete skill instructions
- SPEC.md: Technical specification
- README.md: User documentation
- CHANGELOG.md: Version history
- Inline code documentation

### Security
- No external network requests
- Local processing only
- Input validation and sanitization
- Timeout enforcement
- Graceful error handling

---

## [0.1.0] - 2025-04-18

### Added
- Initial design and architecture
- Proof of concept implementation
- Basic rule engine
- Basic template engine
- Basic citation verifier

---

## Future Versions

### [1.1.0] - Planned
- Custom rule editor
- Template marketplace
- Performance dashboard
- Integration with more agent frameworks

### [1.2.0] - Planned
- Machine learning-based validation
- Adaptive thresholds
- Real-time validation
- Multi-language support

### [2.0.0] - Planned
- Distributed validation
- Cloud-based verification
- Advanced citation analysis
- Plugin system

---

## Version Summary

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| 2.0.0 | TBD | Planned | Major features |
| 1.2.0 | TBD | Planned | ML validation |
| 1.1.0 | TBD | Planned | Enhanced features |
| 1.0.0 | 2025-04-19 | Stable | Initial release |
| 0.1.0 | 2025-04-18 | Beta | Proof of concept |

---

## Upgrade Guide

### From 0.1.0 to 1.0.0

No breaking changes. Simply upgrade to 1.0.0:

```bash
# Backup your configuration
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.backup

# Install new version
cd ~/.hermes/skills/nox
./install.sh

# Restore your configuration if needed
cp ~/.hermes/config.yaml.backup ~/.hermes/config.yaml
```

### From 1.0.0 to 1.1.0 (when released)

No breaking changes expected. Upgrade instructions will be provided in the release notes.

---

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/NousResearch/hermes-agent/issues
- Discord: https://discord.gg/NousResearch
- Documentation: See README.md and SPEC.md

---

## License

MIT License - See LICENSE file for details
