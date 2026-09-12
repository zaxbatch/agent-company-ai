#!/usr/bin/env python3
"""Minimal Scratch 3 (.sb3) project writer.

A .sb3 is a ZIP containing project.json plus assets named <md5>.<ext> — the same
"zip + JSON manifest" shape as LMMS .mmp and Pencil2D .pclx, so projects can be
authored programmatically and then opened/played in Scratch.

Block input encoding (scratch-vm):
  literal number : [1, [4, "10"]]
  literal text   : [1, [10, "hello"]]
  broadcast      : [1, [11, "name", "id"]]
  a block input  : [3, "<blockid>", [10, ""]]
  a substack     : [2, "<blockid>"]
"""
from __future__ import annotations
import hashlib, json, os, zipfile


class Blocks:
    """Collects blocks for one target and wires up next/parent pointers."""

    def __init__(self):
        self.b = {}
        self._n = 0

    def _id(self, tag="b"):
        self._n += 1
        return f"{tag}{self._n}"

    def add(self, opcode, inputs=None, fields=None, top=False, parent=None):
        bid = self._id()
        self.b[bid] = {
            "opcode": opcode,
            "next": None,
            "parent": parent,
            "inputs": inputs or {},
            "fields": fields or {},
            "shadow": False,
            "topLevel": bool(top),
        }
        return bid

    def chain(self, specs, parent=None):
        """specs: list of (opcode, inputs, fields) -> returns first block id."""
        ids = []
        for opcode, inputs, fields in specs:
            bid = self.add(opcode, inputs, fields, top=(not ids and parent is None),
                           parent=parent if not ids else None)
            ids.append(bid)
        for a, c in zip(ids, ids[1:]):
            self.b[a]["next"] = c
            self.b[c]["parent"] = a
        return ids[0] if ids else None

    def script(self, specs, parent=None):
        return self.chain(specs, parent=parent)


def num(v):
    return [1, [4, str(v)]]


def text(v):
    return [1, [10, str(v)]]


def bcast(name, mid):
    return [1, [11, str(name), str(mid)]]


def sub(bid):
    return [2, bid]


def via(bid):
    return [3, bid, [10, ""]]


def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


class Project:
    def __init__(self):
        self.targets = []
        self.assets = []          # (source_path, md5ext)
        self.meta = {"semver": "3.0.0", "vm": "0.2.0", "agent": "zdot-scratch-lib"}
        self.broadcasts = {}      # mid -> name

    def broadcast_id(self, name):
        mid = "zdmsg" + hashlib.md5(name.encode()).hexdigest()[:12]
        self.broadcasts[mid] = name
        return mid

    # ---------- targets ----------
    def stage(self, backdrop_png, sounds=()):
        costumes = []
        aid = md5_file(backdrop_png)
        ext = os.path.splitext(backdrop_png)[1][1:]
        self.assets.append((backdrop_png, f"{aid}.{ext}"))
        from PIL import Image
        w, h = Image.open(backdrop_png).size
        costumes.append(dict(name="backdrop", bitmapResolution=1, dataFormat=ext,
                             assetId=aid, md5ext=f"{aid}.{ext}", rotationCenterX=0,
                             rotationCenterY=0, _w=w, _h=h))
        self.targets.append(dict(
            isStage=True, name="Stage", variables={}, lists={}, broadcasts=dict(self.broadcasts),
            blocks={}, comments={}, currentCostume=0, costumes=costumes, sounds=list(sounds),
            volume=100, layerOrder=0, tempo=60, videoTransparency=50, videoState="off",
            textToSpeechLanguage=None))
        return self.targets[-1]

    def sprite(self, name, png, x=0, y=0, size=100, layer=1, blocks=None,
               rotation_style="all around"):
        aid = md5_file(png)
        ext = os.path.splitext(png)[1][1:]
        self.assets.append((png, f"{aid}.{ext}"))
        from PIL import Image
        w, h = Image.open(png).size
        self.targets.append(dict(
            isStage=False, name=name, variables={}, lists={}, broadcasts=dict(self.broadcasts),
            blocks=blocks or {}, comments={}, currentCostume=0,
            costumes=[dict(name=os.path.basename(png), bitmapResolution=1, dataFormat=ext,
                           assetId=aid, md5ext=f"{aid}.{ext}",
                           rotationCenterX=w // 2, rotationCenterY=h // 2)],
            sounds=[], volume=100, layerOrder=layer,
            visible=True, x=x, y=y, size=size, direction=90, draggable=False,
            rotationStyle=rotation_style))
        return self.targets[-1]

    def add_sound(self, target, path, name=None, rate=44100, samples=0):
        aid = md5_file(path)
        ext = os.path.splitext(path)[1][1:]
        self.assets.append((path, f"{aid}.{ext}"))
        target["sounds"].append(dict(name=name or os.path.splitext(os.path.basename(path))[0],
                                     assetId=aid, dataFormat=ext, md5ext=f"{aid}.{ext}",
                                     rate=rate, sampleCount=samples))
        return target["sounds"][-1]

    def save(self, path):
        # keep the broadcast table in sync everywhere
        for t in self.targets:
            if not t["isStage"]:
                t["broadcasts"] = dict(self.broadcasts)
        doc = {"targets": self.targets, "monitors": [], "extensions": [],
               "meta": self.meta}
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("project.json", json.dumps(doc))
            written = set()
            for src, md5ext in self.assets:
                if md5ext in written:
                    continue
                z.write(src, md5ext)
                written.add(md5ext)
        return os.path.getsize(path)
