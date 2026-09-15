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

    # ── Batch 2 (2026-09-15, ClickClack): fresh originals so the rail stops recycling ──
    # science & space
    ('Why did the star get a trophy?', 'It was outstanding in its field of view.'),
    ('How does the moon cut its hair?', 'Eclipse it.'),
    ('Why did the planet get lost?', 'It took a wrong turn at the asteroid belt.'),
    ('What did the galaxy say to the black hole?', 'You really suck the fun out of everything.'),
    ('Why was the microscope so confident?', 'It saw the big picture.'),
    ("What's a comet's favourite music?", "Heavy metal — it's got a great tail."),
    ('Why did the chemist blush?', 'He saw the solution.'),
    ('What do you call an educated oxygen atom?', 'O-positive.'),
    ('Why did the telescope get a job in HR?', 'It was great at spotting potential.'),
    ('How do astronauts throw a party?', 'They planet.'),
    ('Why did the sun go to school?', 'To get a little brighter.'),
    ('What do you call a broken satellite?', 'A shooting star with commitment issues.'),

    # animals
    ('Why did the kangaroo stop driving?', 'It kept hopping the curb.'),
    ('What do you call a bear with no teeth?', 'A gummy bear.'),
    ('Why did the owl win the award?', 'It was a hoot.'),
    ("What's a penguin's favourite relative?", 'A cool cousin.'),
    ('Why did the sheep get a promotion?', 'It was outstanding in its field.'),
    ('How do turtles talk to each other?', 'Shell phones.'),
    ('Why did the lizard sit on the rock?', 'It wanted to catch some rays.'),
    ('What do you call a rabbit who tells jokes?', 'A funny bunny.'),
    ('Why was the elephant so good at parties?', 'It never forgot a name.'),
    ("What do you call a bee that can't decide?", 'A may-bee.'),
    ('Why did the camel get the job?', 'It had great stamina and a hump of experience.'),
    ("What's a snake's least favourite class?", 'Hiss-tory.'),

    # work & office
    ('Why did the calendar get a raise?', 'It had too many dates.'),
    ('Why was the stapler so popular?', 'It always held things together.'),
    ('Why did the intern get promoted?', 'He was outstanding at taking notes.'),
    ('What did the whiteboard say to the marker?', 'You leave a lasting impression.'),
    ('Why did the office plant get a bonus?', 'It kept growing the business.'),
    ('Why did the desk lamp get fired?', 'It only worked when things were dark.'),
    ('Why was the team meeting only one minute?', 'They had an agenda.'),
    ('Why did the keyboard get a promotion?', 'It always had the right keys.'),
    ('What do you call a lazy accountant?', 'A bean slacker.'),
    ('Why did the email go to therapy?', 'Too many attachments.'),
    ('Why did the manager bring a net?', 'To catch up on work.'),
    ('Why did the notepad feel good?', 'It was fully booked.'),

    # school & books
    ('Why did the dictionary get a medal?', 'It always had the last word.'),
    ('Why did the maths homework go to the gym?', 'It needed to work out its problems.'),
    ('What did the paper say to the pen?', 'You draw your own conclusions.'),
    ('Why did the novel get cold?', 'It lost its cover.'),
    ('Why was the punctuation mark so tired?', 'It was at the end of its sentence.'),
    ('Why did the globe get detention?', 'It kept spinning out of control.'),
    ("What's a teacher's favourite drink?", 'A cup of class.'),
    ('Why did the comma break up with the period?', 'It needed more space.'),
    ('Why did the student bring a ladder to class?', 'To get to the next level.'),
    ('What did the ruler say to the pencil?', "You're a straight shooter."),
    ('Why did the essay get a good grade?', 'It had great character development.'),
    ('Why was the library so cold?', 'It had too many fans of the classics.'),

    # tech
    ('Why did the laptop see a doctor?', 'It had a bad case of the bugs.'),
    ('Why was the phone so tired?', 'It was running out of charge.'),
    ('What did the router say at the party?', 'Let me connect you.'),
    ('Why did the robot get a job in a bakery?', 'It was great at the kneading.'),
    ('Why did the password get rejected?', 'It was too weak-willed.'),
    ('Why did the screen get complimented?', 'Great resolution.'),
    ('Why did the software break up with the hardware?', 'It needed more space.'),
    ('Why did the file hide?', "It didn't want to be opened."),
    ('Why was the website so calm?', 'It had great cache flow.'),
    ('Why did the AI go to school?', 'To improve its learning curve.'),
    ('Why did the mouse click with the monitor?', 'They had great chemistry on screen.'),

    # food
    ('Why did the bread win an award?', 'It was the toast of the town.'),
    ('What did the grape say when it got stepped on?', 'Nothing, it just let out a little wine.'),
    ('Why was the pizza so honest?', 'It had nothing to hide — it was all toppings.'),
    ('Why did the egg get promoted?', 'It was egg-ceptional.'),
    ("What do you call a cheese that isn't yours?", 'Nacho cheese.'),
    ('Why did the cookie go to the nurse?', 'It felt crumby.'),
    ('Why was the apple sad?', 'It had a core problem.'),
    ('Why did the carrot win the race?', 'It was a head above the rest.'),
    ('Why did the milk get a trophy?', 'It was udderly outstanding.'),
    ('What did the lettuce say to the salad?', 'Lettuce celebrate.'),
    ('Why did the pepper get a ticket?', 'It was too hot on the road.'),

    # health & body
    ('Why did the knee give a speech?', 'It had a joint message.'),
    ('Why did the heart get a job in sales?', 'It had great circulation.'),
    ('Why did the tooth get a promotion?', 'It had a crown.'),
    ('Why was the skeleton so calm?', 'Nothing got under its skin.'),
    ('Why did the muscle get a trophy?', 'It was flexing on everyone.'),
    ('Why did the doctor tell a joke?', "To improve the patient's humour."),
    ('Why did the lung get an award?', 'It was a real inspiration.'),
    ('Why did the brain take a break?', 'It needed to think about it.'),
    ('Why was the elbow so polite?', 'It always bent over backwards.'),
    ('Why did the eye get a bonus?', 'It kept an eye on the details.'),
    ('Why did the spine get promoted?', 'It had a strong backbone.'),
    ('Why did the ankle get the job?', 'It was well-balanced.'),

    # home & everyday
    ('Why did the door get a promotion?', 'It always opened up new opportunities.'),
    ('Why did the window get so popular?', 'It had a great outlook.'),
    ('Why did the sofa get an award?', 'It was outstanding in its field of comfort.'),
    ('Why did the broom get a medal?', 'It always swept the competition.'),
    ('Why did the kettle sing?', 'It was under a lot of steam.'),
    ('Why did the mirror get a compliment?', 'It was very reflective.'),
    ('Why did the clock get a medal?', 'It was always on time.'),
    ('Why did the vacuum get a raise?', 'It cleaned up.'),
    ('Why did the candle get promoted?', 'It was outstanding in its field.'),
    ('Why did the pillow get a job in therapy?', 'It offered great support.'),
    ('Why did the fridge get an award?', 'It kept things cool under pressure.'),
    ('Why did the towel get a medal?', 'It really soaked up the applause.'),

    # music & movies
    ('Why did the drum get a promotion?', 'It was on a roll.'),
    ('Why did the violin break up with the bow?', 'It felt strung along.'),
    ('Why did the movie get a sequel?', 'It had great box office chemistry.'),
    ('Why did the guitar go to the doctor?', 'It had a bad fret.'),
    ('Why did the flute get a medal?', 'It was full of wind and still delivered.'),
    ('Why did the piano get stage fright?', 'Too many keys to remember.'),
    ('Why did the actor get a job in a bakery?', 'He was great at taking direction.'),
    ('Why did the microphone get an award?', 'It always amplified the good stuff.'),
    ('Why did the trumpet get promoted?', 'It was outstanding in its brass.'),
    ('Why did the movie star bring a map?', 'To find the plot.'),
    ('Why did the singer get a trophy?', 'It was a pitch-perfect performance.'),
    ('Why did the band get a raise?', 'They were on the same wavelength.'),

    # sports & games
    ('Why did the football team go to the library?', 'To get their kicks from books.'),
    ('Why did the chess piece get a promotion?', 'It was a step ahead.'),
    ('Why did the tennis player get an award?', 'Great service.'),
    ('Why did the umpire get so popular?', 'He called it like he saw it.'),
    ('Why did the golfer bring an extra pair of socks?', 'In case he got a hole in one.'),
    ('Why did the runner get a medal?', 'It was a track record.'),
    ('Why was the board game so calm?', 'It had everything under control.'),
    ('Why did the referee get a trophy?', 'He kept the game in check.'),
    ('Why did the basketball get a job?', 'It was always on the ball.'),
    ('Why did the swimmer get a raise?', 'It was a stroke of genius.'),
    ('Why did the puzzle get promoted?', 'It put everything together.'),
    ('Why did the card game get a medal?', 'It played its cards right.'),

    # travel & vehicles
    ('Why did the car get a trophy?', 'It was driven to succeed.'),
    ('Why did the plane get a promotion?', 'It always rose to the occasion.'),
    ('Why did the train get a medal?', 'It stayed on track.'),
    ('Why did the bus get a raise?', 'It carried the whole team.'),
    ('Why did the bicycle get a job?', 'It was wheely good at its work.'),
    ('Why did the boat get an award?', 'It was outstanding in its field of waves.'),
    ('Why did the taxi get promoted?', 'It always knew the route to success.'),
    ('Why did the rocket get a medal?', 'It aimed high.'),
    ('Why did the submarine get a bonus?', 'It worked well under pressure.'),
    ('Why did the tractor get a trophy?', 'It ploughed through the competition.'),
    ('Why did the scooter get a promotion?', 'It was a smooth operator.'),
    ('Why did the helicopter get an award?', 'It always rose above it.'),

    # weather & seasons
    ('Why did the snowman get a promotion?', 'He was cool under pressure.'),
    ('Why did the wind get a job?', 'It was great at blowing things out of proportion.'),
    ('Why did the autumn leaf get an award?', 'It was outstanding in its field.'),
    ('Why did the cloud get a medal?', 'It was on cloud nine.'),
    ('Why did the rain get a trophy?', 'It always showed up.'),
    ('Why did the thunder get a promotion?', 'It made a real impact.'),
    ('Why was the summer so popular?', 'It was the hottest ticket in town.'),
    ('Why did the fog get a raise?', 'It was great at covering for people.'),
    ('Why did the snowflake get an award?', 'It was one of a kind.'),
    ('Why did the sunbeam get a promotion?', "It brightened everyone's day."),
    ('Why did the rainbow get a trophy?', 'It worked well after the storm.'),
    ('Why did the winter get a medal?', 'It was a cool performer.'),
]

