#!/usr/bin/env python3
"""Generate the MilkUps anthem "Raised on the Shelves" via udioapi.pro (v2 API).

Reads the API key from communication/credentials.txt (never prints/commits it).
Pre-flights the credit balance and aborts early if there aren't enough credits.

API reference (verified 2026-08-30 from https://udioapi.pro/docs):
  - POST /api/v2/generate   (Bearer auth; custom mode: prompt/style/title)
  - GET  /api/v2/feed?workId=xxx  (poll every 5-10s until type SUCCESS)
  - GET  /api/v2/credits    (credits left on the key)
  - Credit cost: chirp-v3-5 = 5, chirp-v4 = 8, chirp-v4-5 = 10, chirp-v5/v5-5 = 12
  - 402 = "account does not have enough credits" -> top up at udioapi.pro dashboard

Usage:
  venv/bin/python scripts/milkups_udio_song.py [--model chirp-v3-5|chirp-v5-5] [--check-credits]
"""
import re, json, os, sys, time, argparse, urllib.request, urllib.parse

ROOT = "/home/zax/Biz/z-dot-team"
CREDS = os.path.join(ROOT, "communication", "credentials.txt")
OUT_DIR = os.path.join(ROOT, "content", "milkups", "assets")
LOG_DIR = os.path.join(ROOT, "logs")
BASE = "https://udioapi.pro/api"

# credit cost per model (from udioapi.pro docs, Credit Consumption by Model)
MODEL_COST = {"chirp-v3-5": 5, "chirp-v4": 8, "chirp-v4-5": 10,
              "chirp-v4-5-plus": 10, "chirp-v5": 12, "chirp-v5-5": 12}

TITLE = "Raised on the Shelves"
STYLE = ("80s retro synthwave, neon night drive, analog synth arpeggios, driving bassline, "
         "gated reverb drums, dreamy synth pop vocals, cinematic, energetic, nostalgic")
LYRICS = """[Verse 1]
Midnight at the corner store, neon hum and open door
Crack of dawn, a silver carton, cold light from the start
They stacked us high, row by row, every shelf a place to go
Took the chill into our soul, made us ready for the road

[Chorus]
We were raised on the shelves, cold vibes all the way
Fresh beats in our blood, we were born to play
Straight from the cab-nets, never going back
Turn the tape up loud, we're the MilkUps attack

[Verse 2]
Vin and Que on the boulevard, synths igniting after dark
Spread the word across the night, every speaker burning bright
Milk-white moon above the street, every shadow keeps the beat
From the dairy to the stage, we were written on this page

[Chorus]
We were raised on the shelves, cold vibes all the way
Fresh beats in our blood, we were born to play
Straight from the cab-nets, never going back
Turn the tape up loud, we're the MilkUps attack

[Bridge]
Chill like the carton, cold as the frost
Every beat we carry, nothing ever lost
Shelves to the stars, we came up from below
Raised on the cold, and that's how we glow

[Chorus]
We were raised on the shelves, cold vibes all the way
Fresh beats in our blood, we were born to play
Straight from the cab-nets, never going back
Turn the tape up loud, we're the MilkUps attack

[Outro]
Raised on the shelves... cold vibes forever..."""


def load_key():
    txt = open(CREDS).read()
    m = re.search(r"udioapi\.pro\s*\n(sk-[A-Za-z0-9]+)", txt)
    if not m:
        sys.exit("KEY NOT FOUND in credentials.txt (expected 'udioapi.pro' then 'sk-...' line)")
    return m.group(1)


def api(path, payload=None, method=None):
    """Call udioapi.pro with Bearer auth. Returns parsed JSON or raises."""
    headers = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json",
               "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
    url = BASE + path
    if payload is not None:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers, method=method or "POST")
    else:
        req = urllib.request.Request(url, headers=headers, method=method or "GET")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return json.loads(body)
        except Exception:
            return {"code": e.code, "message": body[:300]}


def check_credits(model):
    r = api("/v2/credits")
    bal = (r.get("data") or {}).get("credits", -1)
    need = MODEL_COST.get(model, 12)
    print(f"[credits] balance={bal}  model={model}  cost={need}")
    return bal, need


