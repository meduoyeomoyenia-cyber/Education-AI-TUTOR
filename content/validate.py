"""Validate vetted bank. Run: python content/validate.py"""
import json, pathlib, sys
HERE = pathlib.Path(__file__).parent
bank = json.loads((HERE/"questions.vetted.json").read_text()) if (HERE/"questions.vetted.json").exists() else []
errs = []
for i, vq in enumerate(bank):
    for f in ("topic","subject","stem","answer","difficulty","exam_style","source","license"):
        if f not in vq or vq[f] in ("", None):
            errs.append(f"row {i} missing {f}")
    if isinstance(vq.get("options"), list) and vq["options"] and vq["answer"] not in vq["options"]:
        # allow short-answer where options list holds distractors; MCQ must contain answer
        if len(vq["options"]) == 4:
            errs.append(f"row {i} answer not in MCQ options")
if errs:
    print("FAIL"); print("\n".join(errs[:20])); sys.exit(1)
print(f"vetted ok: {len(bank)}")