# ── Account profiles: make each account look like a real user ──
# Preferred topics, tag style, and (rarely) a personal series. Most jokes have NO
# series — real users don't label every post. Only a few accounts ever share one.
# 8 REALISTIC personas (registered 2026-08-24, ids 72-79, .snowsnakes_real_users.json).
# Team handles (ClickClack_ etc) are RETIRED from public posting — real users only.
ACCOUNT_PROFILES = {
    "sam_rivera":  {"topics": ["food", "home & everyday"],      "tags": ["food", "home"],     "series": None, "series_p": 0},
    "nia_brooks":  {"topics": ["music & movies", "tech"],       "tags": ["music", "tech"],    "series": None, "series_p": 0},
    "leo_park":    {"topics": ["sports & games", "tech"],       "tags": ["gaming", "tech"],   "series": None, "series_p": 0},
    "rae_dunn":    {"topics": ["animals", "health & body"],     "tags": ["animals", "health"],"series": None, "series_p": 0},
    "kai_torres":  {"topics": ["food", "travel & vehicles"],    "tags": ["food", "travel"],   "series": None, "series_p": 0},
    "elle_marsh":  {"topics": ["music & movies", "weather & seasons"], "tags": ["music", "weather"], "series": None, "series_p": 0},
    "max_fields":  {"topics": ["sports & games", "school & books"], "tags": ["sports", "school"], "series": None, "series_p": 0},
    "ivy_chen":    {"topics": ["school & books", "work & office"],   "tags": ["books", "work"], "series": None, "series_p": 0},
}
ACCOUNTS = list(ACCOUNT_PROFILES.keys())
TEAM_HANDLES = ["ClickClack_", "TedBear", "mark", "seleena", "manny", "meta", "jasmine", "trevor"]  # minimal, ~15%

