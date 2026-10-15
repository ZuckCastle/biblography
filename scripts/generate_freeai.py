"""Experimental one-shot Free.ai CogVideoX render for verse 3 on GitHub Actions.

This is intentionally opt-in. The provider's free allowance and API response
shape can change; a missing key or quota error fails the experimental run.
"""
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.free.ai"
MAX_BYTES = 100 * 1024 * 1024


def request_json(url, key, payload=None):
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=None if payload is None else json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read(500).decode("utf-8", "replace")
        raise RuntimeError(f"Free.ai returned HTTP {exc.code}: {body}") from exc


def video_url(data):
    direct = data.get("video_url") or data.get("output_url")
    video = data.get("video")
    if isinstance(video, dict):
        direct = direct or video.get("url")
    elif isinstance(video, str):
        direct = direct or video
    result = data.get("result")
    if isinstance(result, dict):
        direct = direct or video_url(result)
    return direct


def main():
    key = os.environ.get("FREE_AI_API_KEY", "")
    if not key:
        raise RuntimeError("Set FREE_AI_API_KEY as a GitHub Actions secret for this optional run")
    plan = json.loads((ROOT / "scene_plan.json").read_text(encoding="utf-8"))
    prompt = next(s["ai_prompt"] for s in plan["scenes"] if s["verse"] == 3)
    response = request_json(f"{API}/v1/video/generate/", key, {
        "model": "cogvideox", "prompt": prompt, "duration": 3, "aspect_ratio": "9:16"
    })
    url = video_url(response)
    job_id = response.get("job_id") or response.get("id")
    deadline = time.monotonic() + 10 * 60
    while not url and job_id and time.monotonic() < deadline:
        time.sleep(10)
        response = request_json(f"{API}/v1/status/{job_id}/", key)
        status = str(response.get("status", "")).lower()
        if status in {"failed", "error", "cancelled", "canceled"}:
            raise RuntimeError(f"Free.ai generation failed: {str(response)[:500]}")
        url = video_url(response)
    if not url:
        raise RuntimeError(f"Free.ai did not return a video URL or a supported job ID: {str(response)[:500]}")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise RuntimeError("Provider returned a non-HTTPS video URL")
    output = ROOT / "build" / "ai_clips" / "scene_3.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "bible-animation-studio/0.1"})
    with urllib.request.urlopen(req, timeout=180) as source, output.open("wb") as target:
        copied = 0
        while chunk := source.read(1024 * 1024):
            copied += len(chunk)
            if copied > MAX_BYTES:
                raise RuntimeError("Generated clip exceeds 100 MB safety limit")
            target.write(chunk)
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name",
                            "-of", "default=noprint_wrappers=1:nokey=1", str(output)], check=True, capture_output=True, text=True)
    if not probe.stdout.strip():
        raise RuntimeError("Provider output does not contain a video stream")
    deliverable = ROOT / "build" / "deliverables"
    deliverable.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output, deliverable / "experimental_ai_scene_3.mp4")
    print(f"Generated experimental AI clip: {output} ({copied} bytes)")


if __name__ == "__main__":
    main()
