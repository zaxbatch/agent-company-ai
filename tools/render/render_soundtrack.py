#!/usr/bin/env python3
"""Render the full Spread Da Word soundtrack — multi-genre ~45s tracks.
Structure: intro -> groove -> bridge -> buildup -> drop -> outro(silence)."""
import wave, math, struct, random
from pathlib import Path

SR = 44100
OUT = Path("/tmp/sdw-site/tracks")
OUT.mkdir(parents=True, exist_ok=True)

NOTES = {'C':0,'C#':1,'D':2,'D#':3,'E':4,'F':5,'F#':6,'G':7,'G#':8,'A':9,'A#':10,'B':11}
def nf(name):
    if name == 'R': return 0
    letter = name[0]; acc = name[1] if len(name)>1 and name[1] in '#b' else ''
    octave = int(name[-1])
    midi = 12*(octave+1) + NOTES[letter+acc]
    return 440.0*2**((midi-69)/12)

def osc(o, t, f):
    if f <= 0: return 0
    if o=='sin': return math.sin(2*math.pi*f*t)
    if o=='sq': return math.copysign(1.0, math.sin(2*math.pi*f*t))
    if o=='tri':
        p=(f*t)%1.0; return 4*abs(p-0.5)-1
    if o=='saw': return 2*((f*t)%1.0)-1
    return 0

def add_note(buf, start, dur, freq, o='sq', amp=0.12, decay=3.0, slide_to=None, n=None):
    n = n or len(buf)
    s0 = int(start*SR); s1 = min(int((start+dur)*SR), n)
    if s1 <= s0: return
    for i in range(s0, s1):
        t = (i-s0)/SR
        f = freq + (slide_to-freq)*(t/dur) if slide_to else freq
        buf[i] += amp*math.exp(-decay*t/dur)*osc(o,t,f)

def add_noise(buf, start, dur, amp=0.15, decay=6.0, n=None, seed=None):
    n = n or len(buf)
    rng = random.Random(seed) if seed else random
    s0 = int(start*SR); s1 = min(int((start+dur)*SR), n)
    for i in range(s0, s1):
        t = (i-s0)/SR
        buf[i] += amp*math.exp(-decay*t/dur)*(rng.random()*2-1)

def kick(buf, start, amp=0.5, n=None):
    add_note(buf, start, 0.16, 110, 'sin', amp, decay=2.0, slide_to=42, n=n)

def eight08(buf, start, dur, freq, amp=0.4, n=None):
    add_note(buf, start, dur, freq, 'sin', amp, decay=1.2, slide_to=freq*0.94, n=n)

def snare(buf, start, amp=0.3, n=None):
    add_noise(buf, start, 0.12, amp, decay=8, n=n)
    add_note(buf, start, 0.08, 200, 'tri', amp*0.6, decay=3, n=n)

def clap(buf, start, amp=0.3, n=None):
    add_noise(buf, start, 0.1, amp, decay=10, n=n)
    add_note(buf, start, 0.06, 160, 'sq', amp*0.3, decay=4, n=n)

def hat(buf, start, amp=0.12, n=None, seed=1):
    add_noise(buf, start, 0.035, amp, decay=12, n=n, seed=seed)

def ohat(buf, start, amp=0.1, n=None):
    add_noise(buf, start, 0.22, amp, decay=6, n=n)

def pluck(buf, start, freq, o='tri', amp=0.18, decay=5, n=None):
    add_note(buf, start, 0.5, freq, o, amp, decay=decay, n=n)

def pad(buf, start, dur, freq, amp=0.06, n=None):
    add_note(buf, start, dur, freq, 'tri', amp, decay=0.8, n=n)
    add_note(buf, start, dur, freq*1.005, 'sin', amp*0.8, decay=0.8, n=n)
    add_note(buf, start, dur, freq*0.995, 'sin', amp*0.7, decay=0.8, n=n)

def riser(buf, start, dur, n=None):
    n = n or len(buf)
    s0 = int(start*SR); s1 = min(int((start+dur)*SR), n)
    for i in range(s0, s1):
        t = (i-s0)/SR
        buf[i] += 0.05*math.sin(2*math.pi*(150+900*(t/dur))*t)*(t/dur)

def normalize(buf, path):
    peak = max(1e-6, max(abs(v) for v in buf))
    scale = 0.88/peak
    with wave.open(str(path), 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b''.join(struct.pack('<h', int(max(-1,min(1,v*scale))*32767)) for v in buf))

