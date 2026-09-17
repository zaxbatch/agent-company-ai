#!/usr/bin/env python3
"""mkproj.py — build valid LMMS 1.2.2 projects by cloning LMMS's own skeleton.

Three things were learned the hard way, each by a failed render:

1. A hand-written project containing only <trackcontainer>, <fxmixer> and
   <timeline> loads to nothing: LMMS exits 0 and writes no file. The automation
   track, ControllerRackView, pianoroll, automationeditor, projectnotes and
   <controllers> are all required. So the skeleton is cloned from LMMS itself.

2. The automation track is a SIBLING of the song's <trackcontainer>, not a child.
   Cutting the file at <track type="6"> therefore deletes the container's closing
   tag and the project fails to load.

3. A <pattern> is a child of the instrument <track type="0">, NOT a sibling of
   <bbtrack>. Put it in the wrong place and the project renders the right length
   but in total silence -- LMMS warns "Track::getTCO(0), but TCO 0 doesn't exist".

Structure (verified against LMMS's own tutorial project):
  <track type="1">            the BB track = one arrangement section
    <bbtrack><trackcontainer>
      <track type="0">        one instrument
        <instrumenttrack>
          <instrument>...</instrument>
        </instrumenttrack>
        <pattern>...</pattern> the TCO -- notes live HERE
      </track>
    </trackcontainer></bbtrack>
    <bbtco pos=... len=... />  where this section sits in the song
  </track>
"""
from __future__ import annotations
from pathlib import Path
import re

SKELETON = Path("/usr/share/lmms/projects/tutorials/editing_note_volumes.mmp")
TPB = 96  # VERIFIED empirically: a note written at 7 bars rendered at bar 14 with
          # TPB=192, so LMMS 1.2.2 uses 96 ticks per bar here. The tutorial
          # project ships len="192" for a TWO-bar pattern, which is what misled
          # me into 192 and doubled every position and every rendered length.

# built-in instruments only -- no external samples, matching our stated scope
INSTR = {
    "tripleosc": lambda **k: ("tripleoscillator",
        f'<tripleoscillator vol1="{k.get("v1",100)}" vol2="{k.get("v2",0)}" vol3="{k.get("v3",0)}" '
        f'wavetype0="{k.get("w0",0)}" wavetype1="{k.get("w1",0)}" wavetype2="0" '
        f'coarse0="{k.get("c0",0)}" coarse1="{k.get("c1",0)}" coarse2="0" '
        f'finel0="0" finel1="0" finel2="0" finer0="0" finer1="0" finer2="0" '
        f'pan0="0" pan1="0" pan2="0"/>'),
    "kicker": lambda **k: ("kicker",
        f'<kicker startfreq="{k.get("f0",40)}" endfreq="{k.get("f1",150)}" '
        f'decay="{k.get("decay",60)}" noise="{k.get("noise",0)}" dist="1" gain="1" length="300"/>'),
    "lb302": lambda **k: ("lb302",
        f'<lb302 vol="{k.get("vol",40)}" wave="{k.get("wave",1)}" slide="0" shape="0" '
        f'vco="1" noise="0" k="1" dist="{k.get("dist",0)}" cut="{k.get("cut",1)}"/>'),
    "organic": lambda **k: ("organic",
        f'<organic vol="{k.get("vol",100)}" pan="0" fx1="0" fx2="0" '
        f'harmonic="{k.get("harmonic",4)}" modulation="{k.get("modulation",2)}" offset="0"/>'),
    "bitinvader": lambda **k: ("bitinvader",
        f'<bitinvader vol="{k.get("vol",100)}" pan="0" fx1="0" fx2="0" userwavefile=""/>'),
    "monstro": lambda **k: ("monstro",
        f'<monstro vol="100" pan="0" fx1="0" fx2="0" fx3="0" osc1vol="{k.get("o1",100)}" '
        f'osc1pan="-20" osc2vol="{k.get("o2",80)}" osc2pan="20" osc3vol="0" osc3pan="0" '
        f'osc1wave="{k.get("w1",2)}" osc2wave="{k.get("w2",-5)}" osc3wave="0"/>'),
}

