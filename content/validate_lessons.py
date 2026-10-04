"""Validate vetted lessons. Run: python content/validate_lessons.py"""
import json, pathlib, sys
HERE = pathlib.Path(__file__).parent
lessons = json.loads((HERE / "lessons.vetted.json").read_text(encoding="utf-8"))
errs = []
for i, ls in enumerate(lessons):
    for f in ("topic", "subject", "title", "objectives", "explanation", "examples", "key_points", "language", "source", "license"):
        if f not in ls or ls[f] in ("", None, []):
            errs.append(f"lesson {i} missing/empty {f}")
    for j, ex in enumerate(ls.get("examples", [])):
        for f in ("title", "steps", "answer"):
            if f not in ex or ex[f] in ("", None, []):
                errs.append(f"lesson {i} example {j} missing/empty {f}")
if errs:
    print("FAIL"); print("\n".join(errs[:20])); sys.exit(1)
print(f"lessons ok: {len(lessons)}")
