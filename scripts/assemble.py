"""Build bilingual narrated episode and Short MP4s from Blender scene loops."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
RENDERS = BUILD / "frames"
OUTPUT = BUILD / "deliverables"


def run(*args):
    print("+", " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), check=True)


def seconds(path):
    result = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], text=True)
    return float(result.strip())


def concat_list(paths, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    listfile = destination.with_suffix(".txt")
    listfile.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in paths), encoding="utf-8")
    return listfile


def make_audio(language, verse, lines):
    folder = BUILD / "audio" / language / str(verse)
    folder.mkdir(parents=True, exist_ok=True)
    wavs = []
    durations = []
    voice = "en-us" if language == "english" else "id"
    for index, line in enumerate(lines):
        textfile = folder / f"{index:02d}.txt"
        wav = folder / f"{index:02d}.wav"
        textfile.write_text(line["text"], encoding="utf-8")
        pitch = 33 if line["role"] == "character" else 54
        run("espeak-ng", "-v", voice, "-s", "135", "-p", str(pitch), "-f", textfile, "-w", wav)
        wavs.append(wav)
        durations.append(seconds(wav))
    joined = folder / "scene.wav"
    run("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", concat_list(wavs, joined),
        "-ac", "1", "-ar", "22050", "-c:a", "pcm_s16le", joined)
    return joined, durations


def scene_lines(data, language, verse):
    dialogue = data["plan"]["dialogue"][language]
    if str(verse) in dialogue:
        narrator = "Narrator" if language == "english" else "Tagapagsalaysay"
        return [{"role": "character" if item["speaker"] != narrator else "narrator",
                 "speaker": item["speaker"], "text": item["text"]} for item in dialogue[str(verse)]]
    return [{"role": "narrator", "speaker": "Narrator" if language == "english" else "Tagapagsalaysay",
             "text": data["scripture"][language]["verses"][str(verse)]}]


def srt_time(value):
    millis = round(value * 1000)
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def make_loop(verse):
    target = BUILD / "loops" / f"scene_{verse}.mp4"
    target.parent.mkdir(parents=True, exist_ok=True)
    ai_clip = BUILD / "ai_clips" / f"scene_{verse}.mp4"
    if ai_clip.is_file():
        run("ffmpeg", "-y", "-v", "error", "-i", ai_clip, "-an",
            "-vf", "scale=360:640:force_original_aspect_ratio=increase,crop=360:640,fps=24",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", target)
        return target
    run("ffmpeg", "-y", "-v", "error", "-framerate", "6", "-i", RENDERS / f"scene_{verse}" / "%03d.png",
        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", "24", target)
    return target


def make_variant(data, language, kind, verses, loops):
    work = BUILD / "variant" / language / kind
    work.mkdir(parents=True, exist_ok=True)
    scene_videos = []
    captions = []
    cursor = 0.0
    for verse in verses:
        lines = scene_lines(data, language, verse)
        audio, durations = make_audio(language, verse, lines)
        length = seconds(audio) + 0.25
        scene_video = work / f"scene_{verse}.mp4"
        run("ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", loops[verse], "-i", audio,
            "-t", f"{length:.3f}", "-map", "0:v:0", "-map", "1:a:0", "-vf", "fps=24",
            "-af", "apad", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "22050", "-ac", "1", scene_video)
        scene_videos.append(scene_video)
        line_cursor = cursor
        for line, duration in zip(lines, durations):
            label = (line["speaker"] + ": " if line["role"] == "character" else "") + line["text"]
            captions.append((line_cursor, line_cursor + duration, label))
            line_cursor += duration
        cursor += length
    joined = work / "joined.mp4"
    run("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", concat_list(scene_videos, joined),
        "-c", "copy", joined)
    srt = OUTPUT / f"genesis_1_1-5_{kind}_{language}{'_draft' if language == 'tagalog' else ''}.srt"
    srt.parent.mkdir(parents=True, exist_ok=True)
    srt.write_text("\n\n".join(f"{i}\n{srt_time(start)} --> {srt_time(end)}\n{text}"
                               for i, (start, end, text) in enumerate(captions, 1)) + "\n", encoding="utf-8")
    final = srt.with_suffix(".mp4")
    # Relative subtitle filename is safe on the Linux GitHub runner.
    run("ffmpeg", "-y", "-v", "error", "-i", joined,
        "-vf", f"subtitles={srt.as_posix()}:force_style='FontName=DejaVu Sans,FontSize=16,Outline=2,Alignment=2,MarginV=38'",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "25", "-pix_fmt", "yuv420p",
        "-c:a", "copy", final)
    print(f"Created {final} ({seconds(final):.1f}s)")


def main():
    data = json.loads((BUILD / "ingested.json").read_text(encoding="utf-8"))
    loops = {verse: make_loop(verse) for verse in range(1, 6)}
    for language in ("english", "tagalog"):
        make_variant(data, language, "episode", range(1, 6), loops)
        make_variant(data, language, "short", range(1, 4), loops)
    ai_note = (
        "Verse 3 AI clip: ByteDance/AnimateDiff-Lightning on Hugging Face ZeroGPU; ToonYou base; review model and base-model rights before publishing.\n"
        if (BUILD / "ai_clips" / "scene_3.mp4").is_file()
        else "Visuals: procedural Blender animation only; no AI-generated clip.\n"
    )
    (OUTPUT / "PROVENANCE.txt").write_text(
        "English scripture: World English Bible Classic, public domain.\n"
        "https://ebible.org/eng-web/GEN01.htm\n"
        "https://ebible.org/eng-web/copyright.htm\n\n"
        "Tagalog: original draft adaptation of the English WEB text; human language and theological review required before publishing.\n"
        "Voice: eSpeak NG English; Indonesian voice used as a pronunciation proxy for Tagalog.\n"
        + ai_note,
        encoding="utf-8")


if __name__ == "__main__":
    main()

