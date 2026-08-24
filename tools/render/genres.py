#!/usr/bin/env python3
"""Render 4 genre beats (lo-fi, country, pop, electro) ~45s each + full-length
versions of hood/fridge/battle. All synthesized, bridge+buildup+silence."""
import wave, math, struct, random
from pathlib import Path
SR = 44100
OUT = Path("/tmp/sdw-site/tracks")
OUT.mkdir(parents=True, exist_ok=True)
NOTES = {'C':0,'C#':1,'D':2,'D#':3,'E':4,'F':5,'F#':6,'G':7,'G#':8,'A':9,'A#':10,'B':11}
def nf(n):
    if n=='R': return 0
    l=n[0]; a=n[1] if len(n)>1 and n[1] in '#b' else ''; o=int(n[-1])
    return 440.0*2**((12*(o+1)+NOTES[l+a]-69)/12)
def osc(o,t,f):
    if f<=0: return 0
    if o=='sin': return math.sin(2*math.pi*f*t)
    if o=='sq': return math.copysign(1.0,math.sin(2*math.pi*f*t))
    if o=='tri':
        p=(f*t)%1.0; return 4*abs(p-0.5)-1
    if o=='saw': return 2*((f*t)%1.0)-1
    return 0
def note(buf,st,du,f,o='sq',amp=0.12,dec=3.0,slide=None,n=None):
    n=n or len(buf); s0=int(st*SR); s1=min(int((st+du)*SR),n)
    for i in range(s0,s1):
        t=(i-s0)/SR
        ff=f+(slide-f)*(t/du) if slide else f
        buf[i]+=amp*math.exp(-dec*t/du)*osc(o,t,ff)
def noise(buf,st,du,amp=0.15,dec=6.0,n=None,seed=None):
    n=n or len(buf); rng=random.Random(seed) if seed else random
    s0=int(st*SR); s1=min(int((st+du)*SR),n)
    for i in range(s0,s1):
        t=(i-s0)/SR; buf[i]+=amp*math.exp(-dec*t/du)*(rng.random()*2-1)
def kick(buf,st,amp=0.5,n=None): note(buf,st,0.16,110,'sin',amp,dec=2.0,slide=42,n=n)
def snare(buf,st,amp=0.28,n=None): noise(buf,st,0.12,amp,dec=8,n=n); note(buf,st,0.08,200,'tri',amp*0.6,dec=3,n=n)
def clap(buf,st,amp=0.3,n=None): noise(buf,st,0.1,amp,dec=10,n=n); note(buf,st,0.06,160,'sq',amp*0.3,dec=4,n=n)
def hat(buf,st,amp=0.1,n=None,seed=1): noise(buf,st,0.035,amp,dec=12,n=n,seed=seed)
def ohat(buf,st,amp=0.1,n=None): noise(buf,st,0.22,amp,dec=6,n=n)
def eight08(buf,st,du,f,amp=0.4,n=None): note(buf,st,du,f,'sin',amp,dec=1.2,slide=f*0.94,n=n)
def pluck(buf,st,f,o='tri',amp=0.18,dec=5,n=None): note(buf,st,0.5,f,o,amp,dec=dec,n=n)
def pad(buf,st,du,f,amp=0.06,n=None):
    note(buf,st,du,f,'tri',amp,dec=0.8,n=n); note(buf,st,du,f*1.005,'sin',amp*0.8,dec=0.8,n=n); note(buf,st,du,f*0.995,'sin',amp*0.7,dec=0.8,n=n)
def riser(buf,st,du,n=None):
    n=n or len(buf); s0=int(st*SR); s1=min(int((st+du)*SR),n)
    for i in range(s0,s1):
        t=(i-s0)/SR; buf[i]+=0.05*math.sin(2*math.pi*(150+900*(t/du))*t)*(t/du)

