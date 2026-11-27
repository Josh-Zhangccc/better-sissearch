#!/usr/bin/env python3
"""Overlay the SAI official AIE 1904 page onto data/courses.json.

SIS Class Search lists all eight AIE 1904 sections with the instructor
"Staff": the SIS snapshot alone cannot tell a student who teaches a section
or which topic it covers. The School of Artificial Intelligence publishes the
2027-spring schedule (time, lecturer, topic, room) on its own course page:

    https://sai.cuhk.edu.cn/zh-hans/aie1904-spring2027

`data/sai_aie1904_spring2027.json` is that page's own JSON feed, captured and
section-keyed (S01–S08 line up with the SIS section labels; every SAI room
code matches the SIS room of the same label). This script applies it on top
of the SIS snapshot, so the pipeline stays reproducible:

    python scrape_full.py          # refresh the SIS snapshot (staff back to "Staff")
    python apply_sai.py            # re-apply the SAI time/lecturer overlay

Only `instructor` and the single meeting time of AIE 1904 are touched; rooms,
class numbers and every other course are left exactly as scraped.

Usage:
  python apply_sai.py            # write data/courses.json
  python apply_sai.py --dry-run  # print the changes only
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COURSES = os.path.join(HERE, "data", "courses.json")
OVERLAY = os.path.join(HERE, "data", "sai_aie1904_spring2027.json")


def ampm(hhmm: str) -> str:
    h, m = (int(x) for x in hhmm.split(":"))
    suffix = "AM" if h < 12 else "PM"
    return f"{h % 12 or 12}:{m:02d}{suffix}"


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.load(open(COURSES, encoding="utf-8"))
    overlay = json.load(open(OVERLAY, encoding="utf-8"))
    code = overlay["course"]

    course = next((c for c in data["courses"] if c["code"] == code), None)
    if course is None:
        print(f"ERROR: {code} not found in {COURSES}", file=sys.stderr)
        return 1

    by_section = {s["section"]: s for s in course["sections"]}
    print(f"{code} — {course['title']}  ({len(by_section)} sections in SIS, "
          f"{len(overlay['sections'])} in SAI overlay)")

    changes = []
    missing = []
    for src in overlay["sections"]:
        section = by_section.get(src["section"])
        if section is None:
            missing.append(src["section"])
            continue
        old = (section.get("instructor"),
               [(m["day"], m["start"], m["end"]) for m in section["meetings"]])
        section["instructor"] = src["instructor"]
        section["meetings"] = [{
            "day": src["day"],
            "start": src["start"],
            "end": src["end"],
            "raw": f"{src['day']} {ampm(src['start'])} - {ampm(src['end'])}",
        }]
        new = (section["instructor"],
               [(m["day"], m["start"], m["end"]) for m in section["meetings"]])
        flag = "" if src["room"] == section["room"] else \
            f"  [WARN room differs: SIS {section['room']!r} vs SAI {src['room']!r}]"
        changes.append((src["section"], old, new, flag))
        print(f"  {src['section']}: {old[0]} {old[1][0][0]} {old[1][0][1]}–{old[1][0][2]}"
              f"  ->  {new[0]} {new[1][0][0]} {new[1][0][1]}–{new[1][0][2]}{flag}")

    extra = sorted(set(by_section) - {s["section"] for s in overlay["sections"]})
    if missing:
        print(f"ERROR: overlay names sections SIS does not have: {missing}",
              file=sys.stderr)
        return 1
    if extra:
        print(f"WARNING: SIS has sections the overlay does not cover: {extra}")

    if dry:
        print(f"dry run: {len(changes)} sections would be updated; nothing written")
        return 0
    with open(COURSES, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"wrote {COURSES}: {len(changes)} sections updated from SAI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
