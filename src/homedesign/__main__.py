"""CLI: python -m homedesign <compile|plans|build> <spec.json> [--final] [--floor N]"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .compiler import compile_spec
from .errors import SpecValidationError
from .validate import validate_compiled, validate_schema
from . import plan2d

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_spec(spec_path: Path) -> dict:
    return json.loads(spec_path.read_text())


def _validate_and_compile(spec_path: Path):
    spec = _load_spec(spec_path)
    schema_errors = validate_schema(spec)
    if schema_errors:
        return None, schema_errors
    try:
        model = compile_spec(spec)
    except SpecValidationError as e:
        return None, e.errors
    geo_errors = validate_compiled(model)
    if geo_errors:
        return None, geo_errors
    return model, []


def _print_errors(errors) -> None:
    for e in errors:
        print(f"[{e.code}] {e.path}: {e.message}", file=sys.stderr)


def cmd_compile(args) -> int:
    spec_path = Path(args.spec)
    model, errors = _validate_and_compile(spec_path)
    if errors:
        _print_errors(errors)
        return 1
    out_dir = REPO_ROOT / "output" / "compiled"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{model.name}.model.json"
    out_path.write_text(json.dumps(model.to_dict(), indent=2))
    print(str(out_path))
    return 0


def cmd_plans(args) -> int:
    spec_path = Path(args.spec)
    model, errors = _validate_and_compile(spec_path)
    if errors:
        _print_errors(errors)
        return 1
    paths = plan2d.write_plans(model, REPO_ROOT / "output")
    for p in paths:
        print(str(p))
    return 0


def cmd_build(args) -> int:
    from . import orchestrator

    spec_path = Path(args.spec)
    model, errors = _validate_and_compile(spec_path)
    if errors:
        _print_errors(errors)
        return 1
    out_dir = REPO_ROOT / "output"
    plan_paths = plan2d.write_plans(model, out_dir)
    for p in plan_paths:
        print(str(p))

    model_path = out_dir / "compiled" / f"{model.name}.model.json"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps(model.to_dict(), indent=2))

    t0 = time.time()
    result = orchestrator.build_scene(model_path, out_dir, final=args.final)
    elapsed = time.time() - t0
    print(f"blender build: {elapsed:.1f}s")
    for p in result:
        print(str(p))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="homedesign")
    sub = parser.add_subparsers(dest="command", required=True)

    p_compile = sub.add_parser("compile", help="validate + compile a spec to a model JSON")
    p_compile.add_argument("spec")
    p_compile.set_defaults(func=cmd_compile)

    p_plans = sub.add_parser("plans", help="generate 2D SVG/DXF plans")
    p_plans.add_argument("spec")
    p_plans.set_defaults(func=cmd_plans)

    p_build = sub.add_parser("build", help="full build: plans + Blender scene + render")
    p_build.add_argument("spec")
    p_build.add_argument("--final", action="store_true", help="full-quality render instead of preview")
    p_build.add_argument("--floor", type=int, default=None)
    p_build.set_defaults(func=cmd_build)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
