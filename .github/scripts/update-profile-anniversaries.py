from datetime import date, datetime
import os
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
README_PATH = ROOT / "README.md"
HEADING_RE = re.compile(
    r"(?m)^### (?P<age>\d+)yo Developer / 29卒 / 専門(?P<school>\d+)年生$"
)
STATE_RE = re.compile(
    r"(?m)^<!-- profile-anniversaries: "
    r"age=(?P<age>\d+); age-year=(?P<age_year>\d{4}); "
    r"school=(?P<school>\d+); school-year=(?P<school_year>\d{4}); "
    r"heartbeat=(?P<heartbeat>\d{4}-\d{2}) -->$"
)


def main() -> int:
    readme = README_PATH.read_text(encoding="utf-8")
    heading_match = HEADING_RE.search(readme)
    state_match = STATE_RE.search(readme)

    if heading_match is None or state_match is None:
        raise SystemExit("Expected profile heading or anniversary state marker was not found.")

    age = int(state_match.group("age"))
    age_year = int(state_match.group("age_year"))
    school_year = int(state_match.group("school"))
    school_updated_year = int(state_match.group("school_year"))
    heartbeat = state_match.group("heartbeat")

    if (int(heading_match.group("age")), int(heading_match.group("school"))) != (
        age,
        school_year,
    ):
        raise SystemExit("Visible profile values do not match the anniversary state marker.")

    today = datetime.now(ZoneInfo("Asia/Tokyo")).date()
    mode = os.environ.get("UPDATE_MODE", "both")
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")

    if mode not in {"both", "age", "school"}:
        raise SystemExit(f"Unsupported update mode: {mode}")

    age_delta = 0
    if mode in {"both", "age"} and today >= date(today.year, 9, 29):
        age_delta = max(0, today.year - age_year)

    school_delta = 0
    if mode in {"both", "school"} and today >= date(today.year, 4, 1):
        school_delta = max(0, today.year - school_updated_year)

    age += age_delta
    age_year += age_delta
    school_year += school_delta
    school_updated_year += school_delta

    next_heartbeat = heartbeat
    if event_name == "schedule":
        current_month = today.strftime("%Y-%m")
        if current_month > heartbeat:
            next_heartbeat = current_month

    new_heading = f"### {age}yo Developer / 29卒 / 専門{school_year}年生"
    new_state = (
        "<!-- profile-anniversaries: "
        f"age={age}; age-year={age_year}; "
        f"school={school_year}; school-year={school_updated_year}; "
        f"heartbeat={next_heartbeat} -->"
    )

    updated = HEADING_RE.sub(new_heading, readme, count=1)
    updated = STATE_RE.sub(new_state, updated, count=1)

    if updated == readme:
        print("No anniversary or heartbeat update is due.")
        return 0

    README_PATH.write_text(updated, encoding="utf-8")
    print(
        "Updated profile state: "
        f"age +{age_delta}, school year +{school_delta}, "
        f"heartbeat {next_heartbeat}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
