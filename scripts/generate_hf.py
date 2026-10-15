"""Generate one experimental Genesis light shot on a public ZeroGPU Space."""
import json
import os
import shutil
import subprocess
from pathlib import Path

from gradio_client import Client

ROOT = Path(__file__).resolve().parents[1]
SPACE = "ByteDance/AnimateDiff-Lightning"


def main():
    plan = json.loads((ROOT / "scene_plan.json").read_text(encoding="utf-8"))
    prompt = next(scene["ai_prompt"] for scene in plan["scenes"] if scene["verse"] == 3)
    token = os.environ.get("HF_TOKEN") or None
    client = Client(SPACE, token=token)
    result = client.predict(
        prompt=prompt,
        base="ToonYou",
        motion="",
        step="4",
        api_name="/generate_image",
    )
    source = result.get("video") if isinstance(result, dict) else result
    if not source or not Path(source).is_file():
        raise RuntimeError(f"Hugging Face did not return a local video file: {str(result)[:300]}")
    output = ROOT / "build" / "ai_clips" / "scene_3.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, output)
    if output.stat().st_size > 100 * 1024 * 1024:
        output.unlink()
        raise RuntimeError("Generated clip exceeds 100 MB safety limit")
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1", str(output)],
        check=True, capture_output=True, text=True,
    )
    if not probe.stdout.strip():
        output.unlink()
        raise RuntimeError("Generated clip contains no video stream")
    deliverables = ROOT / "build" / "deliverables"
    deliverables.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output, deliverables / "experimental_ai_scene_3.mp4")
    (ROOT / "build" / "ai_clips" / "provider.txt").write_text(
        "ByteDance/AnimateDiff-Lightning on Hugging Face ZeroGPU; ToonYou base; 4 steps.\n",
        encoding="utf-8",
    )
    print(f"Generated {output} using {SPACE}")


if __name__ == "__main__":
    main()

