"""Fail the cloud build if any bilingual video or caption is missing or malformed."""
import json
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "build" / "deliverables"


def probe(path):
    result = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)
    ], text=True)
    return json.loads(result)


def main():
    for language in ("english", "tagalog"):
        durations = {}
        for kind in ("episode", "short"):
            stem = f"genesis_1_1-5_{kind}_{language}{'_draft' if language == 'tagalog' else ''}"
            video = OUT / f"{stem}.mp4"
            captions = OUT / f"{stem}.srt"
            if not captions.is_file() or "-->" not in captions.read_text(encoding="utf-8"):
                raise RuntimeError(f"Missing captions: {captions}")
            info = probe(video)
            streams = info["streams"]
            if not any(s["codec_type"] == "audio" for s in streams):
                raise RuntimeError(f"Missing audio: {video}")
            if not any(s["codec_type"] == "video" and s["width"] == 360 and s["height"] == 640 for s in streams):
                raise RuntimeError(f"Wrong video dimensions: {video}")
            durations[kind] = float(info["format"]["duration"])
            if durations[kind] < 5:
                raise RuntimeError(f"Suspiciously short output: {video}")
        if durations["episode"] <= durations["short"]:
            raise RuntimeError(f"Episode must be longer than Short: {language}")
    print("Verified four videos, four captions, audio streams, dimensions, and durations")


if __name__ == "__main__":
    main()
