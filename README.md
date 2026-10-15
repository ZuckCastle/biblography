# Bible Animation Studio: Genesis 1:1–5 prototype

One YouTube channel, two language series. This first cloud workflow makes four files: English and Tagalog draft **episodes** covering Genesis 1:1–5, plus **Shorts** covering 1:1–3. The prototype has a narrator and a separate character voice for God's quoted line in 1:3. It renders simple low-poly 3D scenes in headless Blender, synthesizes speech with eSpeak NG, and assembles captioned MP4s with FFmpeg.

## Run in GitHub Actions

1. Create a public GitHub repository and push these files to `main`.
2. Open **Actions → Genesis prototype**. A push to `main` starts the build automatically; **Run workflow** also works.
3. When the build finishes, download the `genesis-1-1-5-prototype` artifact. It contains four MP4s, four SRT caption files, and `PROVENANCE.txt`.

The build job uses `ubuntu-24.04` on GitHub, installs Blender, FFmpeg, eSpeak NG, and Xvfb, and does all rendering there. No local PC is needed once the repository is on GitHub. The repository contains no generated video; videos are workflow artifacts retained for seven days.

### Experimental free AI shot

The manual workflow has `experimental_ai_scene`. If enabled, GitHub Actions asks the public [ByteDance AnimateDiff-Lightning Space](https://huggingface.co/spaces/ByteDance/AnimateDiff-Lightning) on [Hugging Face ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu) for **one short shot for verse 3** and uses it in both language cuts. The artifact includes `experimental_ai_scene_3.mp4` for separate review when generation succeeds. The Space's 4-step ToonYou setting generated a 2-second clip in an anonymous website test on 2026-10-15. The GitHub Actions API path may still fail due to anonymous shared quota, queue limits, service changes, or an unavailable Space. An optional `HF_TOKEN` GitHub secret for a free Hugging Face account gives the request that account's daily quota; never paste the token into a commit or workflow input. The default build does not call the Space.

The AI clip is an early quality experiment: short, square, and potentially inconsistent with the other scenes. It is cropped to the vertical frame and repeated to cover narration. The Space uses AnimateDiff-Lightning and the ToonYou base model. Review the [AnimateDiff license](https://huggingface.co/ByteDance/AnimateDiff-Lightning) and [ToonYou model](https://huggingface.co/frankjoshua/toonyou_beta6), including the base model's incomplete rights information, before any YouTube upload. The `ai_rights_reviewed` upload gate must only be checked after that review. A failed AI attempt leaves the four Blender videos available and records that fallback in `PROVENANCE.txt`.

We also tested [Free.ai's CogVideoX API](https://free.ai/models/cogvideox-2b/) with a free key. It returned `HTTP 429` with `not_in_tier`: **free API keys do not include video generation**; its website allowance is separate. `scripts/generate_freeai.py` is retained for a future account with paid API video tokens, but the workflow does not call it.

## Scripture and translation safeguards

- The checked-in English verses are the **World English Bible Classic**, Genesis 1:1–5, sourced from [eBible](https://ebible.org/eng-web/GEN01.htm). The [rights statement](https://ebible.org/eng-web/copyright.htm) says WEB is public domain. The text is preserved as a verse fixture; the dialogue split in verse 3 is for performance.
- The Tagalog text is an **original draft adaptation of WEB**, not a claimed quotation from a published Tagalog Bible. It needs a fluent Tagalog and theological review before uploading. `scripts/ingest.py` rejects changes to the translation status, unexpected verse sets, unreviewed rights labels, or sources outside eBible.
- New scripture passages or translations require a source and rights review, followed by an explicit update to the ingestion policy. The current script deliberately accepts only this fixture. A public-domain English source does not automatically make a third-party translation reusable.

## Optional YouTube upload

Uploads are disabled on pushes. To enable them, configure a GitHub environment named `youtube-publish` with a **required reviewer** and environment secrets `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, and `YOUTUBE_REFRESH_TOKEN`. The OAuth token must grant `https://www.googleapis.com/auth/youtube.upload` for the intended single channel. GitHub's environment protection is the human approval gate; keep these credentials in that environment only.

Then use **Run workflow** and set `upload_to_youtube=true`, `tagalog_reviewed=true` only after a real review, and select the correct `made_for_kids` answer. For private or unlisted uploads type `UPLOAD`; for public upload select `public` and type `PUBLISH_PUBLIC`. The workflow builds first, pauses for the `youtube-publish` reviewer, then uploads all four files. Do not assume family-friendly content determines the YouTube audience setting; make that decision for the actual videos.

The upload script uses one OAuth identity, so all four videos go to one channel. Separate language series are expressed in titles and tags. Playlist creation is not part of this MVP. Google may require API project verification, channel setup, or quota; credentials and environment approval are not provisioned by this repository.

## What this prototype does and does not solve

- Blender renders five 2-second animation loops at 360×640 and 6 frames/s. FFmpeg repeats each loop to match its narration and outputs 24 frames/s. Motion is simple and repeated, and 24 frames/s does not add new 3D poses. This is a working procedural visual pipeline, not cinematic AI animation.
- The optional AI shot can improve one visual beat, but text-to-video output may be inconsistent with the other four scenes, and the short clip is repeated over longer narration. It does not solve character consistency or full-episode direction.
- eSpeak NG makes a distinct lower-pitch quoted voice. Its English voice is synthetic. It has no proper Tagalog voice in this setup, so the Tagalog text is read with an Indonesian pronunciation proxy. The MP4 is useful for pipeline review, not publication quality. Replace it with a licensed Tagalog recording or TTS voice and listen before upload.
- The Short is an excerpt with vertical video, not an automatically edited social clip. Episode and Short durations follow speech length.
- Public GitHub repositories can use standard GitHub-hosted runners without billed runner minutes under [GitHub's current policy](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job); storage and third-party API quotas still have limits. Private repositories have included minute and storage allowances that vary by plan.

## Local developer commands

GitHub Actions is the production path. For changes to the pipeline, a Linux machine with `blender`, `xvfb-run`, `ffmpeg`, and `espeak-ng` can reproduce it:

```bash
python3 scripts/ingest.py
xvfb-run -a blender -b -t 2 --python scripts/render_blender.py -- --out build/frames --fps 6 --frames-per-scene 12
python3 scripts/assemble.py
```

The workflow installs these tools on each cloud run. The optional upload step additionally installs `requirements.txt`.

