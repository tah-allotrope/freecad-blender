# designs/

User-authored home specs live here. Each file is a complete `homedesign`
spec JSON: site plot, storeys, rooms, openings, views.

- `tubehouse-dream.json` — the flagship 4x25 m tube house (5 storeys).

To build a design, run from the repo root:

```bash
homedesign build designs/<slug>.json
homedesign pdf designs/<slug>.json
```

See `AGENTS.md` for the full workflow. `spec/examples/` holds smaller
reproducible fixtures; `spec/homespec.schema.json` is the spec schema —
neither moves.
