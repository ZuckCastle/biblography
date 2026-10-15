"""Opt-in upload to the one channel authorized by the OAuth refresh token."""
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "build" / "deliverables"


def required(name):
    value = os.getenv(name, "")
    if not value:
        raise RuntimeError(f"Missing {name}")
    return value


def main():
    visibility = required("YOUTUBE_VISIBILITY")
    if visibility not in {"private", "unlisted", "public"}:
        raise RuntimeError("Invalid visibility")
    if required("TAGALOG_REVIEWED") != "true":
        raise RuntimeError("Human review of the Tagalog draft is required before uploading")
    audience = required("MADE_FOR_KIDS")
    if audience not in {"true", "false"}:
        raise RuntimeError("Set MADE_FOR_KIDS explicitly to true or false")
    credentials = Credentials(
        token=None,
        refresh_token=required("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=required("YOUTUBE_CLIENT_ID"),
        client_secret=required("YOUTUBE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    titles = {
        ("english", "episode"): "Genesis 1:1–5 | The First Day | English",
        ("english", "short"): "Let There Be Light | Genesis 1:1–3 | English Short",
        ("tagalog", "episode"): "Genesis 1:1–5 | Ang Unang Araw | Tagalog",
        ("tagalog", "short"): "Magkaroon ng Liwanag | Genesis 1:1–3 | Tagalog Short",
    }
    for (language, kind), title in titles.items():
        suffix = "_draft" if language == "tagalog" else ""
        path = OUTPUT / f"genesis_1_1-5_{kind}_{language}{suffix}.mp4"
        if not path.is_file():
            raise FileNotFoundError(path)
        description = (
            "Genesis 1:1–5 visual prototype. English Scripture: World English Bible Classic, public domain. "
            "https://ebible.org/eng-web/GEN01.htm\n"
            "Tagalog text is an original adaptation of the WEB and was reviewed by a human before upload. "
            "Computer-generated voices and simple procedural 3D animation."
        )
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "categoryId": "22",
                    "defaultLanguage": "en" if language == "english" else "tl",
                    "tags": ["Bible", "Genesis", "English" if language == "english" else "Tagalog"],
                },
                "status": {
                    "privacyStatus": visibility,
                    "selfDeclaredMadeForKids": audience == "true",
                },
            },
            media_body=MediaFileUpload(str(path), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True),
        )
        response = None
        while response is None:
            _, response = request.next_chunk()
        print(f"Uploaded {language} {kind}: https://www.youtube.com/watch?v={response['id']}")


if __name__ == "__main__":
    main()

