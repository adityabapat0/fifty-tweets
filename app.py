from flask import Flask, render_template
import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

load_dotenv('secretkeys.env')

app = Flask(__name__)

CACHE_FILE = 'tweet_cache.json'
IST = pytz.timezone('Asia/Kolkata')


# ── Fetch tweets from API ──────────────────────────────────────────────────

def fetch_tweets(count=50):
    all_tweets = []
    cursor = ""

    while len(all_tweets) < count:
        payload = {
            "cookie": os.getenv("TWITTER_COOKIE"),
            "proxy": os.getenv("PROXY"),
            "count": 20,
            "cursor": cursor,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        }
        headers = {
            "X-API-Key": os.getenv("API_KEY"),
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                "https://api.apitwitter.com/twitter/timeline/latest",
                json=payload,
                headers=headers,
                timeout=15
            )
            data = response.json()
            tweets = data.get('data', {}).get('tweets', [])
            all_tweets.extend(tweets)

            has_next = data.get('data', {}).get('has_next_page', False)
            cursor = data.get('data', {}).get('next_cursor', '')

            if not has_next or not cursor:
                break
        except Exception as e:
            print(f"[fetch error] {e}")
            break

    def parse_date(tweet):
        try:
            return datetime.strptime(tweet['created_at'], "%a %b %d %H:%M:%S +0000 %Y")
        except:
            return datetime.min

    all_tweets.sort(key=parse_date, reverse=True)
    return all_tweets[:count]


# ── Cache helpers ──────────────────────────────────────────────────────────

def save_cache(tweets):
    now_ist = datetime.now(IST).strftime("%B %d, %Y")
    cache = {
        "date": now_ist,
        "fetched_at": datetime.now(IST).isoformat(),
        "tweets": tweets
    }
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)
    print(f"[cache] Saved {len(tweets)} tweets at {cache['fetched_at']}")


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return None
    with open(CACHE_FILE, 'r') as f:
        return json.load(f)


def refresh_tweets():
    print("[scheduler] Fetching new tweets...")
    tweets = fetch_tweets(50)
    if tweets:
        save_cache(tweets)
        print(f"[scheduler] Done. {len(tweets)} tweets cached.")
    else:
        print("[scheduler] No tweets returned.")


# ── Scheduler: runs every night at midnight IST ────────────────────────────

scheduler = BackgroundScheduler(timezone=IST)
scheduler.add_job(refresh_tweets, 'cron', hour=0, minute=0)
scheduler.start()


# ── On startup: fetch if no cache exists ──────────────────────────────────

cache = load_cache()
if not cache:
    print("[startup] No cache found, fetching tweets...")
    refresh_tweets()


# ── Routes ────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    cache = load_cache()
    if cache:
        tweets = cache['tweets']
        date = cache['date']
        fetched_at = cache['fetched_at']
    else:
        tweets = []
        date = datetime.now(IST).strftime("%B %d, %Y")
        fetched_at = None

    # Calculate time until next midnight IST refresh
    now_ist = datetime.now(IST)
    midnight_ist = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    from datetime import timedelta
    next_midnight = midnight_ist + timedelta(days=1)
    diff = next_midnight - now_ist
    hours_left = int(diff.seconds // 3600)
    mins_left = int((diff.seconds % 3600) // 60)
    next_refresh = f"{hours_left}h {mins_left}m"

    return render_template('index.html',
        tweets=tweets,
        date=date,
        next_refresh=next_refresh
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
