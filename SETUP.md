# SHTG Podcast Feed — One-Time Setup Guide

Follow these steps once. After that, every daily run publishes automatically.

---

## Step 1 — Create the GitHub repo

1. Go to [github.com/new](https://github.com/new)
2. Name it **`shtg-podcast`** (or anything you like — just be consistent below)
3. Set visibility to **Public** (required for free GitHub Pages)
4. Click **Create repository**

---

## Step 2 — Enable GitHub Pages

1. In the new repo, go to **Settings → Pages**
2. Under *Source*, select **Deploy from a branch**
3. Branch: **`main`**, folder: **`/ (root)`**
4. Click **Save**

GitHub Pages URL will be:
```
https://YOUR_GITHUB_USERNAME.github.io/shtg-podcast/
```

---

## Step 3 — Edit feed.xml

Open `feed.xml` from this folder and replace **all four** occurrences of:
```
YOUR_GITHUB_USERNAME
```
with your actual GitHub username (e.g. `eweiss`).

Also update the `<enclosure>` `length=` in the first episode item to match the actual
MP3 file size in bytes (run `wc -c shtg-podcast-2026-04-24.mp3` to get it).

---

## Step 4 — Add a cover image (optional but recommended)

Apple Podcasts requires a square cover image (minimum 1400×1400 px, JPEG or PNG).
Save it as `cover.jpg` in this folder. A simple one with "SHTG Daily" text on a
dark background works fine. If you skip this, the feed will work but won't have
artwork in podcast apps.

---

## Step 5 — Push the initial files to GitHub

```bash
cd /path/to/shtg-podcast-feed

# Initialize and push
git init
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/shtg-podcast.git
git checkout -b main

# Create the episodes folder and copy today's MP3 into it
mkdir -p episodes
cp /path/to/shtg-podcast-2026-04-24.mp3 episodes/

# Commit everything
git add feed.xml episodes/ publish_episode.py cover.jpg   # (cover.jpg if you have one)
git commit -m "Initial podcast feed setup"
git push -u origin main
```

Give GitHub Pages 1–2 minutes to deploy, then verify:
```
https://YOUR_GITHUB_USERNAME.github.io/shtg-podcast/feed.xml
```

---

## Step 6 — Create a GitHub Personal Access Token

The daily task needs permission to push new episodes automatically.

1. Go to **GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens**
2. Click **Generate new token**
3. Set *Repository access* to **Only select repositories → shtg-podcast**
4. Under *Permissions*, give **Contents: Read and write**
5. Click **Generate token** and copy it

Store it in your shell environment (add to `~/.zshrc` or `~/.bashrc`):
```bash
export GITHUB_TOKEN="github_pat_XXXXXXXXXXXX"
export GITHUB_REPO="YOUR_GITHUB_USERNAME/shtg-podcast"
```

---

## Step 7 — Subscribe in your podcast app

**Apple Podcasts (iPhone):**
1. Open Apple Podcasts
2. Tap **Search** → type in the search bar and look for the small "URL" option, or go to the Library tab and tap the `+` in the top-right corner → "Follow a Show by URL"
3. Paste: `https://YOUR_GITHUB_USERNAME.github.io/shtg-podcast/feed.xml`
4. Tap **Subscribe**

**Overcast (recommended — better for science podcasts):**
1. Tap **+** → **Add URL**
2. Paste the feed URL above

**Pocket Casts, Castro, Spotify:** All support custom RSS URLs via "Add by URL" or similar.

---

## How the daily automation works (after setup)

Each morning the scheduled task:
1. Searches PubMed, writes the digest `.md` and podcast `.txt`
2. Generates the `.mp3` via gTTS
3. Calls `publish_episode.py` which uploads the MP3 to `episodes/` and injects a new `<item>` into `feed.xml` via the GitHub API
4. Your podcast app picks up the new episode automatically (usually within minutes)

The task will call publish_episode.py like this:
```bash
python3 /path/to/publish_episode.py \
  --date 2026-04-25 \
  --mp3 /path/to/shtg-podcast-2026-04-25.mp3 \
  --title "SHTG Digest — Saturday April 25, 2026" \
  --summary "One-sentence bottom line from today's search." \
  --duration "7:00"
```

---

## Troubleshooting

- **Feed not loading in Apple Podcasts:** Validate at [castfeedvalidator.com](https://www.castfeedvalidator.com) or [podba.se/validate](https://podba.se/validate)
- **GitHub Pages not serving:** Check Settings → Pages for build errors; make sure the repo is public
- **Token errors:** Regenerate the PAT and re-export `GITHUB_TOKEN`