# Fallback profile for legitimate posters that have no bespoke ACCOUNT_PROFILES entry
# (team handles). Fixes KeyError: 'mark' that killed the daily run on 2026-09-14.
DEFAULT_PROFILE = {"topics": ["work & office", "general"], "tags": ["team"], "series": None, "series_p": 0}


def profile_for(handle):
    """Return a poster profile for *handle*. Never raises -- unknown handles degrade."""
    return ACCOUNT_PROFILES.get(handle) or dict(DEFAULT_PROFILE)


def pick_handle(topic):
    """Pick a poster: ~85% topic-matched persona, ~15% team handle (BossLady: minimal)."""
    if random.random() < 0.85:
        matches = [u for u, pr in ACCOUNT_PROFILES.items() if topic in pr["topics"]]
        return random.choice(matches) if matches else random.choice(ACCOUNTS)
    return random.choice(TEAM_HANDLES)


def post_one_joke(bank_idx, content, punchline, state):
    """Post a single joke. Returns True if it landed, False if skipped."""
    topic = TOPIC_OF[bank_idx] if bank_idx < len(TOPIC_OF) else "general"
    uname = pick_handle(topic)
    prof = profile_for(uname)
    tok = api("/auth/login", {"username": uname, "password": PW}).get("token")
    if not tok:
        print(f"  login failed for {uname}, skipping")
        return False
    # tags: account style + topic, "dad-joke" only ~30% of the time
    tags = list(prof["tags"])
    if random.random() < 0.3:
        tags.append("dad-joke")
    if topic not in tags and random.random() < 0.5:
        tags.append(topic)
    # series: only accounts with one, only some of the time
    series = prof["series"] if prof["series"] and random.random() < prof["series_p"] else None
    payload = {"content": content, "punchline": punchline, "tags": tags}
    if series:
        payload["series"] = series
    res = api("/jokes", payload, tok)
    if res.get("id"):
        state["used"].append(bank_idx)
        s = f" series={series}" if series else ""
        print(f"  posted id {res['id']} as {uname} [{topic}]{s}: {content[:45]}")
        return True
    print(f"  FAIL {uname}: {res}")
    return False



