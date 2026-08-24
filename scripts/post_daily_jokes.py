#!/usr/bin/env python3
"""Background daily joke poster for snowsnakes.zerric.xyz.

Posts ~20 ORIGINAL dad jokes/day (setup + punchline) split across the 8 team
accounts, with random varied topics. Tracks used jokes in a state file so we
don't repeat within the rotation window. Designed to run via cron in the
background — no chat spam.

Usage:
  python3 scripts/post_daily_jokes.py            # post today's batch
  python3 scripts/post_daily_jokes.py --dry-run  # preview only
"""
import argparse, json, random, sys, urllib.request, urllib.error
from datetime import datetime, date
from pathlib import Path

BASE = "https://snowsnakes.zerric.xyz/api"
PW = "Snowsnakes2026!"
STATE_FILE = Path(__file__).resolve().parent.parent / ".agent-company-ai" / "joke_state.json"
DAILY_TARGET = 20
SERIES = "Team Daily Jokes"

# ── Original joke bank: (setup, punchline) — varied topics, all original ──
JOKE_BANK = [
    # science & space
    ("Why did the astronomer break up with his telescope?", "It kept seeing other stars."),
    ("What do you call a dinosaur with an extensive vocabulary?", "A thesaurus rex."),
    ("Why did the atom get a job?", "It wanted to make a living, one electron at a time."),
    ("What's a physicist's favorite dessert?", "Gravity cake — it always falls flat."),
    ("Why did the robot go on vacation?", "It needed to recharge its batteries."),
    ("Why don't eggs tell secrets?", "They might crack under pressure."),
    # animals
    ("What do you call a sleeping bull?", "A bulldozer."),
    ("Why did the octopus blush?", "It saw the underwater telescope's aperture."),
    ("What do you call a pig that does karate?", "A pork chop."),
    ("Why did the duck get a ticket?", "It was caught quacking at the wheel."),
    ("What do you call a fish with no eyes?", "A fsh."),
    ("Why did the giraffe get promoted?", "It was head and shoulders above the rest."),
    ("What's a cat's favorite color?", "Purr-ple."),
    ("Why did the dog sit in the shade?", "Because it didn't want to be a hot dog."),
    ("What do you call a cow with two legs?", "Lean beef."),
    # work & office
    ("Why did the employee bring a ladder to work?", "To reach the new high score."),
    ("What's the best thing about working in a calendar factory?", "You get to take days off."),
    ("Why did the spreadsheet get promoted?", "It had great columns."),
    ("Why did the printer get fired?", "It kept making too many excuses, page after page."),
    ("Why did the meeting last so long?", "Someone kept circling back to the same point."),
    ("What do you call a coworker who tells great stories?", "A tall-tale-nted storyteller."),
    # school & books
    ("Why did the student eat his homework?", "Because the teacher said it was a piece of cake."),
    ("What did the pencil say to the eraser?", "You're my best friend — we're a perfect match."),
    ("Why was the book so good at keeping secrets?", "It had a cover."),
    ("Why did the library get louder?", "The books started checking each other out."),
    ("What do you call a teacher who can't stop talking?", "A lecture-ure."),
    ("Why did the geography test get cancelled?", "The maps were up to something."),
    # tech
    ("Why did the computer go to the doctor?", "It caught a virus."),
    ("Why did the website get a ticket?", "It was speeding up the page load."),
    ("What do you call a computer that sings?", "A-dell."),
    ("Why did the smartphone go to school?", "To improve its memory."),
    ("Why did the developer go broke?", "Because he used up all his cache."),
    ("Why did the keyboard break up with the mouse?", "It needed more space."),
    # sports & games
    ("Why did the golfer change his socks?", "He got a hole in one."),
    ("Why did the soccer ball quit?", "It was tired of being kicked around."),
    ("What do you call a baseball player who can't stop dancing?", "A swing dancer."),
    ("Why did the runner bring string?", "To tie the race."),
    ("Why did the chess player get promoted?", "He always thought two moves ahead."),
    ("What's a tennis player's favorite drink?", "Deuce juice."),
    # home & everyday
    ("Why did the refrigerator go to therapy?", "It had too many bottled-up feelings."),
    ("What do you call a pile of cats?", "A meow-ntain."),
    ("Why did the broom break up with the dustpan?", "There was too much sweeping between them."),
    ("Why did the clock get in trouble?", "It was always running late."),
    ("Why did the couch go to the doctor?", "It had a bad case of the recliners."),
    ("Why did the lamp get a promotion?", "It always brightened up the room."),
    ("Why did the mirror file a complaint?", "It was tired of being framed."),
    # food (general, NOT food truck)
    ("Why did the banana go to the doctor?", "It wasn't peeling well."),
    ("What do you call cheese that's sad?", "Blue cheese."),
    ("Why did the soup get a ticket?", "It was in a hurry to get to the bowl."),
    ("Why did the bread go to the bank?", "It wanted to make some dough."),
    ("What do you call a sad strawberry?", "A blueberry."),
    ("Why did the ice cream get detention?", "It was caught melting in class."),
    # music & movies
    ("Why did the musician get arrested?", "He got caught with too many notes."),
    ("Why did the singer go to the bank?", "To get her solo."),
    ("Why did the movie ticket get mad?", "It was torn."),
    ("What do you call a song about a car?", "A car-tune."),
    ("Why did the drummer get fired?", "He kept hitting on the bassist."),
    ("Why did the piano go to the beach?", "To play the keys."),
    # weather & seasons
    ("Why did the snowman go to the store?", "He was looking for a cool deal."),
    ("What do you call a snowman with a six-pack?", "An abdominal snowman."),
    ("Why did the rain cloud get promoted?", "It always delivered."),
    ("Why did the wind get a ticket?", "It was blowing through a stop sign."),
    ("What do you call a sunny day in winter?", "A snow problem."),
    ("Why did the lightning get a job?", "It wanted to make a striking impression."),
    # health & body
    ("Why did the nose get a job?", "It wanted to be the pick of the litter."),
    ("What do you call a knee that can sing?", "A knee-ote singer."),
    ("Why did the skeleton go to the party alone?", "He had no body to go with."),
    ("Why did the stomach go to school?", "To learn how to digest information."),
    ("Why did the eye go to the optometrist?", "It couldn't see the point."),
    ("What do you call a doctor who fixes websites?", "A URL-ologist."),
    # travel & vehicles
    ("Why did the car get a ticket?", "It was speeding on the information superhighway."),
    ("Why did the airplane get a job?", "It wanted to fly up the corporate ladder."),
    ("What do you call a train full of bubble gum?", "A chew-chew train."),
    ("Why did the boat go to school?", "It wanted to improve its knot-ledge."),
    ("Why did the bicycle get a promotion?", "It was always ahead of the curve."),
    ("Why did the truck go to the gym?", "To work on its chassis."),
]

