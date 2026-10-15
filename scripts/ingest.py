"""Validate the checked-in, rights-reviewed scripture fixture before rendering."""
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripture" / "genesis_1_1-5.json"
PLAN = ROOT / "scene_plan.json"
OUT = ROOT / "build" / "ingested.json"


def main():
    scripture = json.loads(SOURCE.read_text(encoding="utf-8"))
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if scripture["reference"] != "Genesis 1:1-5" or plan["reference"] != scripture["reference"]:
        raise ValueError("Unexpected scripture reference")
    if [s["verse"] for s in plan["scenes"]] != [1, 2, 3, 4, 5]:
        raise ValueError("Scene plan must cover Genesis 1:1-5 exactly")
    expected = {str(v) for v in range(1, 6)}
    for language in ("english", "tagalog"):
        record = scripture[language]
        if set(record["verses"]) != expected:
            raise ValueError(f"Missing or extra {language} verses")
        if not all(isinstance(v, str) and v.strip() for v in record["verses"].values()):
            raise ValueError(f"Empty {language} verse")
        for field in ("rights_url", "source_url"):
            url = urlparse(record[field])
            if url.scheme != "https" or url.netloc != "ebible.org":
                raise ValueError(f"Unreviewed source URL in {language}: {field}")
    if scripture["english"]["rights"] != "public-domain":
        raise ValueError("English source is not approved for this fixture")
    if scripture["tagalog"]["rights"] != "original-draft":
        raise ValueError("Tagalog text must remain identified as a draft adaptation")
    if scripture["tagalog"]["translation_status"] != "draft-needs-human-review":
        raise ValueError("Tagalog review status changed; update policy intentionally")
    for language in ("english", "tagalog"):
        lines = plan["dialogue"][language]["3"]
        if len(lines) != 3 or any(not x["text"].strip() for x in lines):
            raise ValueError(f"Verse 3 dialogue invalid: {language}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"scripture": scripture, "plan": plan}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Validated {scripture['reference']} and wrote {OUT}")


if __name__ == "__main__":
    main()

