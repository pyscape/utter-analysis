#!/usr/bin/env python3
"""Export a partial_states.py run (.streams.jsonl) as tidy tables with a manifest.

    python export/states.py --streams RUN.streams.jsonl --out data/DATE-states
        --wheel "how the audio was decoded" [--report FILE ...]

One row per stream, word, gap, final and stable block; and in advances.parquet one row per
stream, advance and reading. A reading's `relation` and `lead_delta` are the runtime's own, as
the harness read them off the partial; the lead is derived from the confidences, which the
partial carries and no field repeats.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

import pandas as pd

UTTER = Path.home() / "Repos" / "utter"
SAMPLES_PER_MS = 16


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args):
    try:
        return subprocess.run(["git", "-C", str(UTTER), *args], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def clip_id(path):
    parts = path.split("/")
    return parts[-2] + "/" + parts[-1].removesuffix(".wav")


def load(path):
    T = dict(streams=[], words=[], gaps=[], finals=[], stable=[], advances=[])
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            key, split = r["key"], r["split"]
            T["streams"].append(dict(key=key, split=split, samples=r["samples"], n_words=len(r["words"]), n_gaps=len(r["gaps"]),
                                     n_finals=len(r["finals"]), n_advances=len(r["advances"])))
            for w in r["words"]:
                T["words"].append(dict(key=key, split=split, utt=w["utt"], word_index=w["index"], label=w["label"],
                                       clip_id=clip_id(w["clip"]), pos=w["pos"], samples=w["samples"], onset=w["onset"], offset=w["offset"]))
            for g in r["gaps"]:
                T["gaps"].append(dict(key=key, split=split, kind=g["kind"], after=g["after"], pos=g["pos"], samples=g["samples"], source=g["source"]))
            for fi in r["finals"]:
                T["finals"].append(dict(key=key, split=split, fed=fi["fed"], text=fi["text"]))
            for fed, word, ms in r["stable"]:
                T["stable"].append(dict(key=key, split=split, fed=fed, word=word, stable_ms=ms))
            for i, a in enumerate(r["advances"]):
                confs = [rd[1] for rd in a["readings"]]
                top = a["readings"][0][0] if a["readings"] else None
                for rank, (text, conf, delta, rel) in enumerate(a["readings"]):
                    others = [c for j, c in enumerate(confs) if j != rank]
                    T["advances"].append(dict(key=key, split=split, adv=i, fed=a["fed"], ms=a["fed"] / SAMPLES_PER_MS, seg=a["seg"],
                                              grew=bool(a["grew"]), sil_span_ms=a["sil_span"], top=top, rank=rank, text=text, conf=conf,
                                              lead=(conf - max(others)) if others else None, lead_delta=delta, relation=rel))
    return {k: pd.DataFrame(v) for k, v in T.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--streams", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--wheel", required=True, help="which build decoded the audio; refuse to guess")
    ap.add_argument("--harness", default="scripts/partial_states.py")
    ap.add_argument("--args", default="")
    ap.add_argument("--report", action="append", default=[])
    a = ap.parse_args()
    out = Path(a.out)
    (out / "raw").mkdir(parents=True, exist_ok=True)
    tables = load(a.streams)
    dst = out / "raw" / Path(a.streams).name
    if Path(a.streams).resolve() != dst.resolve():
        shutil.copy2(a.streams, dst)
    for rep in a.report:
        if Path(rep).resolve() != (out / "raw" / Path(rep).name).resolve():
            shutil.copy2(rep, out / "raw" / Path(rep).name)
    for name, df in tables.items():
        df.to_parquet(out / f"{name}.parquet", index=False)
    adv = tables["advances"]
    manifest = dict(
        exported=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), harness=a.harness, harness_args=a.args, wheel=a.wheel,
        utter_head=git("rev-parse", "--short", "HEAD"), utter_dirty=bool(git("status", "--porcelain")),
        sources=[dict(file=dst.name, sha256=sha256(a.streams), bytes=Path(a.streams).stat().st_size)],
        reports=[Path(r).name for r in a.report],
        tables={k: dict(rows=len(v), columns=list(v.columns)) for k, v in tables.items()},
        counts=dict(streams=tables["streams"].groupby("split").size().to_dict(), words=len(tables["words"]),
                    gaps=tables["gaps"].kind.value_counts().to_dict(), relation=adv.relation.value_counts().to_dict()),
    )
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    print(f"{out}: " + ", ".join(f"{k} {len(v)}" for k, v in tables.items()))


if __name__ == "__main__":
    main()
