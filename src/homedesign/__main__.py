"""CLI: python -m homedesign <compile|plans|build> <spec.json> [--final] [--floor N]"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .compiler import compile_spec
from .errors import SpecValidationError
from .model import model_hash
from .validate import validate_compiled, validate_schema
from . import plan2d

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _write_model_json(model, out_dir: Path) -> Path:
    """Persist the compiled model with its provenance hash stamped in."""
    out = out_dir / "compiled"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{model.name}.model.json"
    data = model.to_dict()
    data["model_hash"] = model_hash(model)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def _load_spec(spec_path: Path) -> dict:
    return json.loads(spec_path.read_text(encoding="utf-8"))


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
    if any(e.severity != "warning" for e in geo_errors):
        return None, geo_errors
    return model, geo_errors


def _split_errors(errors):
    errors_out = [e for e in errors if e.severity != "warning"]
    warnings = [e for e in errors if e.severity == "warning"]
    return errors_out, warnings


def _print_errors(errors, json_out: bool = False) -> int:
    errors_out, warnings = _split_errors(errors)
    if json_out:
        print(json.dumps({"errors": [e.to_dict() for e in errors_out],
                          "warnings": [e.to_dict() for e in warnings]}))
    else:
        for e in errors_out:
            print(f"[{e.code}] {e.path}: {e.message}", file=sys.stderr)
        for e in warnings:
            print(f"warning: [{e.code}] {e.path}: {e.message}", file=sys.stderr)
    return 1 if errors_out else 0


def _handle_errors(errors, args) -> int | None:
    """Print errors/warnings and return the exit code, or None when no
    error-severity item exists (warnings alone must not block the build)."""
    errors_out, _ = _split_errors(errors)
    if not errors:
        return None
    _print_errors(errors, json_out=args.json)
    return 1 if errors_out else None


def cmd_compile(args) -> int:
    spec_path = Path(args.spec)
    model, errors = _validate_and_compile(spec_path)
    code = _handle_errors(errors, args)
    if code is not None:
        return code
    out_dir = REPO_ROOT / "output" / "compiled"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = _write_model_json(model, REPO_ROOT / "output")
    if not args.json:
        print(str(out_path))
    return 0


def cmd_plans(args) -> int:
    spec_path = Path(args.spec)
    model, errors = _validate_and_compile(spec_path)
    code = _handle_errors(errors, args)
    if code is not None:
        return code
    paths = plan2d.write_plans(model, REPO_ROOT / "output")
    if not args.json:
        for p in paths:
            print(str(p))
    return 0


def cmd_build(args) -> int:
    from . import orchestrator

    spec_path = Path(args.spec)
    model, errors = _validate_and_compile(spec_path)
    code = _handle_errors(errors, args)
    if code is not None:
        return code
    out_dir = REPO_ROOT / "output"
    plan_paths = plan2d.write_plans(model, out_dir)
    if not args.json:
        for p in plan_paths:
            print(str(p))

    model_path = _write_model_json(model, out_dir)

    t0 = time.time()
    result = orchestrator.build_scene(model_path, out_dir, final=args.final, profile=args.profile, gltf=args.gltf)
    elapsed = time.time() - t0
    print(f"blender build: {elapsed:.1f}s")
    for p in result:
        print(str(p))
    return 0


def cmd_pdf(args) -> int:
    from . import pdf as pdf_mod

    spec_path = Path(args.spec)
    model, errors = _validate_and_compile(spec_path)
    code = _handle_errors(errors, args)
    if code is not None:
        return code
    out_dir = REPO_ROOT / "output"

    svg_dir = out_dir / "svg"
    needs_drawings = not all((svg_dir / f"{model.name}_f{s.level}.svg").exists() for s in model.storeys)
    if not needs_drawings:
        needs_drawings = not (svg_dir / f"{model.name}_elev_north.svg").exists() \
            or not (svg_dir / f"{model.name}_section_x.svg").exists()
    if needs_drawings:
        plan2d.write_plans(model, out_dir)

    brief_path = Path(args.brief) if args.brief else REPO_ROOT / "spec" / "briefs" / f"{model.name}.json"
    if not brief_path.exists():
        print(f"brief copy not found: {brief_path}", file=sys.stderr)
        return 1
    brief = json.loads(brief_path.read_text(encoding="utf-8"))

    pdf_path = pdf_mod.build_brief(model, brief, out_dir, spec_path, hero_view=args.hero,
                                   embed_images=args.embed_images, require_fresh=args.require_fresh)
    if not args.json:
        print(str(pdf_path))
    return 0


def cmd_render(args) -> int:
    from . import orchestrator

    spec_path = Path(args.spec)
    model, errors = _validate_and_compile(spec_path)
    code = _handle_errors(errors, args)
    if code is not None:
        return code
    out_dir = REPO_ROOT / "output"

    model_path = _write_model_json(model, out_dir)

    views = args.views or None
    if args.detach:
        pid = orchestrator.render_only(
            model_path, out_dir, profile=args.profile, views=views,
            skip_existing=args.skip_existing, detach=True,
        )
        print(f"render launched (pid {pid})")
        return 0
    pngs = orchestrator.render_only(
        model_path, out_dir, profile=args.profile, views=views,
        skip_existing=args.skip_existing, detach=False,
    )
    for p in pngs:
        print(str(p))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="homedesign")
    sub = parser.add_subparsers(dest="command", required=True)

    json_parent = argparse.ArgumentParser(add_help=False)
    json_parent.add_argument(
        "--json", action="store_true",
        help="emit errors/warnings as JSON on stdout instead of human text",
    )

    p_compile = sub.add_parser("compile", parents=[json_parent], help="validate + compile a spec to a model JSON")
    p_compile.add_argument("spec")
    p_compile.set_defaults(func=cmd_compile)

    p_plans = sub.add_parser("plans", parents=[json_parent], help="generate 2D SVG/DXF plans")
    p_plans.add_argument("spec")
    p_plans.set_defaults(func=cmd_plans)

    p_build = sub.add_parser("build", parents=[json_parent], help="full build: plans + Blender scene + render")
    p_build.add_argument("spec")
    p_build.add_argument("--final", action="store_true", help="full-quality render instead of preview")
    p_build.add_argument("--profile", default=None, choices=["preview", "final", "cycles"],
                         help="render profile; overrides --final")
    p_build.add_argument("--gltf", action="store_true",
                         help="also export a GLB and a self-contained web viewer")
    p_build.add_argument("--floor", type=int, default=None)
    p_build.set_defaults(func=cmd_build)

    p_render = sub.add_parser("render", parents=[json_parent], help="render views of an already-built model (reuses the .blend)")
    p_render.add_argument("spec")
    p_render.add_argument("--view", dest="views", action="append", default=None,
                          help="view name to render (repeatable; default all)")
    p_render.add_argument("--profile", default="preview", choices=["preview", "final", "cycles"])
    p_render.add_argument("--skip-existing", action="store_true", help="skip views whose PNG exists")
    p_render.add_argument("--detach", action="store_true", help="launch detached and return immediately")
    p_render.set_defaults(func=cmd_render)

    p_pdf = sub.add_parser("pdf", parents=[json_parent], help="assemble the architect-brief PDF")
    p_pdf.add_argument("spec")
    p_pdf.add_argument("--brief", default=None, help="path to brief copy JSON (default: spec/briefs/<name>.json)")
    p_pdf.add_argument("--hero", default=None, help="view name to use as cover hero image")
    p_pdf.add_argument("--embed-images", action="store_true",
                       help="embed gallery images as base64 data URIs (self-contained HTML; large)")
    p_pdf.add_argument("--require-fresh", action="store_true",
                       help="fail (exit 1) if any gallery render is stale vs the current model")
    p_pdf.set_defaults(func=cmd_pdf)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