ELDATA = '''        <eldata fwet="1" ftype="7" fres="1.2" fcut="1754">
          <elvol lspd="0.1" ctlenvamt="0" lpdel="0" pdel="0" amt="1" hold="0" syncmode="0" userwavefile="" latt="0" sustain="1"/>
          <elcut lspd="0.2918" ctlenvamt="1" lpdel="0" pdel="0" amt="0.82" hold="0" syncmode="0" userwavefile="" latt="0" sustain="1"/>
          <elres lspd="0.1" ctlenvamt="0" lpdel="0" pdel="0" amt="0" hold="0.499" syncmode="0" userwavefile="" latt="0" sustain="1"/>
        </eldata>
'''


def pattern_xml(name, notes, bars):
    """notes: (key, pos_bars, len_bars, vol 0-100). Lives INSIDE the track."""
    rows = []
    for key, pos, ln, vol in notes:
        rows.append(f'          <note key="{int(key)}" vol="{max(1,min(100,int(vol)))}" '
                    f'pos="{int(round(pos * TPB))}" pan="0" len="{max(1, int(round(ln * TPB)))}"/>')
    # `steps` MUST match the pattern length in 16th notes, i.e. bars * 16.
    # The tutorial skeleton uses steps="16" because its pattern is ONE bar. Left
    # at 16 for a 32-bar pattern, LMMS treats the pattern as 1 bar and LOOPS it
    # across the whole bbtco -- which produced instruments sounding on the wrong
    # bars, content offset by 4 bars, and a "dip" that was not a dip.
    return (f'        <pattern type="1" muted="0" steps="{bars * 16}" name="{name}" '
            f'pos="0" len="{bars * TPB}">\n' + "\n".join(rows) + '\n        </pattern>\n')


def inst_track(name, vol, instr_key, notes, bars, **kw):
    """<track type="0"> holding an <instrumenttrack> plus the <pattern>."""
    el_name, el_attrs = INSTR[instr_key](**kw)
    return f'''      <track type="0" muted="0" name="{name}" solo="0">
        <instrumenttrack pitch="0" vol="{vol}" fxch="0" pan="0" basenote="57" usemasterpitch="1" pitchrange="1">
          <instrument name="{el_name}">
            {el_attrs}
          </instrument>
{ELDATA}          <chordcreator chordrange="1" chord="0" chord-enabled="0"/>
          <arpeggiator arpdir="0" arpgate="100" arptime_denominator="4" syncmode="0" arp-enabled="0" arprange="2" arptime_numerator="4" arp="0"/>
          <midiport inputchannel="0" fixedinputvelocity="-1" outputcontroller="0" outputchannel="1" fixedoutputvelocity="-1" readonly="0"/>
          <fxchain numofeffects="0" enabled="0"/>
        </instrumenttrack>
{pattern_xml(name, notes, bars)}      </track>
'''


def section(name, tracks, start_bar, bars, color="4282417407"):
    """One BB track = one arrangement section, placed at start_bar."""
    body = "".join(tracks)
    return f'''    <track type="1" muted="0" name="{name}" solo="0">
      <bbtrack>
        <trackcontainer visible="1" width="580" height="249" type="bbtrackcontainer" x="426" y="182" maximized="0" minimized="0">
{body}        </trackcontainer>
      </bbtrack>
      <bbtco usestyle="1" muted="0" name="{name}" pos="{start_bar * TPB}" len="{bars * TPB}" color="{color}"/>
    </track>
'''


def build(bpm, sections, out_path, total_bars, mastervol=80):
    src = SKELETON.read_text()
    src = re.sub(r'(<head[^>]*?)bpm="\d+"', r'\1bpm="%d"' % bpm, src, count=1)
    # mastervol matters: six tracks summed at vol 100 with master at 100 clipped
    # the render to full scale (p90 = 1.0 from bar 12 on), which destroyed the
    # dynamic shape -- the intended dip read as the loudest section.
    src = re.sub(r'(<head[^>]*?)mastervol="\d+"', r'\1mastervol="%d"' % mastervol, src, count=1)
    start = src.index('<track type="1"')
    end = src.index('<track type="6"')
    src = (src[:start] + "".join(sections)
           + "</trackcontainer>\n    " + src[end:])
    # make sure the song is long enough to cover every section
    src = re.sub(r'<timeline lp0pos="0" lp1pos="\d+"',
                 f'<timeline lp0pos="0" lp1pos="{total_bars * TPB}"', src)
    Path(out_path).write_text(src)
    return out_path
