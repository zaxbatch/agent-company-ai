#!/usr/bin/env python3
"""Generate a MilkUps song via udioapi.pro. Key loaded from credentials.txt, never printed."""
import re, json, os, sys, time, urllib.request, urllib.parse

CREDS = "/home/zax/Biz/z-dot-team/communication/credentials.txt"
OUT_DIR = "/home/zax/Biz/z-dot-team/content/milkups/assets"

def load_key():
    txt = open(CREDS).read()
    m = re.search(r"udioapi\.pro\s*\n(sk-[A-Za-z0-9]+)", txt)
    if not m:
        sys.exit("KEY NOT FOUND in credentials.txt")
    return m.group(1)

KEY = load_key()
BASE = "https://udioapi.pro/api"

def post(path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

def get(path, params):
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(BASE + path + "?" + qs, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

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

payload = {
    "prompt": LYRICS,
    "title": TITLE,
    "style": STYLE,
    "custom_mode": True,
    "make_instrumental": False,
    "model": "chirp-v3.5",
    "gpt_description_prompt": "A MilkUps synthwave anthem about being raised on the shelves of a corner store, cold vibes, fresh beats, and the cab-nets. Retro 80s night drive energy, big chorus, dreamy vocals.",
    "cluster": "default",
    "token": KEY,
}

print("Submitting generation...")
resp = post("/generate", payload)
print("GENERATE RESPONSE:", json.dumps({k: v for k, v in resp.items() if k != "token"}, indent=2)[:800])
work_id = resp.get("workId")
if not work_id:
    sys.exit("No workId in response")

print("workId:", work_id)
log = {"workId": work_id, "title": TITLE, "style": STYLE, "lyrics": LYRICS, "submitted_ts": int(time.time())}
with open("/home/zax/Biz/z-dot-team/logs/milkups_udio_gen.json", "w") as f:
    json.dump(log, f, indent=2)

# Poll
deadline = time.time() + 600
last = ""
while time.time() < deadline:
    time.sleep(8)
    try:
        st = get("/feed", {"workId": work_id, "token": KEY})
    except Exception as e:
        print("poll error:", e); continue
    t = st.get("type", "?")
    msg = json.dumps(st)[:200]
    if msg != last:
        print(f"[{t}] {msg}")
        last = msg
    if t == "complete":
        break
    if t == "error":
        sys.exit("GENERATION ERROR: " + json.dumps(st)[:500])
else:
    sys.exit("TIMEOUT waiting for generation")

tracks = st.get("response_data") or st.get("data") or []
if not tracks:
    # sometimes wrapped
    d = st.get("data")
    if isinstance(d, dict):
        tracks = d.get("data") or []
print("TRACKS:", len(tracks))
for i, tr in enumerate(tracks):
    print(f"--- track {i}: title={tr.get('title')} dur={tr.get('duration')} audio={tr.get('audio_url')}")

# Download
os.makedirs(OUT_DIR, exist_ok=True)
saved = []
for i, tr in enumerate(tracks):
    au = tr.get("audio_url")
    if not au: continue
    fn = f"{OUT_DIR}/{TITLE.lower().replace(' ', '-')}.mp3"
    urllib.request.urlretrieve(au, fn)
    saved.append(fn)
    img = tr.get("image_url")
    if img:
        try:
            imgfn = f"{OUT_DIR}/{TITLE.lower().replace(' ', '-')}-cover.png"
            urllib.request.urlretrieve(img, imgfn)
            saved.append(imgfn)
        except Exception as e:
            print("img dl err", e)
    print("saved:", fn, os.path.getsize(fn), "bytes")

with open("/home/zax/Biz/z-dot-team/logs/milkups_udio_result.json", "w") as f:
    json.dump({"workId": work_id, "saved": saved, "tracks": [
        {k: tr.get(k) for k in ("title", "duration", "audio_url", "image_url", "tags", "model_name")} for tr in tracks
    ]}, f, indent=2)

print("DONE. saved:", saved)
