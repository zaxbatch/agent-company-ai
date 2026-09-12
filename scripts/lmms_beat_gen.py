#!/usr/bin/env python3
"""Generate a real LMMS project (.mmp) deterministically, then render it headless.

No GUI, no GUI-automation: LMMS 1.2.x project files are plain XML, and
`lmms render <project> -o <file> -f wav` works under QT_QPA_PLATFORM=offscreen.

Usage:
    python3 scripts/lmms_beat_gen.py --out content/experiments/lmms/beat-8bar.mmp
    python3 scripts/lmms_beat_gen.py --out X.mmp --render X.wav [--bpm 128]
"""
from __future__ import annotations
import argparse, os, subprocess, sys
from xml.sax.saxutils import quoteattr

TICKS_PER_BAR = 192  # LMMS internal resolution: 192 ticks per 4/4 bar

SAMPLES = "/usr/share/lmms/samples"   # what AFP `src` is relative to


class Track:
    """One instrument track inside a Beat/Bassline container."""

    def __init__(self, name, instrument_xml, vol=100, pan=0):
        self.name, self.instrument_xml = name, instrument_xml
        self.vol, self.pan = vol, pan
        self.notes = []  # (pos_ticks, key, vol, len_ticks)

    def n(self, pos, key=57, vol=100, length=12):
        self.notes.append((int(pos), int(key), int(vol), int(length)))
        return self

    def hits(self, positions, key=57, vol=100, length=12):
        for p in positions:
            self.n(p, key, vol, length)
        return self

    def xml(self):
        notes = "".join(
            f'\n                <note pos="{p}" key="{k}" vol="{v}" len="{l}" pan="0"/>'
            for p, k, v, l in self.notes)
        return f'''            <track muted="0" name={quoteattr(self.name)} solo="0" type="0">
              <instrumenttrack pitch="0" fxch="0" basenote="57" usemasterpitch="1" pitchrange="1" vol="{self.vol}" pan="{self.pan}">
                {self.instrument_xml}
                <eldata ftype="0" fres="0.5" fcut="14000" fwet="0">
                  <elvol latt="0" dec="0.5" lamt="0" lspd_numerator="1" att="0" sustain="0.5" amt="0" userwavefile="" ctlenvamt="0" lshp="0" lspd_denominator="1" x100="0" lpdel="0" lspd="0.1" pdel="0" hold="0.5" syncmode="0" rel="0.1"/>
                  <elcut latt="0" dec="0.5" lamt="0" lspd_numerator="1" att="0" sustain="0.5" amt="0" userwavefile="" ctlenvamt="0" lshp="0" lspd_denominator="1" x100="0" lpdel="0" lspd="0.1" pdel="0" hold="0.5" syncmode="0" rel="0.1"/>
                  <elres latt="0" dec="0.5" lamt="0" lspd_numerator="1" att="0" sustain="0.5" amt="0" userwavefile="" ctlenvamt="0" lshp="0" lspd_denominator="1" x100="0" lpdel="0" lspd="0.1" pdel="0" hold="0.5" syncmode="0" rel="0.1"/>
                </eldata>
                <chordcreator chord="0" chordrange="1" chord-enabled="0"/>
                <arpeggiator arp="0" arptime_numerator="1" arptime_denominator="1" arprange="1" arpmode="0" arptime="100" arpdir="0" arpgate="100" syncmode="0" arp-enabled="0"/>
                <midiport outputchannel="1" outputcontroller="0" basevelocity="127" outputprogram="1" fixedinputvelocity="-1" fixedoutputvelocity="-1" fixedoutputnote="-1" inputchannel="0" inputcontroller="0" readable="0" writable="0"/>
                <fxchain enabled="0" numofeffects="0"/>
              </instrumenttrack>
              <pattern len="{TICKS_PER_BAR * BARS}" muted="0" name={quoteattr(self.name)} steps="16" pos="0" type="0">{notes}
              </pattern>
            </track>'''


