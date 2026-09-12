#!/usr/bin/env python3
"""Author a real LMMS project (.mmp) from a JSON spec, then render it headless.

LMMS 1.2.x project files are plain XML and `lmms render` runs under
QT_QPA_PLATFORM=offscreen, so a beat becomes reproducible from a spec:
tracks + arrangement go in, project + master + stems come out.

    python3 scripts/lmms_beat.py --spec content/experiments/lmms/beat-16bar.spec.json
    python3 scripts/lmms_beat.py --spec S.json --stems    # also split per-track
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys
from xml.sax.saxutils import quoteattr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmms_spec import (DEFAULT_SPEC, CHORDS, Q, E, S, TICKS_PER_BAR,
                       load, validate, layer_bar_map, chord_for_bar)

BAR = TICKS_PER_BAR
MASTER_FADER = "0.5"   # hard-won: >0.5 clips when 8 tracks sum


class Track:
    def __init__(self, name, instrument_xml, vol=100, pan=0):
        self.name, self.instrument_xml = name, instrument_xml
        self.vol, self.pan = vol, pan
        self.notes = []

    def n(self, pos, key=57, vol=100, length=12):
        self.notes.append((int(pos), int(key), int(vol), int(length)))
        return self

    def xml(self, total_bars):
        notes = "".join(
            f'\n                <note pos="{p}" key="{k}" vol="{v}" len="{l}" pan="0"/>'
            for p, k, v, l in sorted(self.notes))
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
              <pattern len="{BAR * total_bars}" muted="0" name={quoteattr(self.name)} steps="16" pos="0" type="0">{notes}
              </pattern>
            </track>'''


def afp(sample_rel, amp=100):
    return ('<instrument name="audiofileprocessor">\n'
            '                  <audiofileprocessor stutter="0" interp="1" reversed="0" looped="0" '
            f'sframe="0" lframe="0.9999" src={quoteattr(sample_rel)} eframe="1" amp="{amp}"/>\n'
            '                </instrument>')


def tripleosc(wave0=2, wave1=2, wave2=3, vol1=63, vol2=40, coarse2=12):
    return ('<instrument name="tripleoscillator">\n'
            f'                  <tripleoscillator vol0="100" wavetype0="{wave0}" pan0="0" coarse0="0" finel0="0" finer0="0" '
            f'vol1="{vol1}" wavetype1="{wave1}" pan1="0" coarse1="0" finel1="-16" finer1="13" '
            f'vol2="{vol2}" wavetype2="{wave2}" pan2="0" coarse2="{coarse2}" finel2="0" finer2="0" '
            f'phoffset0="0" phoffset1="266" phoffset2="80" modalgo1="2" modalgo2="0" modalgo3="2" '
            f'stphdetun0="121" stphdetun1="259" stphdetun2="92" '
            f'userwavefile0="" userwavefile1="" userwavefile2="samples/shapes/smooth_inv_saw.ogg"/>\n'
            '                </instrument>')


def build_tracks(spec):
    t = {
        "kick":    Track("Kick",    afp("drums/kick_hard01.ogg"), vol=100),
        "snare":   Track("Snare",   afp("drums/snare_harsh01.ogg"), vol=88),
        "clap":    Track("Clap",    afp("drums/clap04.ogg"), vol=68),
        "hat":     Track("Hat",     afp("drums/hihat_closed01.ogg"), vol=58),
        "openhat": Track("OpenHat", afp("drums/hihat_opened02.ogg"), vol=52),
        "crash":   Track("Crash",   afp("drums/crash01.ogg"), vol=56),
        "bass":    Track("Bass",    tripleosc(wave0=2, wave1=0, vol1=0, vol2=0, coarse2=0), vol=92),
        "stab":    Track("Stab",    tripleosc(vol1=52, vol2=30, coarse2=12), vol=44, pan=-18),
    }
    plan = layer_bar_map(spec)
    prev_layers = None
    for bar, (layers, is_fill) in enumerate(plan):
        bar0 = bar * BAR
        root, third, fifth = CHORDS[chord_for_bar(spec, bar)]
        full = bar >= max(1, len(plan) // 2)   # second half of the tune

        if "kick" in layers:
            for beat in range(4):
                t["kick"].n(bar0 + beat * Q, 57, 100 if beat == 0 else 92)
            if full and bar % 2 == 1:
                t["kick"].n(bar0 + 3 * Q + S, 57, 70).n(bar0 + 3 * Q + 2 * S, 57, 60)
        if "snare" in layers:
            t["snare"].n(bar0 + Q, 57, 96).n(bar0 + 3 * Q, 57, 96)
            if full:
                t["snare"].n(bar0 + 2 * Q + 2 * S, 57, 40)
        if "clap" in layers:
            t["clap"].n(bar0 + Q, 57, 64).n(bar0 + 3 * Q, 57, 64)
        if "hat" in layers:
            for i in range(16):
                vol = 70 if i % 4 == 2 else (48 if i % 2 else 32)
                t["hat"].n(bar0 + i * S, 57, vol)
        if "openhat" in layers:
            t["openhat"].n(bar0 + 3 * Q + 2 * S, 57, 50)
        if "crash" in layers or (prev_layers is not None and "kick" not in prev_layers):
            t["crash"].n(bar0, 57, 58)
        if "bass" in layers:
            for i in range(8):
                if full and i == 6:
                    continue
                key = root + (12 if i in (3, 7) else 0)
                t["bass"].n(bar0 + i * E, key, 96 if i % 2 == 0 else 74, E - 6)
            if is_fill:
                t["bass"].n(bar0 + 7 * E, root + 7, 88, E - 6)
        if "stab" in layers:
            for i in (1, 3, 4, 6):
                t["stab"].n(bar0 + i * E, root + 12, 40, E - 8)
                t["stab"].n(bar0 + i * E, third, 36, E - 8)
                t["stab"].n(bar0 + i * E, fifth, 32, E - 8)
        if is_fill:
            for i in range(8, 16):
                t["snare"].n(bar0 + i * S, 57, 40 + (i - 8) * 7)
        prev_layers = layers
    return [t[k] for k in ("kick", "snare", "clap", "hat", "openhat", "crash", "bass", "stab")
            if t[k].notes]


def build_project(spec):
    total = spec["total_bars"]
    body = "\n".join(tr.xml(total) for tr in build_tracks(spec))
    return f'''<?xml version="1.0"?>
<!DOCTYPE lmms-project>
<lmms-project type="song" version="1.0" creator="Z-Dot Team" creatorversion="1.2.0">
  <head timesig_denominator="4" bpm="{spec['bpm']}" masterpitch="0" mastervol="100" timesig_numerator="4"/>
  <song>
    <trackcontainer visible="1" width="1000" height="400" type="song" x="12" y="1" maximized="0" minimized="0">
      <track muted="0" name={quoteattr(spec.get("title", "Beat"))} solo="0" type="1">
        <bbtrack>
          <trackcontainer visible="1" width="972" height="352" type="bbtrackcontainer" x="541" y="531" maximized="0" minimized="0">
{body}
          </trackcontainer>
        </bbtrack>
        <bbtco usestyle="1" muted="0" name={quoteattr(spec.get("title", "Beat"))} pos="0" len="{BAR * total}" color="4282417407"/>
      </track>
    </trackcontainer>
    <fxmixer visible="1" width="530" height="332" x="9" y="530" maximized="0" minimized="0">
      <fxchannel muted="0" num="0" name="Master" volume="{MASTER_FADER}" soloed="0">
        <fxchain numofeffects="0" enabled="0"/>
      </fxchannel>
    </fxmixer>
    <ControllerRackView visible="1" width="258" height="173" x="664" y="444" maximized="0" minimized="0"/>
    <pianoroll visible="0" width="640" height="480" x="1" y="1" maximized="1" minimized="0"/>
    <automationeditor visible="0" width="640" height="400" x="356" y="129" maximized="0" minimized="0"/>
  </song>
</lmms-project>
'''


def run_lmms(args, timeout=300):
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    r = subprocess.run(["lmms"] + args, env=env, capture_output=True, text=True,
                       timeout=timeout)
    if r.returncode != 0:
        sys.stderr.write((r.stdout or "") + "\n" + (r.stderr or "") + "\n")
        raise SystemExit(f"lmms failed rc={r.returncode}: {' '.join(args[:2])}")
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", help="JSON spec (omit to use the built-in default)")
    ap.add_argument("--outdir", default="content/experiments/lmms")
    ap.add_argument("--name")
    ap.add_argument("--stems", action="store_true", help="also render per-track WAVs")
    ap.add_argument("--mp3", action="store_true", help="also encode an MP3")
    a = ap.parse_args()

    spec = load(a.spec) if a.spec else validate(dict(DEFAULT_SPEC))
    os.makedirs(a.outdir, exist_ok=True)
    stem = a.name or spec.get("title", "beat")
    mmp = os.path.join(a.outdir, stem + ".mmp")
    wav = os.path.join(a.outdir, stem + ".wav")

    xml = build_project(spec)
    with open(mmp, "w") as f:
        f.write(xml)
    # write the spec next to the project so QA can read section boundaries
    with open(os.path.join(a.outdir, stem + ".spec.json"), "w") as f:
        json.dump(spec, f, indent=2)

    print(f"wrote {mmp}  ({len(xml)} bytes, {spec['total_bars']} bars @ {spec['bpm']} bpm)")
    print("sections: " + ", ".join(f"{s['name']}x{s['bars']}" for s in spec["sections"]))

    run_lmms(["render", mmp, "-o", wav, "-f", "wav", "-s", "44100"])
    print(f"rendered {wav}")

    if a.stems:
        sd = os.path.join(a.outdir, stem + "-stems")
        os.makedirs(sd, exist_ok=True)
        run_lmms(["rendertracks", mmp, "-o", sd, "-f", "wav"])
        print(f"stems -> {sd}/ ({len(os.listdir(sd))} files)")

    if a.mp3:
        mp3 = os.path.join(a.outdir, stem + ".mp3")
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                        "-i", wav, "-b:a", "192k", mp3], check=True)
        print(f"encoded {mp3}")


if __name__ == "__main__":
    main()
