from pathlib import Path
import tomllib


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_faster_whisper_is_not_a_base_dependency():
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    deps = data["project"]["dependencies"]

    assert not any(dep.startswith("faster-whisper") for dep in deps)

    voice_extra = data["project"]["optional-dependencies"]["voice"]
    assert any(dep.startswith("faster-whisper") for dep in voice_extra)


def test_manifest_includes_bundled_skills():
    manifest = (REPO_ROOT / "MANIFEST.in").read_text(encoding="utf-8")

    assert "graft skills" in manifest
    assert "graft optional-skills" in manifest


def test_all_extra_gates_voice_off_arm32():
    """The [all] profile must exclude voice on 32-bit ARM hosts.

    faster-whisper's transitive deps (ctranslate2, onnxruntime) ship no
    prebuilt wheels for armv6l / armv7l. Building from source OOMs or
    fills tmpfs on 1GB-RAM devices like Raspberry Pi 3B / 2 / Zero, so
    `pip install -e .[all]` hangs indefinitely for those users. Voice
    must carry a platform_machine marker in [all]; users who still need
    it on ARM32 can install the voice extra explicitly.

    This mirrors the existing `termux` extras' rationale and the
    `sys_platform == 'linux'` marker already used for [matrix].
    """
    from packaging.requirements import Requirement

    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    all_extras = data["project"]["optional-dependencies"]["all"]

    # Unconditional voice entry would hang ARM32 installs — must not appear.
    assert "hermes-agent[voice]" not in all_extras, (
        "hermes-agent[voice] must not appear in [all] without a platform marker; "
        "the raw entry hangs pip install on 32-bit ARM hosts where "
        "ctranslate2 / onnxruntime have no prebuilt wheels."
    )

    voice_entries = [e for e in all_extras if e.startswith("hermes-agent[voice]")]
    assert len(voice_entries) == 1, (
        f"expected exactly one voice entry in [all], got {voice_entries}"
    )

    req = Requirement(voice_entries[0])
    assert req.marker is not None, (
        f"voice entry in [all] must carry a platform marker: {voice_entries[0]}"
    )

    # ARM32 hosts: voice must be excluded from [all]
    for machine in ("armv6l", "armv7l"):
        assert req.marker.evaluate({"platform_machine": machine}) is False, (
            f"voice must be excluded from [all] on {machine}"
        )

    # All other architectures: voice stays in [all]
    for machine in ("arm64", "aarch64", "x86_64", "i686", "ppc64le", "s390x"):
        assert req.marker.evaluate({"platform_machine": machine}) is True, (
            f"voice must remain in [all] on {machine}"
        )

    # The voice extra itself must still exist so users can install it manually.
    voice_extra = data["project"]["optional-dependencies"]["voice"]
    assert any(dep.startswith("faster-whisper") for dep in voice_extra), (
        "the voice extra definition must still contain faster-whisper so that "
        "`pip install -e '.[voice]'` remains a valid manual install path on ARM32"
    )