def afp(sample_rel, amp=100):
    return (f'<instrument name="audiofileprocessor">\n'
            f'                  <audiofileprocessor stutter="0" interp="1" reversed="0" looped="0" '
            f'sframe="0" lframe="0.9999" src={quoteattr(sample_rel)} eframe="1" amp="{amp}"/>\n'
            f'                </instrument>')


def tripleosc(wave0=2, wave1=2, wave2=3, vol1=63, vol2=40, coarse2=12, cutoff=2600, res=0.9):
    return (f'<instrument name="tripleoscillator">\n'
            f'                  <tripleoscillator vol0="100" wavetype0="{wave0}" pan0="0" coarse0="0" finel0="0" finer0="0" '
            f'vol1="{vol1}" wavetype1="{wave1}" pan1="0" coarse1="0" finel1="-16" finer1="13" '
            f'vol2="{vol2}" wavetype2="{wave2}" pan2="0" coarse2="{coarse2}" finel2="0" finer2="0" '
            f'phoffset0="0" phoffset1="266" phoffset2="80" modalgo1="2" modalgo2="0" modalgo3="2" '
            f'stphdetun0="121" stphdetun1="259" stphdetun2="92" '
            f'userwavefile0="" userwavefile1="" userwavefile2="samples/shapes/smooth_inv_saw.ogg"/>\n'
            f'                </instrument>')


BARS = 8
BAR = TICKS_PER_BAR
Q, E, S = 48, 24, 12  # quarter, eighth, sixteenth in ticks


