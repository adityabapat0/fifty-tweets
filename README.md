# Daily Twitter Digest

Your personal daily Twitter feed — refreshes every night at midnight IST.

## Project Structure

```
digest/
├── app.py               # Flask app with scheduler
├── requirements.txt     # Python dependencies
├── Procfile             # For Railway/Render
├── secretkeys.env       # Your secrets (never commit this!)
└── templates/
    └── index.html       # Frontend
```

## Run Locally

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

## Deploy to Railway (Free)

1. Go to https://railway.app and sign up
2. Click **New Project → Deploy from GitHub repo**
   - Push this folder to a GitHub repo first (make sure secretkeys.env is in .gitignore!)
3. Once deployed, go to **Variables** tab and add:
   ```
   API_KEY        = your_apitwitter_key
   TWITTER_COOKIE = ct0=...;auth_token=...
   PROXY          = http://user:pass@host:port
   ```
4. Railway auto-detects the Procfile and runs gunicorn

Your site will be live at a `.railway.app` URL instantly.

## How it works

- On first startup, tweets are fetched and saved to `tweet_cache.json`
- Every night at **12:00 AM IST**, the scheduler fetches fresh tweets and updates the cache
- Manual refreshes just serve the cached tweets — no new API calls
- The page shows a countdown to the next refresh

## .gitignore

Create a `.gitignore` file with:
```
secretkeys.env
tweet_cache.json
__pycache__/
*.pyc
.env
```
