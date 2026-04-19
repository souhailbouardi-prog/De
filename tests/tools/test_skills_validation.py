import json
import subprocess
import sys
from pathlib import Path

from tools.skills_validation import find_skill_dirs, validate_skill_content, validate_skill_dir


VALID_SKILL = """---
name: my-skill
description: A test skill
version: 1.0.0
platforms: [macos, linux]
prerequisites:
  env_vars: [API_KEY]
required_environment_variables:
  - name: API_KEY
    prompt: Enter API key
setup:
  collect_secrets:
    - env_var: API_KEY
      prompt: Enter API key
credential_files:
  - path: token.json
    description: auth token
metadata:
  hermes:
    tags: [test]
---

# My Skill

Do the thing.
"""


def test_validate_skill_content_accepts_realistic_skill_schema():
    result = validate_skill_content(VALID_SKILL)
    assert result.valid is True
    assert result.message == "Skill is valid!"


def test_validate_skill_content_rejects_missing_frontmatter():
    result = validate_skill_content("# No frontmatter")
    assert result.valid is False
    assert "frontmatter" in result.message.lower()


def test_validate_skill_content_rejects_empty_body():
    result = validate_skill_content("---\nname: my-skill\ndescription: Test\n---\n")
    assert result.valid is False
    assert "content after the frontmatter" in result.message


def test_validate_skill_content_rejects_bad_name():
    result = validate_skill_content("---\nname: My Skill\ndescription: Test\n---\n\nBody")
    assert result.valid is False
    assert "kebab-case" in result.message


def test_validate_skill_content_rejects_invalid_required_env_shape():
    bad = """---
name: my-skill
description: Test
required_environment_variables:
  - 123
---

Body
"""
    result = validate_skill_content(bad)
    assert result.valid is False
    assert "required_environment_variables" in result.message


def test_validate_skill_dir_reads_skill_md(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(VALID_SKILL, encoding="utf-8")

    result = validate_skill_dir(skill_dir)
    assert result.valid is True


def test_validate_skill_dir_missing_file(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()

    result = validate_skill_dir(skill_dir)
    assert result.valid is False
    assert result.message == "SKILL.md not found"


def test_find_skill_dirs_recursively(tmp_path):
    first = tmp_path / "category-a" / "skill-one"
    second = tmp_path / "category-b" / "skill-two"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    (first / "SKILL.md").write_text(VALID_SKILL, encoding="utf-8")
    (second / "SKILL.md").write_text(VALID_SKILL.replace("my-skill", "skill-two", 1), encoding="utf-8")

    found = find_skill_dirs(tmp_path)
    assert found == [first, second]


def test_find_skill_dirs_requires_existing_directory(tmp_path):
    missing = tmp_path / "missing"
    try:
        find_skill_dirs(missing)
    except FileNotFoundError as exc:
        assert str(missing) in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError")


def test_quick_validate_json_output(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(VALID_SKILL, encoding="utf-8")

    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "scripts/quick_validate.py", str(skill_dir), "--json"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
    assert payload["path"] == str(skill_dir)


def test_validate_all_skills_json_output(tmp_path):
    skill_dir = tmp_path / "category" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(VALID_SKILL, encoding="utf-8")

    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "scripts/validate_all_skills.py", str(tmp_path), "--json"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
    assert payload["summary"]["total"] == 1
    assert payload["results"][0]["path"] == "category/my-skill"
