# utter-analysis

Analysis workbench for [utter](https://github.com/pyscape/utter), the
pure-Rust Vosk decoder: tidy exports of its benchmark series and the
notebooks that read them for patterns before a finding becomes a
decision record. Data stays out of git; nothing here runs the decoder.

## What is here

- `export/`: turns a harness run from utter's `scripts/` into tidy
  tables. One row per clip in `clips.parquet`; one row per clip, advance
  and reading in `advances.parquet`; a `MANIFEST.json` beside them that
  names the script, its arguments, the wheel and the tree revision that
  decoded the audio, the source files with their hashes, and the counts.
- `notebooks/`: the explorers, one per benchmark page. Figures are
  Plotly, so the axes are the mouse's: drag to zoom, double-click to
  reset, box-select, hover for the clip.
- `data/`: gitignored. Each export is a dated directory; the raw
  `.jsonl` the harness wrote sits under `raw/` beside the tables, so the
  tables can be rebuilt and the run can be re-read.

## Use

```
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python export/trust.py --testing RUN.clips.jsonl \
    --validation RUN.validation.clips.jsonl --out data/DATE-trust \
    --wheel "how the audio was decoded" --report RUN.md --report RUN.json
.venv/bin/jupyter lab notebooks/trust.ipynb
```

The decode happens where utter's tree wheel is; the analysis needs only
the tables, on any machine with Python.

## Provenance

A figure is only as good as the runtime that decoded its audio. Every
export carries the manifest, and a notebook prints it first. A run whose
wheel or revision is unknown is not exported.
