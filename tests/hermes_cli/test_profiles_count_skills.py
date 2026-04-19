"""Regression tests for _count_skills directory filtering in profiles.py.

Ensures .git and .hub directories are excluded from skill counts regardless
of the OS path separator (fixes Windows where str(Path) uses backslashes).
"""

from pathlib import Path

from hermes_cli.profiles import _count_skills


class TestCountSkillsFiltering:
    """Verify that _count_skills excludes .git and .hub directories."""

    def test_excludes_git_directory_skills(self, tmp_path):
        """SKILL.md inside .git must not be counted."""
        skills_dir = tmp_path / "skills"
        (skills_dir / ".git" / "hooks").mkdir(parents=True)
        (skills_dir / ".git" / "hooks" / "SKILL.md").write_text("# Fake")
        # _count_skills expects the profile dir, it adds /skills internally
        assert _count_skills(tmp_path) == 0

    def test_excludes_hub_directory_skills(self, tmp_path):
        """SKILL.md inside .hub must not be counted."""
        skills_dir = tmp_path / "skills"
        (skills_dir / ".hub" / "cache").mkdir(parents=True)
        (skills_dir / ".hub" / "cache" / "SKILL.md").write_text("# Fake")
        assert _count_skills(tmp_path) == 0

    def test_counts_legitimate_skills(self, tmp_path):
        """Normal skills must be counted correctly."""
        skills_dir = tmp_path / "skills"
        (skills_dir / "my-skill").mkdir(parents=True)
        (skills_dir / "my-skill" / "SKILL.md").write_text("# Real Skill")
        assert _count_skills(tmp_path) == 1

    def test_counts_nested_legitimate_skills(self, tmp_path):
        """Skills in category subdirectories must be counted."""
        skills_dir = tmp_path / "skills"
        (skills_dir / "category" / "skill-a").mkdir(parents=True)
        (skills_dir / "category" / "skill-a" / "SKILL.md").write_text("# A")
        (skills_dir / "category" / "skill-b").mkdir(parents=True)
        (skills_dir / "category" / "skill-b" / "SKILL.md").write_text("# B")
        assert _count_skills(tmp_path) == 2

    def test_mixed_excluded_and_legitimate(self, tmp_path):
        """Excluded dirs filtered, legitimate skills kept."""
        skills_dir = tmp_path / "skills"
        (skills_dir / ".git" / "hooks").mkdir(parents=True)
        (skills_dir / ".git" / "hooks" / "SKILL.md").write_text("# Fake git")
        (skills_dir / ".hub" / "data").mkdir(parents=True)
        (skills_dir / ".hub" / "data" / "SKILL.md").write_text("# Fake hub")
        (skills_dir / "real-skill").mkdir(parents=True)
        (skills_dir / "real-skill" / "SKILL.md").write_text("# Real")
        assert _count_skills(tmp_path) == 1

    def test_no_skills_dir(self, tmp_path):
        """Profile without a skills directory returns 0."""
        assert _count_skills(tmp_path) == 0

    def test_git_in_name_not_excluded(self, tmp_path):
        """Skills with 'git' in their name must NOT be excluded."""
        skills_dir = tmp_path / "skills"
        (skills_dir / "git-workflow").mkdir(parents=True)
        (skills_dir / "git-workflow" / "SKILL.md").write_text("# Git Workflow")
        assert _count_skills(tmp_path) == 1
