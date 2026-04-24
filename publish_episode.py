#!/usr/bin/env python3
"""
publish_episode.py — called by the daily SHTG digest scheduled task after
generating a new MP3. Updates feed.xml and pushes everything to GitHub Pages.

Usage:
    python3 publish_episode.py \
        --date 2026-04-24 \
        --mp3 /path/to/shtg-podcast-2026-04-24.mp3 \
        --title "SHTG Digest — Friday April 24, 2026" \
        --summary "One-sentence summary for the feed item description." \
        --duration "7:00"

Environment variables required (set in ~/.bashrc or pass directly):
    GITHUB_TOKEN   — Personal access token with repo scope
    GITHUB_REPO    — e.g.  YOUR_GITHUB_USERNAME/shtg-podcast
"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from email.utils import format_datetime

GITHUB_API = "https://api.github.com"
BRANCH = "main"


def gh_request(method, path, token, data=None):
    url = f"{GITHUB_API}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url, data=body, method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"GitHub API error {e.code}: {e.read().decode()}")
        sys.exit(1)


def get_file_sha(token, repo, path):
    """Return (sha, content) for an existing file, or (None, None) if missing."""
    try:
        result = gh_request("GET", f"/repos/{repo}/contents/{path}", token)
        return result["sha"], base64.b64decode(result["content"]).decode()
    except SystemExit:
        return None, None


def upload_file(token, repo, path, content_bytes, message, sha=None):
    data = {
        "message": message,
        "content": base64.b64encode(content_bytes).decode(),
        "branch": BRANCH,
    }
    if sha:
        data["sha"] = sha
    return gh_request("PUT", f"/repos/{repo}/contents/{path}", token, data)


def inject_episode(feed_xml, date_str, title, summary, mp3_url, mp3_size, duration):
    """Insert a new <item> block into feed.xml, newest first."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=6)
    pub_date = format_datetime(dt)

    episode_id = f"shtg-digest-{date_str}"

    item = f"""
    <item>
      <title>{title}</title>
      <description><![CDATA[{summary}]]></description>
      <pubDate>{pub_date}</pubDate>
      <guid isPermaLink="false">{episode_id}</guid>
      <enclosure
        url="{mp3_url}"
        length="{mp3_size}"
        type="audio/mpeg"/>
      <itunes:title>{title}</itunes:title>
      <itunes:duration>{duration}</itunes:duration>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:explicit>false</itunes:explicit>
    </item>
"""

    marker = "<!-- Add new <item> blocks above this line, newest first -->"
    if marker not in feed_xml:
        raise ValueError("Marker comment not found in feed.xml — was it edited?")

    # Avoid duplicate entries
    if episode_id in feed_xml:
        print(f"Episode {episode_id} already in feed — skipping duplicate.")
        return feed_xml

    return feed_xml.replace(marker, item + "\n    " + marker)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--mp3", required=True, help="Local path to MP3 file")
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--duration", default="7:00")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO")
    if not token or not repo:
        print("ERROR: Set GITHUB_TOKEN and GITHUB_REPO environment variables.")
        sys.exit(1)

    username = repo.split("/")[0]
    repo_name = repo.split("/")[1]
    base_url = f"https://{username}.github.io/{repo_name}"

    # 1. Upload MP3
    mp3_filename = os.path.basename(args.mp3)
    mp3_path_in_repo = f"episodes/{mp3_filename}"
    mp3_url = f"{base_url}/{mp3_path_in_repo}"

    with open(args.mp3, "rb") as f:
        mp3_bytes = f.read()
    mp3_size = len(mp3_bytes)

    print(f"Uploading MP3 ({mp3_size // 1024} KB) → {mp3_path_in_repo} ...")
    existing_sha, _ = get_file_sha(token, repo, mp3_path_in_repo)
    upload_file(token, repo, mp3_path_in_repo, mp3_bytes,
                f"Add episode {args.date}", sha=existing_sha)
    print("  ✓ MP3 uploaded")

    # 2. Update feed.xml
    print("Updating feed.xml ...")
    feed_sha, feed_content = get_file_sha(token, repo, "feed.xml")
    if feed_content is None:
        print("ERROR: feed.xml not found in repo. Did you push the initial setup?")
        sys.exit(1)

    new_feed = inject_episode(
        feed_content, args.date, args.title, args.summary,
        mp3_url, mp3_size, args.duration
    )
    upload_file(token, repo, "feed.xml", new_feed.encode(),
                f"Add episode {args.date} to feed", sha=feed_sha)
    print("  ✓ feed.xml updated")

    print(f"\nDone! Feed URL: {base_url}/feed.xml")


if __name__ == "__main__":
    main()