def generate(model):
    payload = {
        "model": model,
        "prompt": LYRICS,
        "style": STYLE,
        "title": TITLE,
        "make_instrumental": False,
        "gender": "male",
        "duration": 180,  # chirp-v5-5 custom mode target seconds (docs: 10-360)
    }
    print(f"Submitting {model} generation for '{TITLE}' ...")
    r = api("/v2/generate", payload)
    work_id = r.get("workId") or (r.get("data") or {}).get("task_id")
    if not work_id:
        print("GENERATE FAILED:", json.dumps(r)[:600])
        sys.exit(1)
    print("workId:", work_id)
    with open(os.path.join(LOG_DIR, "milkups_udio_gen.json"), "w") as f:
        json.dump({"workId": work_id, "title": TITLE, "model": model, "style": STYLE,
                   "lyrics": LYRICS, "submitted_ts": int(time.time())}, f, indent=2)
    return work_id


def poll(work_id, timeout=900):
    """Poll /v2/feed until SUCCESS or fail_message. Returns response_data list."""
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        time.sleep(8)
        try:
            st = api("/v2/feed?" + urllib.parse.urlencode({"workId": work_id}))
        except Exception as e:
            print("poll error:", e); continue
        d = st.get("data") or {}
        typ = d.get("type", "?")
        msg = json.dumps(d)[:220]
        if msg != last:
            print(f"[{typ}] {msg}")
            last = msg
        fm = d.get("fail_message") or ""
        if fm and fm not in ("", "None"):
            sys.exit("GENERATION FAILED: " + fm)
        em = d.get("error_message") or ""
        if em and em not in ("", "None"):
            sys.exit("GENERATION ERROR: " + em)
        if typ == "SUCCESS" and d.get("response_data"):
            return d["response_data"]
        if d.get("status") == "error":
            sys.exit("GENERATION ERROR STATUS: " + json.dumps(d)[:400])
    sys.exit("TIMEOUT waiting for generation (workId=%s)" % work_id)


def download(tracks):
    os.makedirs(OUT_DIR, exist_ok=True)
    saved = []
    base = TITLE.lower().replace(" ", "-")
    for i, tr in enumerate(tracks):
        au = tr.get("audio_url")
        if not au:
            continue
        fn = os.path.join(OUT_DIR, f"{base}.mp3")
        urllib.request.urlretrieve(au, fn)
        saved.append(fn)
        for imgkey in ("image_large_url", "image_url"):
            img = tr.get(imgkey)
            if img:
                try:
                    imgfn = os.path.join(OUT_DIR, f"{base}-cover.png")
                    urllib.request.urlretrieve(img, imgfn)
                    saved.append(imgfn)
                    break
                except Exception as e:
                    print("img dl err", e)
        print(f"track {i}: {tr.get('title')!r} dur={tr.get('duration')} -> {fn} "
              f"({os.path.getsize(fn)} bytes) model={tr.get('model_name')}")
    return saved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="chirp-v5-5", choices=list(MODEL_COST))
    ap.add_argument("--check-credits", action="store_true", help="Only print balance, do not generate")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    global KEY
    KEY = load_key()

    bal, need = check_credits(args.model)
    if args.check_credits:
        print(f"balance={bal} credits, need {need} for {args.model}; "
              f"{'ENOUGH' if bal >= need else 'NOT ENOUGH — top up at udioapi.pro dashboard'}")
        return

    if bal < need:
        print(f"BLOCKED: {bal} credits < {need} needed for {args.model}. "
              f"402 'No credit' expected. Top up at https://udioapi.pro (Basic $10/mo = 1000 cr, "
              f"Pro $20/mo = 2000 cr, or free starter credits on a new account).")
        sys.exit(2)

    work_id = generate(args.model)
    tracks = poll(work_id, timeout=args.timeout)
    saved = download(tracks)
    with open(os.path.join(LOG_DIR, "milkups_udio_result.json"), "w") as f:
        json.dump({"workId": work_id, "saved": saved, "tracks": [
            {k: tr.get(k) for k in ("id", "title", "duration", "audio_url", "image_url",
                                    "image_large_url", "tags", "model_name", "created_at")}
            for tr in tracks]}, f, indent=2)
    print("DONE. saved:", saved)


if __name__ == "__main__":
    main()
