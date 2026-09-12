#!/usr/bin/env python3
"""Export a partial_trust.py series (.clips.jsonl) as tidy tables with a manifest.

    python export/trust.py --testing RUN.clips.jsonl [--validation RUN.validation.clips.jsonl]
        --out data/DATE-trust --wheel "how the audio was decoded" [--report FILE ...]

clips.parquet: one row per clip. advances.parquet: one row per clip, advance and reading, with
the reading's relation to rank 0 (same, prefix, extends, differs) computed from the texts.
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


def words_of(text):
    return [] if text == "[sil]" else text.split()


def relation(words, top):
    if words == top:
        return "same"
    if len(words) < len(top) and top[: len(words)] == words:
        return "prefix"
    if len(top) < len(words) and words[: len(top)] == top:
        return "extends"
    return "differs"


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


def load(path, split):
    clips, advances = [], []
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            parts = r["clip"].split("/")
            # Speech Commands reuses a basename across word folders, so the folder is part of the id.
            clip = parts[-2] + "/" + parts[-1].removesuffix(".wav")
            clips.append(
                dict(
                    split=split, clip_id=clip, label=r["clip"].split("/")[-2], word=r["word"], top_word=r["top_word"],
                    survived=bool(r["survived"]), gap=r["gap"], conf0=r.get("conf0"), energy=r.get("energy"),
                    entropy=r.get("entropy"), entropy_delta=r.get("entropy_delta"), lead_delta0=r.get("lead_delta0"),
                    lead_delta1=r.get("lead_delta1"), displaced_delta=r.get("displaced_delta"),
                    had_history=bool(r.get("had_history")), age_ms=r.get("age_ms"), advances_alive=r.get("advances_alive"),
                    churn=r.get("churn"), vanished=bool(r.get("vanished")), sighting_ms=r["sighting_ms"],
                    end_ms=r["end_ms"], n_advances=r["n_advances"], advance_ms=json.dumps(r["advance_ms"]),
                )
            )
            for i, adv in enumerate(r["series"]):
                top = words_of(adv["readings"][0]["text"]) if adv["readings"] else []
                for rank, a in enumerate(adv["readings"]):
                    advances.append(
                        dict(
                            split=split, clip_id=clip, adv=i, ms=adv["ms"], rank=rank, text=a["text"],
                            relation=relation(words_of(a["text"]), top), conf=a["conf"], lead=a.get("lead"),
                            lead_delta=a.get("lead_delta"), age_ms=a.get("age_ms"), gap=adv.get("gap"),
                            entropy=adv.get("entropy"),
                        )
                    )
    return clips, advances


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--testing", required=True)
    ap.add_argument("--validation")
    ap.add_argument("--out", required=True)
    ap.add_argument("--wheel", required=True, help="which build decoded the audio; refuse to guess")
    ap.add_argument("--harness", default="scripts/partial_trust.py")
    ap.add_argument("--args", default="")
    ap.add_argument("--report", action="append", default=[], help="page or json the run wrote; copied beside the tables")
    a = ap.parse_args()

    out = Path(a.out)
    (out / "raw").mkdir(parents=True, exist_ok=True)
    clips, advances = [], []
    sources = []
    for split, path in (("testing", a.testing), ("validation", a.validation)):
        if not path:
            continue
        c, v = load(path, split)
        clips += c
        advances += v
        dst = out / "raw" / Path(path).name
        shutil.copy2(path, dst)
        sources.append(dict(split=split, file=dst.name, sha256=sha256(path), bytes=Path(path).stat().st_size, clips=len(c)))
    for rep in a.report:
        shutil.copy2(rep, out / "raw" / Path(rep).name)

    cdf = pd.DataFrame(clips)
    dup = cdf.duplicated(["split", "clip_id"]).sum()
    assert dup == 0, f"{dup} clip ids repeat within a split"
    adf = pd.DataFrame(advances)
    cdf.to_parquet(out / "clips.parquet", index=False)
    adf.to_parquet(out / "advances.parquet", index=False)
    manifest = dict(
        exported=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        harness=a.harness,
        harness_args=a.args,
        wheel=a.wheel,
        utter_head=git("rev-parse", "--short", "HEAD"),
        utter_dirty=bool(git("status", "--porcelain")),
        sources=sources,
        reports=[Path(r).name for r in a.report],
        tables=dict(
            clips=dict(rows=len(cdf), columns=list(cdf.columns)),
            advances=dict(rows=len(adf), columns=list(adf.columns)),
        ),
        counts=dict(
            revised={s: int((~cdf[cdf.split == s].survived).sum()) for s in cdf.split.unique()},
            relation=adf.relation.value_counts().to_dict(),
        ),
    )
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    print(f"{out}: clips {len(cdf)}, advance rows {len(adf)}; relation {manifest['counts']['relation']}")


if __name__ == "__main__":
    main()
