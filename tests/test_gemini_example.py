from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _flag_enabled() -> bool:
    value = os.environ.get("ACP_ENABLE_GEMINI_TESTS", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _resolve_gemini_binary() -> str | None:
    override = os.environ.get("ACP_GEMINI_BIN")
    if override:
        return override
    return shutil.which("gemini")


GEMINI_BIN = _resolve_gemini_binary()
pytestmark = pytest.mark.skipif(
    not (_flag_enabled() and GEMINI_BIN),
    reason="Gemini tests disabled. Set ACP_ENABLE_GEMINI_TESTS=1 and provide the gemini CLI.",
)


def test_gemini_example_smoke() -> None:
    env = os.environ.copy()
    src_path = str(Path(__file__).resolve().parent.parent / "src")
    python_path = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src_path if not python_path else os.pathsep.join([src_path, python_path])

    extra_args = shlex.split(env.get("ACP_GEMINI_TEST_ARGS", ""))
    cmd = [
        sys.executable,
        str(Path("examples/gemini.py").resolve()),
        "--gemini",
        GEMINI_BIN or "gemini",
        "--yolo",
        *extra_args,
    ]

    proc = subprocess.Popen(  # noqa: S603 - command is built from trusted inputs
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )

    assert proc.stdin is not None
    assert proc.stdout is not None

    try:
        stdout, stderr = proc.communicate(":exit\n", timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        pytest.fail(_format_failure("Gemini example timed out", stdout, stderr), pytrace=False)

    combined = f"{stdout}\n{stderr}"
    if proc.returncode != 0:
        auth_errors = (
            "Authentication failed",
            "Authentication required",
            "GOOGLE_CLOUD_PROJECT",
        )
        if any(token in combined for token in auth_errors):
            pytest.skip(f"Gemini CLI authentication required:\n{combined}")
        pytest.fail(
            _format_failure(f"Gemini example exited with {proc.returncode}", stdout, stderr),
            pytrace=False,
        )

    assert "Connected to Gemini" in combined or "✅ Connected to Gemini" in combined


def _format_failure(prefix: str, stdout: str, stderr: str) -> str:
    return f"{prefix}.\nstdout:\n{stdout}\nstderr:\n{stderr}"