def save(buf, name):
    peak=max(1e-6,max(abs(v) for v in buf)); scale=0.88/peak
    with wave.open(str(OUT/f"{name}.wav"),'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b''.join(struct.pack('<h',int(max(-1,min(1,v*scale))*32767)) for v in buf))
    print(f"  {name}.wav {len(buf)/SR:.1f}s")

# === LO-FI 85bpm ~45s: 8 bars intro-ish + groove, bridge, silence ===
def lofi():
    B=60/85; bars=14; n=int(bars*4*B*SR); buf=[0.0]*n
    C3,E3,G3,A3,F3,D3 = nf('C3'),nf('E3'),nf('G3'),nf('A3'),nf('F3'),nf('D3')
    C4,E4,G4,A4,F4 = nf('C4'),nf('E4'),nf('G4'),nf('A4'),nf('F4')
    bass=[C3,A3,F3,G3]*4
    for bar in range(bars):
        b0=bar*4*B
        # bass whole notes
        note(buf,b0,B*3.8,bass[bar%len(bass)],'sin',0.18,dec=0.8,n=n)
        # piano-ish plucks
        if bar<4: # intro sparse
            pluck(buf,b0,C4,'tri',0.12,dec=6,n=n)
        elif bar<8: # groove
            kick(buf,b0,0.4,n=n); kick(buf,b0+2.5*B,0.3,n=n); snare(buf,b0+2*B,0.2,n=n)
            for s in range(16):
                if s%4==2: hat(buf,b0+s*0.25*B,0.05,n=n)
            pluck(buf,b0,C4,'tri',0.16,dec=6,n=n); pluck(buf,b0+2*B,E4,'tri',0.13,dec=6,n=n)
        elif bar<10: # bridge (sparse)
            pad(buf,b0,B*4,C4,0.05,n=n)
        else: # buildup+drop
            kick(buf,b0,0.4,n=n); snare(buf,b0+2*B,0.22,n=n)
            for s in range(16):
                hat(buf,b0+s*0.25*B,0.04+0.01*s,n=n)
            pluck(buf,b0,C4,'tri',0.16,dec=6,n=n); pluck(buf,b0+1.5*B,G4,'tri',0.14,dec=6,n=n)
    save(buf,"lofi-theme")

# === COUNTRY 100bpm ~45s ===
def country():
    B=60/100; bars=14; n=int(bars*4*B*SR); buf=[0.0]*n
    G2,D3,C3,E3,G3,B3,D4,G4,A4 = nf('G2'),nf('D3'),nf('C3'),nf('E3'),nf('G3'),nf('B3'),nf('D4'),nf('G4'),nf('A4')
    for bar in range(bars):
        b0=bar*4*B
        # country bass (boom-chick)
        note(buf,b0,B*0.9,G2,'sin',0.22,dec=1.5,n=n)
        note(buf,b0+2*B,B*0.9,D3,'sin',0.2,dec=1.5,n=n)
        # drums
        kick(buf,b0,0.4,n=n); kick(buf,b0+2*B,0.4,n=n)
        snare(buf,b0+1*B,0.24,n=n); snare(buf,b0+3*B,0.24,n=n)
        for s in range(16):
            if s%2==0: hat(buf,b0+s*0.25*B,0.05,n=n)
        # melody (western)
        if bar<4: pluck(buf,b0,G3,'tri',0.14,dec=4,n=n)
        elif bar<8:
            pluck(buf,b0,G3,'tri',0.17,dec=4,n=n); pluck(buf,b0+1*B,B3,'tri',0.14,dec=4,n=n); pluck(buf,b0+2*B,D4,'tri',0.15,dec=4,n=n); pluck(buf,b0+3*B,G3,'tri',0.13,dec=4,n=n)
        elif bar<10: pad(buf,b0,B*4,G3,0.05,n=n)
        else:
            pluck(buf,b0,G3,'tri',0.17,dec=4,n=n); pluck(buf,b0+1.5*B,D4,'tri',0.15,dec=4,n=n); pluck(buf,b0+2.5*B,A4,'tri',0.14,dec=4,n=n)
    save(buf,"country-theme")

# === POP 118bpm ~45s ===
def pop():
    B=60/118; bars=16; n=int(bars*4*B*SR); buf=[0.0]*n
    C3,G3,A3,F3,C4,E4,G4,A4,D4,E4 = nf('C3'),nf('G3'),nf('A3'),nf('F3'),nf('C4'),nf('E4'),nf('G4'),nf('A4'),nf('D4'),nf('E4')
    for bar in range(bars):
        b0=bar*4*B
        root=[C3,G3,A3,F3][bar%4]
        note(buf,b0,B*1.5,root,'sin',0.2,dec=1.0,n=n); note(buf,b0+2*B,B*1.5,root,'sin',0.18,dec=1.0,n=n)
        kick(buf,b0,0.45,n=n); kick(buf,b0+2*B,0.4,n=n)
        snare(buf,b0+1*B,0.24,n=n); snare(buf,b0+3*B,0.24,n=n)
        for s in range(16):
            if s%2==0: hat(buf,b0+s*0.25*B,0.06,n=n)
        # pop melody
        if bar<4: pluck(buf,b0,C4,'tri',0.15,dec=4,n=n); pluck(buf,b0+2*B,E4,'tri',0.13,dec=4,n=n)
        elif bar<8:
            for b,nt in [(0,C4),(1,E4),(2,G4),(3,A4)]: pluck(buf,b0+b*B,nt,'tri',0.16,dec=4,n=n)
        elif bar<10: pad(buf,b0,B*4,C4,0.05,n=n)
        else:
            for b,nt in [(0,C4),(1.5,E4),(2.5,G4)]: pluck(buf,b0+b*B,nt,'tri',0.16,dec=4,n=n)
    save(buf,"pop-theme")

# === ELECTRO 140bpm ~45s ===
def electro():
    B=60/140; bars=16; n=int(bars*4*B*SR); buf=[0.0]*n
    D2,A1,F2,C3,D3,F3,A3,D4,F4,A4 = nf('D2'),nf('A1'),nf('F2'),nf('C3'),nf('D3'),nf('F3'),nf('A3'),nf('D4'),nf('F4'),nf('A4')
    bass=[D2,A1,F2,C3]*4
    for bar in range(bars):
        b0=bar*4*B
        root=bass[bar%len(bass)]
        eight08(buf,b0,B*1.1,root,0.42,n=n); eight08(buf,b0+2*B,B*1.1,root*1.5,0.36,n=n)
        for beat in [0,1,2,3]: kick(buf,b0+beat*B,0.5,n=n)
        clap(buf,b0+1*B,0.3,n=n); clap(buf,b0+3*B,0.3,n=n)
        for s in range(16):
            b=b0+s*0.25*B
            if s>=13:
                for k in range(3): hat(buf,b+k*0.04,0.07,n=n)
            else: hat(buf,b,0.08 if s%4==0 else (0.05 if s%2==0 else 0.03),n=n)
        # synth lead
        if bar<4: note(buf,b0,B*0.8,D4,'saw',0.08,n=n)
        elif bar<8:
            note(buf,b0,B*0.5,D4,'saw',0.09,n=n); note(buf,b0+1*B,F4,'saw',0.08,n=n); note(buf,b0+2*B,A4,'saw',0.09,n=n); note(buf,b0+3*B,F4,'saw',0.07,n=n)
        elif bar<10: pad(buf,b0,B*4,D3,0.05,n=n)
        else:
            note(buf,b0,B*0.5,D4,'saw',0.09,n=n); note(buf,b0+1.5*B,F4,'saw',0.08,n=n); note(buf,b0+2.5*B,A4,'saw',0.09,n=n)
    riser(buf,(bars-2)*4*B,B*6,n=n)
    save(buf,"electro-theme")

print("Rendering genre beats...")
lofi(); country(); pop(); electro()
print("DONE")
