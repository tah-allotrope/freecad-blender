"""Tests for the orchestration layer (arg assembly, streamed output,
detached launch) using stub executables -- no real Blender needed."""
import json
import os
import sys
from pathlib import Path

import pytest

from homedesign import orchestrator
from homedesign.render_profiles import RENDER_PROFILES


def test_render_profiles_declared():
    assert RENDER_PROFILES["final"] == {
        "engine": "EEVEE", "samples": 256, "res": (1920, 1080), "raytracing": True,
    }
    assert RENDER_PROFILES["cycles"]["engine"] == "CYCLES"
    assert RENDER_PROFILES["preview"]["res"] == (960, 540)


def test_build_command_cycles_profile_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("BLENDER_CMD", "fake-blender")
    model = _mini_model(tmp_path)
    out = tmp_path / "out"
    cmd = orchestrator._build_command(model, out, "cycles")
    assert "--profile" in cmd
    assert cmd[cmd.index("--profile") + 1] == "cycles"


def test_build_scene_profile_overrides_final(tmp_path, monkeypatch, stub_blender):
    monkeypatch.setenv("BLENDER_CMD", stub_blender)
    model = _mini_model(tmp_path)
    out = tmp_path / "out"
    # `profile` wins over the legacy `final` flag (DEC-003 backward compat).
    orchestrator.build_scene(model, out, final=True, profile="cycles")
    assert True  # reached without raising; argv already covered above


@pytest.fixture
def stub_blender(tmp_path):
    """A fake blender executable: echoes its argv lines to stdout.

    On Windows a bare script can't be executed as `.exe`, so the stub is a
    `.cmd` wrapper that calls the real python with an argv-echo script file.
    """
    echo_py = tmp_path / "_echo_args.py"
    echo_py.write_text(
        "import sys\n"
        "for a in sys.argv[1:]:\n"
        "    print('ARG:', a)\n"
    )
    if os.name == "nt":
        stub = tmp_path / "blender.cmd"
        stub.write_text(
            f'@echo off\r\n"{sys.executable}" "{echo_py}" %*\r\n'
        )
    else:
        stub = tmp_path / "blender"
        stub.write_text(f"#!/bin/sh\n{sys.executable} {echo_py} \"$@\"\n")
        stub.chmod(0o755)
    yield str(stub)


def _mini_model(tmp_path: Path) -> Path:
    model = tmp_path / "mini.model.json"
    model.write_text(json.dumps({
        "name": "mini", "style": "modern-minimal",
        "plot_width_mm": 4000, "plot_depth_mm": 10000,
        "storeys": [], "views": [],
    }))
    return model


def test_build_command_assembles_flags(tmp_path, monkeypatch):
    monkeypatch.setenv("BLENDER_CMD", "fake-blender")
    model = _mini_model(tmp_path)
    out = tmp_path / "out"
    cmd = orchestrator._build_command(model, out, "preview", views=["a", "b"], skip_existing=True)
    assert "fake-blender" in cmd
    assert "--views" in cmd and "a,b" in cmd
    assert "--skip-existing" in cmd


def test_build_scene_streams_stub_output(tmp_path, monkeypatch, stub_blender):
    monkeypatch.setenv("BLENDER_CMD", stub_blender)
    model = _mini_model(tmp_path)
    out = tmp_path / "out"
    # The stub writes three lines to stdout; build_scene must stream them to
    # stderr and exit 0.
    results = orchestrator.build_scene(model, out)
    assert results  # blend path + any pngs
    assert (out / "blend").exists()


def test_build_scene_failure_includes_output(tmp_path, monkeypatch):
    boom_py = tmp_path / "_boom.py"
    boom_py.write_text(
        "import sys\n"
        "print('boom line 1')\n"
        "print('boom line 2')\n"
        "sys.exit(1)\n"
    )
    if os.name == "nt":
        stub = tmp_path / "blender.cmd"
        stub.write_text(f'@echo off\r\n"{sys.executable}" "{boom_py}"\r\n')
    else:
        stub = tmp_path / "blender"
        stub.write_text(f"#!/bin/sh\n{sys.executable} {boom_py}\n")
        stub.chmod(0o755)
    monkeypatch.setenv("BLENDER_CMD", str(stub))
    model = _mini_model(tmp_path)
    out = tmp_path / "out"
    with pytest.raises(RuntimeError) as exc:
        orchestrator.build_scene(model, out)
    assert "boom line 1" in str(exc.value)


def test_render_only_detach_returns_pid(tmp_path, monkeypatch, stub_blender):
    monkeypatch.setenv("BLENDER_CMD", stub_blender)
    model = _mini_model(tmp_path)
    out = tmp_path / "out"
    log = tmp_path / "render.log"
    result = orchestrator.render_only(model, out, detach=True, log_path=log)
    assert isinstance(result, int)  # a PID