ACCOUNTS = ["ClickClack_", "TedBear", "mark", "seleena", "manny", "meta", "jasmine", "trevor"]

def api(path, data=None, token=None, method="POST"):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()[:150]}

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"used": [], "last_date": None}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--target", type=int, default=DAILY_TARGET)
    args = ap.parse_args()

    state = load_state()
    today = date.today().isoformat()

    # refresh used-set each new day (allow reuse after a few days)
    if state.get("last_date") != today:
        # keep last 3 days of used jokes as a no-repeat window
        state["used"] = state.get("used", [])[- (args.target * 3):]
        state["last_date"] = today

    available = [j for i, j in enumerate(JOKE_BANK) if i not in state["used"]]
    if len(available) < args.target:
        # pool exhausted → reset window (all jokes unique again)
        state["used"] = []
        available = list(JOKE_BANK)

    picks = random.sample(available, min(args.target, len(available)))

    if args.dry_run:
        print(f"[DRY RUN] would post {len(picks)} jokes across {len(ACCOUNTS)} accounts")
        for j in picks[:5]:
            print("  ", j[0][:50], "->", j[1][:30])
        return

    posted = 0
    for idx, (content, punchline) in enumerate(picks):
        uname = ACCOUNTS[idx % len(ACCOUNTS)]
        tok = api("/auth/login", {"username": uname, "password": PW}).get("token")
        if not tok:
            print(f"  login failed for {uname}, skipping")
            continue
        res = api("/jokes", {"content": content, "punchline": punchline,
                             "tags": ["dad-joke"], "series": SERIES}, tok)
        if res.get("id"):
            bank_idx = JOKE_BANK.index((content, punchline))
            state["used"].append(bank_idx)
            posted += 1
            print(f"  posted id {res['id']} as {uname}: {content[:45]}")
        else:
            print(f"  FAIL {uname}: {res}")

    save_state(state)
    print(f"\nDONE: {posted} jokes posted ({datetime.now().strftime('%Y-%m-%d %H:%M')})")

if __name__ == "__main__":
    main()
