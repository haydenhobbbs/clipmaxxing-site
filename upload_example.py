"""Clip Maxxing Uploader - complete upload script (the same flow the app uses).

Uploads one approved clip to the signed-in owner's own YouTube channel through the
YouTube Data API (videos.insert), then prints the video URL.

Requirements:  pip install google-api-python-client google-auth-oauthlib
Usage:         python upload_example.py client_secret.json clip.mp4 "Title" "Description"

client_secret.json is the OAuth "Desktop app" client from Google Cloud. The first run opens
Google's consent screen in the browser; the token is saved next to this script (token.json)
and never leaves the owner's computer.
"""
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
TOKEN = Path(__file__).with_name("token.json")


def credentials(client_secret: str) -> Credentials:
    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES) if TOKEN.exists() else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        creds = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES).run_local_server(port=0)
    TOKEN.write_text(creds.to_json())
    return creds


def main() -> None:
    client_secret, video, title, description = sys.argv[1:5]
    youtube = build("youtube", "v3", credentials=credentials(client_secret))
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {"title": title[:100], "description": description, "categoryId": "20"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
        },
        media_body=MediaFileUpload(video, chunksize=-1, resumable=True),
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")
    print(f"Done: https://youtube.com/shorts/{response['id']}")


if __name__ == "__main__":
    main()