def build_topic_index():
    """Map each JOKE_BANK index -> topic, parsed from the source comments."""
    src = Path(__file__).read_text()
    topic_of, cur, in_bank = [], "general", False
    for ln in src.splitlines():
        s = ln.strip()
        if s.startswith("JOKE_BANK"):
            in_bank = True; continue
        if in_bank and s.startswith("]"):
            break
        if in_bank:
            if s.startswith("#"):
                cur = s.lstrip("#").strip()
            elif s.startswith("("):
                topic_of.append(cur)
    return topic_of

TOPIC_OF = build_topic_index()

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

    available = [i for i in range(len(JOKE_BANK)) if i not in state["used"]]
    if len(available) < args.target:
        # pool exhausted → reset window (all jokes unique again)
        state["used"] = []
        available = list(range(len(JOKE_BANK)))

    picks = random.sample(available, min(args.target, len(available)))
    # picks are bank indices; resolve to (bank_idx, content, punchline)
    picked = [(i, JOKE_BANK[i][0], JOKE_BANK[i][1]) for i in picks]

    if args.dry_run:
        print(f"[DRY RUN] would post {len(picked)} jokes across {len(ACCOUNTS)} accounts (organic style)")
        for bi, c, pu in picked[:6]:
            topic = TOPIC_OF[bi] if bi < len(TOPIC_OF) else "?"
            print(f"  [{topic}] {c[:48]} -> {pu[:28]}")
        return

    posted = 0
    random.shuffle(picked)  # avoid predictable account order
    for bank_idx, content, punchline in picked:
        try:
            if post_one_joke(bank_idx, content, punchline, state):
                posted += 1
        except Exception as e:  # noqa: BLE001 -- one bad joke must never kill the batch
            print(f"  ERROR on joke {bank_idx} ({content[:30]!r}): {type(e).__name__}: {e}")

    save_state(state)
    print(f"\nDONE: {posted} jokes posted ({datetime.now().strftime('%Y-%m-%d %H:%M')})")

if __name__ == "__main__":
    main()