def build(bpm=128):
    kick = Track("Kick", afp("drums/kick_hard01.ogg"), vol=100)
    snare = Track("Snare", afp("drums/snare_harsh01.ogg"), vol=88)
    hat = Track("Hat", afp("drums/hihat_closed01.ogg"), vol=62)
    openhat = Track("OpenHat", afp("drums/hihat_opened02.ogg"), vol=54)
    clap = Track("Clap", afp("drums/clap04.ogg"), vol=70)
    crash = Track("Crash", afp("drums/crash01.ogg"), vol=58)
    bass = Track("Bass", tripleosc(wave0=2, wave1=0, vol1=0, vol2=0, coarse2=0), vol=92)
    stab = Track("Stab", tripleosc(vol1=52, vol2=30, coarse2=12), vol=44, pan=-18)

    roots = [45, 41, 48, 43]  # Am F C G  (A2, F2, C3, G2)
    bars_per_chord = 1

    for b in range(BARS):
        bar0 = b * BAR
        root = roots[(b // bars_per_chord) % 4]
        section_b = b >= 4  # second half = fuller arrangement

        # --- drums -------------------------------------------------------
        # four-on-the-floor, with a 16th pickup into each bar
        for beat in range(4):
            kick.n(bar0 + beat * Q, 57, 100 if beat == 0 else 92)
        if section_b and b % 2 == 1:
            kick.n(bar0 + 3 * Q + S, 57, 70)
            kick.n(bar0 + 3 * Q + 2 * S, 57, 60)
        # snare on 2 and 4 (+ ghost notes in the second half)
        snare.n(bar0 + Q, 57, 96).n(bar0 + 3 * Q, 57, 96)
        if section_b:
            snare.n(bar0 + 2 * Q + 2 * S, 57, 40)
        # closed hats on straight 16ths, accented on the offbeat 8ths
        for i in range(16):
            vol = 70 if i % 4 == 2 else (48 if i % 2 == 1 else 34)
            hat.n(bar0 + i * S, 57, vol)
        openhat.n(bar0 + 3 * Q + 2 * S, 57, 50)
        # clap doubled with the snare in the back half
        if section_b:
            clap.n(bar0 + Q, 57, 64).n(bar0 + 3 * Q, 57, 64)
        if b in (0, 4):
            crash.n(bar0, 57, 60)
        # bar 8 fill: 16th snare roll, dropping the last 8th
        if b == BARS - 1:
            for i in range(8, 16):
                snare.n(bar0 + i * S, 57, 40 + (i - 8) * 7)

        # --- bass: 8th-note pulse with an octave jump on the offbeat ------
        for i in range(8):
            if i == 6 and section_b:
                continue  # syncopated drop-out
            key = root + (12 if i in (3, 7) else 0)
            bass.n(bar0 + i * E, key, 96 if i % 2 == 0 else 74, length=E - 6)
        if b == BARS - 1:
            bass.n(bar0 + 7 * E, root + 7, 88, E - 6)  # walk-up turn

        # --- chord stabs on the off-beats (Am / F / C / G triads) --------
        third = {45: 48, 41: 45, 48: 52, 43: 47}[root]   # +3 or +4 semitones
        fifth = {45: 52, 41: 48, 48: 55, 43: 50}[root]   # +7
        for i in (1, 3, 4, 6):
            stab.n(bar0 + i * E, root + 12, 40, E - 8)
            stab.n(bar0 + i * E, third, 36, E - 8)
            stab.n(bar0 + i * E, fifth, 32, E - 8)

    tracks = [kick, snare, clap, hat, openhat, crash, bass, stab]
    body = "\n".join(t.xml() for t in tracks)

    return f'''<?xml version="1.0"?>
<!DOCTYPE lmms-project>
<lmms-project type="song" version="1.0" creator="Z-Dot Team" creatorversion="1.2.0">
  <head timesig_denominator="4" bpm="{bpm}" masterpitch="0" mastervol="100" timesig_numerator="4"/>
  <song>
    <trackcontainer visible="1" width="1000" height="400" type="song" x="12" y="1" maximized="0" minimized="0">
      <track muted="0" name="Beat/Bassline 0" solo="0" type="1">
        <bbtrack>
          <trackcontainer visible="1" width="972" height="352" type="bbtrackcontainer" x="541" y="531" maximized="0" minimized="0">
{body}
          </trackcontainer>
        </bbtrack>
        <bbtco usestyle="1" muted="0" name="Beat/Bassline 0" pos="0" len="{BAR * BARS}" color="4282417407"/>
      </track>
    </trackcontainer>
    <fxmixer visible="1" width="530" height="332" x="9" y="530" maximized="0" minimized="0">
      <fxchannel muted="0" num="0" name="Master" volume="0.5" soloed="0">
        <fxchain numofeffects="0" enabled="0"/>
      </fxchannel>
    </fxmixer>
    <ControllerRackView visible="1" width="258" height="173" x="664" y="444" maximized="0" minimized="0"/>
    <pianoroll visible="0" width="640" height="480" x="1" y="1" maximized="1" minimized="0"/>
    <automationeditor visible="0" width="640" height="400" x="356" y="129" maximized="0" minimized="0"/>
  </song>
</lmms-project>
'''


def render(mmp, out, lmms="lmms", timeout=120):
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    cmd = [lmms, "render", mmp, "-o", out, "-f", "wav", "-s", "44100", "-x", "2",
           "-i", "sincbest"]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0 or not os.path.exists(out):
        sys.stderr.write(r.stdout + "\n" + r.stderr + "\n")
        raise SystemExit(f"render failed rc={r.returncode}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="content/experiments/lmms/beat-8bar.mmp")
    ap.add_argument("--render", metavar="WAV")
    ap.add_argument("--bpm", type=int, default=128)
    a = ap.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    xml = build(bpm=a.bpm)
    with open(a.out, "w") as f:
        f.write(xml)
    print(f"wrote {a.out} ({len(xml)} bytes, {BARS} bars @ {a.bpm} bpm)")

    if a.render:
        render(a.out, a.render)
        print(f"rendered {a.render}")


if __name__ == "__main__":
    main()