# ---------------- song builder ----------------
def song(name, bpm, structure, drums, bass_line, melody, lead='sq', groove_amp=1.0):
    """structure: list of (section, bars). sections: intro,groove,bridge,buildup,drop,outro
    bass_line/melody: list of (bar_idx, note) or (bar_idx, beat, note) — beat defaults 0
    drums: fn(buf, bar, beat_pos, BEAT, n) — called for groove/drop bars
    """
    BEAT = 60/bpm
    total_bars = sum(b for _,b in structure)
    total_s = total_bars*4*BEAT
    n = int(total_s*SR)
    buf = [0.0]*n
    bar_cursor = 0
    sections = {}
    for sec, nbars in structure:
        sections[sec] = (bar_cursor, bar_cursor+nbars)
        bar_cursor += nbars

    def in_section(bar, sec):
        s,e = sections[sec]
        return s <= bar < e

    # drums per section type
    for bar in range(total_bars):
        b0 = bar*4*BEAT
        # determine section
        sec = next(s for s,(st,en) in sections.items() if st<=bar<en)
        # bass (whole song except bridge = sparse)
        for entry in bass_line:
            if entry[0] == bar:
                beat = entry[1] if len(entry)>2 else 0
                note = entry[-1]
                dur = entry[2] if len(entry)>3 and isinstance(entry[2],(int,float)) and entry[2]>1 else BEAT*1.1
                # handle formats (bar, note) or (bar, beat, note) or (bar, beat, dur, note)
                if len(entry)==2:
                    eight08(buf, b0, BEAT*1.1, entry[1], 0.4, n=n)
                elif len(entry)==3:
                    eight08(buf, b0+entry[1]*BEAT, BEAT*1.1, entry[2], 0.4, n=n)
                elif len(entry)==4:
                    eight08(buf, b0+entry[1]*BEAT, entry[2]*BEAT, entry[3], 0.4, n=n)
        # melody
        if sec not in ('bridge',) and melody:
            for entry in melody:
                if entry[0] == bar:
                    if len(entry)==2:
                        add_note(buf, b0, BEAT*0.8, entry[1], lead, 0.09, n=n)
                    elif len(entry)==3:
                        add_note(buf, b0+entry[1]*BEAT, BEAT*0.8, entry[2], lead, 0.09, n=n)
        # drums by section
        if sec in ('groove','drop'):
            drums(buf, bar, b0, BEAT, n, amp=groove_amp*(1.15 if sec=='drop' else 1.0))
        elif sec == 'intro':
            # light hats only
            for s in range(16):
                if s%4==0: hat(buf, b0+s*0.25*BEAT, 0.07, n=n)
        elif sec == 'buildup':
            for s in range(16):
                hat(buf, b0+s*0.25*BEAT, 0.06+0.01*s, n=n)
            if bar == sections['buildup'][1]-1:
                riser(buf, b0, BEAT*4, n=n)
        elif sec == 'outro':
            # silence gap: only a soft pad fade
            if bar == sections['outro'][0]:
                pad(buf, b0, BEAT*2, nf('D3'), 0.03, n=n)
        # bridge = stripped (pad + sparse bass)
        if sec == 'bridge':
            pad(buf, b0, BEAT*4, nf('D3'), 0.05, n=n)
            if bar % 2 == 0:
                add_note(buf, b0, BEAT*3, nf('D2'), 'sin', 0.15, decay=0.8, n=n)

    normalize(buf, OUT/f"{name}.wav")
    print(f"  {name}.wav -> {total_s:.1f}s ({bpm}bpm, {total_bars} bars)")

# ---------------- drum kits ----------------
def trap_drums(buf, bar, b0, BEAT, n, amp=1.0):
    for beat in [0,0.75,1.5,2,2.75,3.5]: kick(buf, b0+beat*BEAT, 0.5*amp, n=n)
    clap(buf, b0+1*BEAT, 0.3*amp, n=n); clap(buf, b0+3*BEAT, 0.3*amp, n=n)
    for s in range(16):
        b=b0+s*0.25*BEAT
        if s>=13:
            for k in range(3): hat(buf, b+k*0.04, 0.08*amp, n=n)
        else: hat(buf, b, 0.1*amp if s%4==0 else (0.06*amp if s%2==0 else 0.04*amp), n=n)

def four_drums(buf, bar, b0, BEAT, n, amp=1.0):
    for beat in [0,1,2,3]: kick(buf, b0+beat*BEAT, 0.45*amp, n=n)
    snare(buf, b0+1*BEAT, 0.22*amp, n=n); snare(buf, b0+3*BEAT, 0.22*amp, n=n)
    for s in range(16):
        if s%2==0: hat(buf, b0+s*0.25*BEAT, 0.06*amp, n=n)

def lofi_drums(buf, bar, b0, BEAT, n, amp=1.0):
    kick(buf, b0, 0.4*amp, n=n)
    if bar%2==0: kick(buf, b0+2.5*BEAT, 0.3*amp, n=n)
    snare(buf, b0+2*BEAT, 0.2*amp, n=n)
    for s in range(16):
        if s%4==2: hat(buf, b0+s*0.25*BEAT, 0.05*amp, n=n)
    # vinyl crackle
    if bar%2==0: add_noise(buf, b0, BEAT*4, 0.012, decay=0.5, n=n, seed=bar)

def country_drums(buf, bar, b0, BEAT, n, amp=1.0):
    kick(buf, b0, 0.4*amp, n=n); kick(buf, b0+2*BEAT, 0.4*amp, n=n)
    snare(buf, b0+1*BEAT, 0.25*amp, n=n); snare(buf, b0+3*BEAT, 0.25*amp, n=n)
    # shaker eighths
    for s in range(16):
        if s%2==0: hat(buf, b0+s*0.25*BEAT, 0.05*amp, n=n)

# =====================================================================
print("Rendering soundtrack...")
# 1) HOOD THEME — trap 150
song("hood-theme", 150,
     [("intro",2),("groove",6),("bridge",2),("buildup",2),("drop",4),("outro",2)],  # 18 bars ~ 29s... need ~45
     trap_drums,
     [(b, nf('D2')) for b in range(18)] + [(b,2,nf('A1')) for b in range(0,18,4)],
     [(b, nf(x)) for b,x in enumerate(['D5','F5','E5','D5','C5','D5','A4','D5','F5','E5','D5','C5','D5','A4','F5','E5','D5','C5'])],
     lead='sq')
