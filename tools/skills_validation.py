#!/usr/bin/env python3
"""Shared validation helpers for Hermes skills.

These checks are intentionally lightweight and compatible with the real SKILL.md
format used across the Hermes skills tree. They are suitable for fast local
validation loops and batch repo scans.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500
NAME_RE = re.compile(r"^[a-z0-9-]+$")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---(?:\s*\n|\s*$)", re.DOTALL)


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    message: str


def _normalize_content(content: str) -> str:
    return content.replace("\r\n", "\n").replace("\r", "\n")


def _extract_frontmatter(content: str) -> tuple[dict[str, Any], str] | tuple[None, str]:
    content = _normalize_content(content)
    if not content.strip():
        return None, "Content cannot be empty."
    if not content.startswith("---"):
        return None, "SKILL.md must start with YAML frontmatter (---)."

    match = FRONTMATTER_RE.match(content)
    if not match:
        return None, "SKILL.md frontmatter is missing or not closed with a second '---' line."

    frontmatter_text = match.group(1)
    body = content[match.end():].strip()

    try:
        parsed = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as exc:
        return None, f"YAML frontmatter parse error: {exc}"

    if not isinstance(parsed, dict):
        return None, "Frontmatter must be a YAML mapping (key: value pairs)."
    if not body:
        return None, "SKILL.md must have content after the frontmatter (instructions, procedures, etc.)."

    return parsed, body


def _validate_name(value: Any) -> str | None:
    if value is None:
        return "Frontmatter must include 'name' field."
    if not isinstance(value, str):
        return f"Name must be a string, got {type(value).__name__}."

    name = value.strip()
    if not name:
        return "Name cannot be empty."
    if len(name) > MAX_NAME_LENGTH:
        return f"Name exceeds {MAX_NAME_LENGTH} characters."
    if not NAME_RE.match(name):
        return f"Name '{name}' should be kebab-case (lowercase letters, digits, and hyphens only)."
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens."
    return None


def _validate_description(value: Any) -> str | None:
    if value is None:
        return "Frontmatter must include 'description' field."
    if not isinstance(value, str):
        return f"Description must be a string, got {type(value).__name__}."

    description = value.strip()
    if not description:
        return "Description cannot be empty."
    if len(description) > MAX_DESCRIPTION_LENGTH:
        return f"Description exceeds {MAX_DESCRIPTION_LENGTH} characters."
    return None


def _validate_optional_string(frontmatter: dict[str, Any], key: str, max_len: int) -> str | None:
    value = frontmatter.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        return f"{key} must be a string, got {type(value).__name__}."
    if len(value) > max_len:
        return f"{key} exceeds {max_len} characters."
    return None


def _validate_string_list(frontmatter: dict[str, Any], key: str) -> str | None:
    value = frontmatter.get(key)
    if value is None:
        return None
    if not isinstance(value, list):
        return f"{key} must be a list, got {type(value).__name__}."
    for item in value:
        if not isinstance(item, str) or not item.strip():
            return f"{key} must contain only non-empty strings."
    return None


def _validate_prerequisites(frontmatter: dict[str, Any]) -> str | None:
    prerequisites = frontmatter.get("prerequisites")
    if prerequisites is None:
        return None
    if not isinstance(prerequisites, dict):
        return f"prerequisites must be a mapping, got {type(prerequisites).__name__}."
    for key in ("env_vars", "commands"):
        value = prerequisites.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            continue
        if not isinstance(value, list):
            return f"prerequisites.{key} must be a string or list of strings."
        for item in value:
            if not isinstance(item, str) or not item.strip():
                return f"prerequisites.{key} must contain only non-empty strings."
    return None


def _validate_required_environment_variables(frontmatter: dict[str, Any]) -> str | None:
    value = frontmatter.get("required_environment_variables")
    if value is None:
        return None
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        return "required_environment_variables must be a list or mapping."
    for item in value:
        if isinstance(item, str):
            if not item.strip():
                return "required_environment_variables cannot contain empty strings."
            continue
        if not isinstance(item, dict):
            return "required_environment_variables entries must be strings or mappings."
        name = item.get("name") or item.get("env_var")
        if not isinstance(name, str) or not name.strip():
            return "required_environment_variables mapping entries must include a non-empty 'name' or 'env_var'."
    return None


def _validate_setup(frontmatter: dict[str, Any]) -> str | None:
    setup = frontmatter.get("setup")
    if setup is None:
        return None
    if not isinstance(setup, dict):
        return f"setup must be a mapping, got {type(setup).__name__}."
    collect_secrets = setup.get("collect_secrets")
    if collect_secrets is None:
        return None
    if isinstance(collect_secrets, dict):
        collect_secrets = [collect_secrets]
    if not isinstance(collect_secrets, list):
        return "setup.collect_secrets must be a list or mapping."
    for item in collect_secrets:
        if not isinstance(item, dict):
            return "setup.collect_secrets entries must be mappings."
        env_var = item.get("env_var")
        if not isinstance(env_var, str) or not env_var.strip():
            return "setup.collect_secrets entries must include a non-empty 'env_var'."
    return None


def _validate_credential_files(frontmatter: dict[str, Any]) -> str | None:
    value = frontmatter.get("credential_files")
    if value is None:
        return None
    if not isinstance(value, list):
        return f"credential_files must be a list, got {type(value).__name__}."
    for item in value:
        if not isinstance(item, dict):
            return "credential_files entries must be mappings."
        path_value = item.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            return "credential_files entries must include a non-empty 'path'."
    return None


def validate_skill_content(content: str) -> ValidationResult:
    parsed, error = _extract_frontmatter(content)
    if parsed is None:
        return ValidationResult(False, error)

    for validator in (
        lambda fm: _validate_name(fm.get("name")),
        lambda fm: _validate_description(fm.get("description")),
        lambda fm: _validate_optional_string(fm, "compatibility", MAX_COMPATIBILITY_LENGTH),
        lambda fm: _validate_optional_string(fm, "version", 128),
        lambda fm: _validate_optional_string(fm, "author", 256),
        lambda fm: _validate_optional_string(fm, "license", 128),
        lambda fm: _validate_string_list(fm, "platforms"),
        lambda fm: _validate_string_list(fm, "allowed-tools"),
        lambda fm: None if fm.get("metadata") is None or isinstance(fm.get("metadata"), dict) else f"metadata must be a mapping, got {type(fm.get('metadata')).__name__}.",
        _validate_prerequisites,
        _validate_required_environment_variables,
        _validate_setup,
        _validate_credential_files,
    ):
        error = validator(parsed)
        if error:
            return ValidationResult(False, error)

    return ValidationResult(True, "Skill is valid!")


def validate_skill_dir(skill_dir: str | Path) -> ValidationResult:
    path = Path(skill_dir).expanduser()
    if not path.exists():
        return ValidationResult(False, f"Skill directory not found: {path}")
    if not path.is_dir():
        return ValidationResult(False, f"Path is not a directory: {path}")

    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        return ValidationResult(False, "SKILL.md not found")

    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception as exc:
        return ValidationResult(False, f"Could not read SKILL.md: {exc}")

    return validate_skill_content(content)


def find_skill_dirs(skills_root: str | Path) -> list[Path]:
    root = Path(skills_root).expanduser()
    if not root.exists():
        raise FileNotFoundError(f"Skills root not found: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Skills root is not a directory: {root}")
    return sorted({path.parent for path in root.rglob("SKILL.md")})
