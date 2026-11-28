#!/usr/bin/env python3
"""Overlay the SAI official AIE course pages onto data/courses.json.

SIS Class Search lists the AIE exploration courses (AIE 1902 / 1904) with the
instructor "Staff": these are college-run courses whose own teaching plan is
published by the School of Artificial Intelligence on its course pages —

    https://sai.cuhk.edu.cn/zh-hans/aie1902-spring2027
    https://sai.cuhk.edu.cn/zh-hans/aie1904-spring2027

`data/sai_aie*_spring2027.json` are those pages' own JSON feeds, captured and
section-keyed (S01–S11 / S01–S08 line up with the SIS section labels; every
SAI room code matches the SIS room of the same label). This script applies
them on top of the SIS snapshot, so the pipeline stays reproducible:

    python scrape_full.py          # refresh the SIS snapshot (staff back to "Staff")
    python apply_sai.py            # re-apply every SAI time/lecturer overlay

Only `instructor` and the single meeting time of the overlaid courses are
touched; rooms, class numbers and every other course are left as scraped.

Usage:
  python apply_sai.py            # write data/courses.json
  python apply_sai.py --dry-run  # print the changes only
"""
from __future__ import annotations

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COURSES = os.path.join(HERE, "data", "courses.json")
OVERLAY_GLOB = os.path.join(HERE, "data", "sai_aie*_spring2027.json")


def ampm(hhmm: str) -> str:
    h, m = (int(x) for x in hhmm.split(":"))
    suffix = "AM" if h < 12 else "PM"
    return f"{h % 12 or 12}:{m:02d}{suffix}"


def apply_overlay(data: dict, overlay: dict) -> int:
    """Apply one course overlay; return the number of sections updated."""
    code = overlay["course"]
    course = next((c for c in data["courses"] if c["code"] == code), None)
    if course is None:
        raise SystemExit(f"ERROR: {code} not found in {COURSES}")

    by_section = {s["section"]: s for s in course["sections"]}
    print(f"\n{code} — {course['title']}  ({len(by_section)} sections in SIS, "
          f"{len(overlay['sections'])} in SAI overlay)")

    missing = []
    updated = 0
    for src in overlay["sections"]:
        section = by_section.get(src["section"])
        if section is None:
            missing.append(src["section"])
            continue
        old_instr = section.get("instructor")
        old_meet = [(m["day"], m["start"], m["end"]) for m in section["meetings"]]
        section["instructor"] = src["instructor"]
        section["meetings"] = [{
            "day": src["day"],
            "start": src["start"],
            "end": src["end"],
            "raw": f"{src['day']} {ampm(src['start'])} - {ampm(src['end'])}",
        }]
        new_meet = [(m["day"], m["start"], m["end"]) for m in section["meetings"]]
        warn = "" if src["room"] == section["room"] else \
            f"  [WARN room differs: SIS {section['room']!r} vs SAI {src['room']!r}]"
        if old_instr != section["instructor"] or old_meet != new_meet:
            print(f"  {src['section']}: {old_instr} {old_meet[0][0]} "
                  f"{old_meet[0][1]}–{old_meet[0][2]}  ->  "
                  f"{section['instructor']} {new_meet[0][0]} "
                  f"{new_meet[0][1]}–{new_meet[0][2]}{warn}")
            updated += 1
    if missing:
        raise SystemExit(f"ERROR: {code} overlay names sections SIS does not "
                         f"have: {missing}")
    extra = sorted(set(by_section) - {s["section"] for s in overlay["sections"]})
    if extra:
        print(f"  WARNING: SIS has sections the overlay does not cover: {extra}")
    return updated


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.load(open(COURSES, encoding="utf-8"))
    overlays = [json.load(open(p, encoding="utf-8"))
                for p in sorted(glob.glob(OVERLAY_GLOB))]
    if not overlays:
        print(f"ERROR: no overlay files matched {OVERLAY_GLOB}", file=sys.stderr)
        return 1

    total = sum(apply_overlay(data, o) for o in overlays)

    if dry:
        print(f"\ndry run: {total} sections would be updated; nothing written")
        return 0
    with open(COURSES, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"\nwrote {COURSES}: {total} sections updated from SAI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
