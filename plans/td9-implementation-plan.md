# TD-9 implementation plan: relation and lead_delta on the partial

## 0a. Corrections after the owner's review (/tmp/td9-review.md) - these supersede conflicting text below

Promise: give hosts each reading's relation to the current partial and
the change in its competitive margin, at a defined decoding cadence
over all surviving groups, so they decide better about acting or
waiting; preserve text, timing, endpoints, ordering and the output
with the new keys removed; thresholds stay the host's; the cost of the
evidence is measured. Not promised: accuracy, a calibrated probability,
per-word readiness, onset prediction, or the consumer's acceptance.

1. Fields: exactly `relation` and `lead_delta`. Every remaining mention
   of age_ms (map, JSON, tests, strip-key gates, open questions) is
   void. The identity gate strips both new keys, relation included.
2. Clock: one grouping per network chunk decoded, inside the drain
   (advance_decoding), not once per accept; one grouping feeds both
   the history and the traced top n. Lifecycle to specify and test:
   n=1 requested (history still over every surviving group; the lead
   is null only when one group survives), n changed with no new audio
   (re-trace, history untouched), alternatives disabled then enabled
   (history starts at the next chunk), repeated partial() calls (memo),
   endpoint/reset (history cleared), one accept spanning several chunks
   (one sample each).
3. Oracle for the tracker: a diagnostic trace (stream --trace-groups)
   that records every group with the decoded frame count at each
   chunk; the harness's top-n series cannot verify unseen history, and
   a reading entering the top n may rightly have a runtime delta where
   the harness has null. Compare runtime floats to reconstructed ones
   within a stated tolerance (confidences are printed to six decimals).
4. Trust page: baselines are fitted-gap, gap+entropy and hold-only;
   all thresholds and operating points frozen on validation (the
   equal-delay/equal-catch scans on testing are descriptive only);
   report realized testing delay/catch with intervals. Attribution as
   the record now states: recalibrated gap 7,998 -> 8,083 correct at
   trust 0.9; motion +27 more, seven fewer revisions caught.
5. States page, onset section: exploratory. Add baselines (candidate
   presence, candidate lead, elapsed silence, timing-only), score
   alarms over all non-speech including right after words, one-to-one
   event matching, detection after onset vs prediction before it
   reported apart; the exact README rule (extender before a first
   word too) measured on its own, with varied pause distributions and
   continuous recorded commands. The 521 ms figure is withdrawn as an
   acoustic warning (736 of 890 calls preceded any sample of the word).
6. Lattice: deferred, not closed; the merge census, if instrumented,
   reports local collisions and lost readings as separate quantities
   and does not claim to settle it.
7. Diagnostics (1d): a changed final under a wider beam is search
   sensitivity, not proof of a search error; the widest-beam oracle
   rate is not a model ceiling; report observations before causes.
8. Consumer promise: separate item; a concrete host policy validated
   on the consumer's continuous recordings and configuration (12-frame
   chunk, five languages): false commands in room-only audio, lost
   correct commands, readiness latency.
9. Restored from the original after the omissions review: the trust page
   scores at the sighting AND one advance later, reports availability
   at each on both the runtime's all-group history and the harness's
   top-n; compares at equal delay with validation-chosen targets and
   flags any later drop in catch at equal delay; the states page keeps
   candidate preview (52%, one advance, one in six) as its own measured
   result with presence/lead vs motion baselines; README examples for
   prefix/differs/extends, nulls, absent competitors, TD-8's clock.
10. Delivery: commit series includes the states page and its script;
   the Implemented-by marker for the harness is the real symbol
   (scripts/partial_trust.py's trace function as it exists after
   step 4), never a guessed one.


Working plan, not a repo document. The record is
docs/td/0009-trust-is-the-readings-motion-not-a-lattice.md. Steps in
order; each has what it produces and what would send the record back
for an edit before code lands.

## 0. Standing

- Runtime today: one token per FST state, a single backpointer chain
  (src/decoder.rs `Link`/`Token`), readings = surviving tokens grouped
  by word sequence, cheapest per group (`Decoder::alternatives`),
  recomputed on every `Recognizer::partial` call. No history across
  blocks except `stable` (per word position on the best path,
  `update_stable`, run once per advance under the TD-7 memo).
- Harness today: scripts/partial_trust.py records only the
  first-sighting block (one-shot `shown`), although `feed` calls
  `on_partial` on every block.
- Gate for any runtime change: byte identity of partial text, segments
  and word times over the gate corpus (the run TD-7 quotes, 42,878
  blocks, via `stream` JSON lines diffed), G4 (`scripts/g4.py`), and
  `rr index && rr verify` at 0 findings.

## 1. Measurement first, harness only (running, Opus agent)

Extends scripts/partial_trust.py in place; output to this scratchpad
(partial-trust-motion.md + .clips.jsonl). Nothing under src/ or docs/
changes. Features are defined exactly as the record's fields so the
figures transfer:

- advance = a block whose readings list changed; ms between advances
  (verifies the 240 ms the record states).
- per reading (identity = text): first seen, lead = confidence minus
  best other, lead_delta = lead now minus lead at previous advance
  (None if absent then), age_ms, advances_alive; churn; entropy and
  its delta.
- at first sighting: gap (level), age_ms/lead_delta of rank 0,
  lead_delta of rank 1, the displaced leader's delta, had_history.
- at the next advance: the same, plus hold_ms and whether the word
  already changed.
- merge-loss proxy: a reading within 2 nats of the leader at advance
  k absent at k+1.

Decision rules, applied to the record before step 2:

| finding | record edit |
|---|---|
| lead_delta separates within gap buckets (AUC away from 0.5) at first sighting or after one advance, or the logistic gains AUC over gap alone | keep "Every reading carries its lead's motion" as written |
| lead_delta adds nothing at equal level in both places | drop that ruling and the key; the record keeps the lattice ruling, the memo ruling and the measured rejection of motion (title changes) |
| age_ms adds nothing beyond stable_ms and lead_delta | drop "A reading is a word sequence with an age"; keep identity text inside the motion ruling |
| motion defined at first sighting on few clips but useful after one advance | keep both; Consequences already says the leader's own motion arrives one advance late; README reads it on the hold, not the sighting |
| ms between advances is not ~240 at 40 ms blocks | correct the figure in "Readings are read once per decoding advance" |
| merge-loss proxy is frequent and clips with it revise more | the lattice ruling stands as written (it names the number); next plan item becomes top-k tokens per state, a separate record |

### Outcome of step 1 (testing 9230 sightings, validation 8322 for fitting; tree wheel, rerun done)

- Advances: every one of 21,315 intervals exactly 240 ms; first at
  400 ms; 3 per clip on 10,461 clips. Record figure confirmed.
- Availability: rank 0 new at the sighting on 58.9%; had_history
  40.7%; displaced_delta defined 37.6%; entropy_delta 91.8%.
- lead_delta: KEPT. Within gap buckets 0.51-0.65 where defined;
  held out R1-R0 = +0.0035 [0.0017, 0.0055]; McNemar 35/147
  p = 1.6e-17; +112 correct of 9230 at trust 0.9 (119 fewer good
  words held to the end, mean delay 58 vs 65 ms); +14 revisions at
  equal delay (1065 vs 1051); 61 vs 65 ms at equal catch. Small on
  trust; its keep is decided with partial-states.md (the states are
  what it is for).
- age_ms: DROPPED per the table. AUC 0.42 (0.58 inverted), 0.54-0.56
  within buckets, logistic coefficient +0.0006. Re-add only if the
  states page shows a use (how long an extends reading has formed).
- Entropy of the readings' softmax: 0.88 AUC at the sighting, 0.59-0.69
  within every bucket, always defined. Host-side (record unchanged);
  the README gains it beside the sigmoid.
- Hold one advance: available on 54.7%; on 85% of those the advance is
  the clip's last; revision already visible on 97% of revisions there.
  The split cannot separate the wait from the motion; the built stream
  can (multi-word utterances where the next advance is not the final).
- Merge-loss proxy: before 56% of sightings; revision 7.7% with vs
  18.6% without. Predicts survival. Lattice question closed; the record
  says so.
- Coefficients barely move with provenance (validation-fit 0.880,
  split-half 0.877, in-sample 0.881): the protocol was cheap insurance.

### Findings that are not about motion

1. REPRODUCIBILITY: RESOLVED, and it changes what the figures are.
   The consumer venv's utterpy is pinned at utter rev 248cd20
   (2026-09-11), 17 src commits behind the tree: before the fixed
   StateHasher (80cbb03, b6f7850), before TD-6's graph scaling of
   finals, TD-7's memo and TD-8's floor. Reproduced: 8 fresh venv
   processes on zero/bb05582b_nohash_1.wav split 4:4; the tree's
   `stream` binary 8/8 identical (dither 0 and default); the wheel
   built from the tree at <scratchpad>/pylibs 8/8 identical under the
   harness's own settings (rep_utterpy.py). The grammar's counts are a
   BTreeMap; no seeded map in the tree reaches an ordering decision.
   Consequences and actions:
   - The trust agent's first decode ran on the stale wheel (my prompt
     named the venv python without PYTHONPATH); rerun on the tree
     wheel, done: the label moved by 4 revisions (TD-6), no conclusion
     moved, and the Outcome block and the record carry the tree
     figures. Decode is also 185 s vs 320 s per split (TD-7).
   - docs/benchmarks/partial-trust.md reproduces exactly from the tree
     wheel (1147 revisions, every bucket and hold row), so it was
     tree-equivalent; the stale wheel alone caused the 1151/1153 drift.
     What it lacks is a provenance line (speech-commands.md has one):
     add `sc.provenance()` to its header when the script lands.
   - `provenance()` in scripts/speech_commands.py reports the repo's
     HEAD (`git rev-parse` in scripts/), not the wheel's revision, so a
     page's "utter aef2ce6" proves nothing about which runtime ran.
     Fix: utterpy exposes the utter revision it was built from (a
     build-time env var or the pinned rev from its Cargo.lock) and
     provenance() prints that beside the module path; a page whose
     wheel rev differs from HEAD says so.
   - The page's determinism pass (200 clips, fresh process) cannot see
     a 0.05% tie rate. Replace with the whole split decoded twice in
     fresh processes, diffing every partial's readings and the finals.
   - The build-side pin already exists and is machine-local:
     ~/Repos/utterpy/.cargo/config.toml (untracked) patches utter to
     ../utter, so any build there is the tree. The stale part is only
     the installed artifact. A symlink cannot fix that: the .so is
     compiled and must be rebuilt after any Rust change, and a symlink
     in the consumer venv would run the tree under the consumer app.
   - Benchmark venv = utterpy's own (~/Repos/utterpy/.venv: python
     3.14.4, maturin 1.15.0): once `pip install vosk numpy`; after any
     tree change `.venv/bin/maturin develop --release` rebuilds and
     installs in one step. Scripts run from that python. No PYTHONPATH,
     no pip --target, no scratchpad wheel. docs/benchmarks/README.md
     and the memory say so; the consumer venv is left alone.
   - Provenance: utter's build.rs records `git rev-parse HEAD` (+dirty)
     into a `REVISION` const (no dependency; TD-2's policy holds);
     utterpy re-exports it; provenance() prints it beside the module
     path and flags a mismatch with the repo HEAD.
   - DONE: utterpy's venv has vosk and numpy; `maturin develop
     --release` installed the tree build (editable); 8 fresh processes
     identical (e67aec127b8f, the pylibs hash). Scripts run from
     ~/Repos/utterpy/.venv/bin/python from here on.
2. `scripts/speech_commands.py` `mcnemar` overflows (`2.0**n`) past
   ~1020 discordant pairs; the agent added a log-space one local to
   partial_trust.py. Fix the shared helper in log space (own commit)
   and drop the local copy.
3. KALDI IS ON THE MACHINE: ~/Repos/kaldi (vosk branch tip) and the
   release-matched worktree ~/Repos/kaldi-93ef0 (the 0.3.45 wheel's
   commit, from its version string; feature/decoder code byte-identical
   to the tip). A full oracle: online2-wav-nnet3-latgen-faster for
   libvosk-equivalent decodes with lattices and per-frame posteriors,
   for the attribution work in 1d.
4. DONE (uncommitted): the quiet-frame CMVN rule is in src/ivector.rs;
   quiet clips 1.41e-5, twelve takes 3.49e-4; G2 corpus byte-identical
   before/after (0 of 42,878 blocks, 0 of 209 segments), so the 12
   missed segments are NOT this - next suspects: the network's float
   summation order (the G1 MFCC residual's mechanism), label placement
   in the lookahead composition, tie-breaks among equal-cost tokens.
   Public pages rerun on the patched build: Speech Commands finals
   identical to the wheel on the same 10,913 of 11,005, same 92
   disagreements, no clip moved; trust page revisions 1147 -> 1147,
   buckets +-2 clips, R1-R0 0.00351 -> 0.00350; states page away F1
   0.1217 -> 0.1218, momentum r 0.2138 -> 0.2137. The committed pages
   stay valid; no regeneration needed for this change. Harness bug
   found on the way: speech_commands.py --steady-state-clips 0 divides
   by zero instead of skipping the pass (steady_state_pass: step =
   len(clips) // seconds); one-line guard, with the mcnemar fix.
   History of the item:
   (was) G1 i-VECTOR HALF FAILS; THE FIX IS THE TOP PARITY ITEM. The wheel's
   Kaldi skips the online CMVN stats update for a frame with raw c0 <=
   --cmn-min-energy (50.0; ecb4b4715, ancestor of 93ef0) and re-smooths
   the previous frame's smoothed stats instead; utter's
   IvectorStream::cmvn_frame (src/ivector.rs) computes the window every
   frame (upstream). Quietest clip per word: 1.86e-1 relative (gate
   1e-2), 10/10 fail; with the skip off in Kaldi 1.04e-5. Reach: 9.97%
   of testing-split frames, 34% of clips, runs up to 93 frames; the
   first take set (first clip per word) had none and passed, which is
   why the verdict flipped. Fix: read cmn-min-energy from the model's
   online_cmvn.conf (default 50.0), replicate OnlineCmvn::GetFrame's
   branch exactly (skip ComputeStatsForFrame, smooth from the previous
   temp stats), unit test against the Kaldi rows for the quietest
   clips (g1.py), then: byte identity on the gate corpus WILL break by
   design (the corpus has quiet speech) and agreement with libvosk is
   what is measured instead - G2 partial and segment agreement before
   and after (the 12 near-tie segments are the first suspect), the
   Speech Commands agreement pass, and every benchmark page rerun
   (trust, states) as the regression rule requires; TD-9's figures were
   measured on the divergent front end and are re-measured then. Own
   commit; a sentence in TD-2's front-end i-vector section.
5. MFCC bound for the owner: TD-2 states "MFCC frames within 1e-3"
   (absolute); against Kaldi proper on loud public frames every port
   is at ~1.3e-2 absolute and 1e-4 relative. A relative bound (1e-3)
   holds everywhere; changing TD-2's Verification section is a record
   edit (rr search 'TD-2#Verification and acceptance').

## 1b. The before/after benchmark (fixed before the after-figures are read)

The question the page must answer: is a host's prediction of whether a
partial's word will hold better with the motion than without, at the
same delay, on held-out clips. Everything below is decided now, so the
after cannot be tuned to the test set.

Target (unchanged, so the before is the page as it stands): the first
word shown survives to the final. Secondary, so a rule that helps only
later words shows: every rank-0 word at the advance it first appears.

Splits: Speech Commands ships validation_list.txt and testing_list.txt.
Fit every coefficient and threshold on validation; report every
headline figure on testing. The harness gains `--split`. Until the
validation decode exists, a split-half of testing by a fixed rule
(clip index parity) is the interim hold-out and is labelled as such.

Rules compared, all scored on the identical clips:
- R0, before: sigmoid(gap) at the sighting; the README's rule.
- R1, after, same moment: gap + motion available at the sighting
  (the displaced reading's lead_delta, rank 0's age_ms/lead_delta
  where defined, missing as null with an indicator). No added delay.
- R2, after, on the hold: the same rule read at the first advance
  after the sighting; charged its delay.

Scores, each paired on clips:
1. Discrimination: rank-AUC against revision; paired bootstrap over
   clips (1000 resamples) for the difference R1-R0 and R2-R0 with a
   95% interval. Better = the interval excludes zero on the right side.
2. Calibration: the existing gap-bucket table for each rule; expected
   calibration error beside it.
3. The host's trade, on a delay axis in ms: for each threshold, the
   share of revisions caught (held past the final) and the median and
   p90 ms of audio from the sighting to the block the rule first clears
   on good words (never clears before the final = held to the final).
   Better = at equal median delay, more caught; at equal caught, less
   delay. Report the curve and the values at the README's operating
   point (trust 0.9, gap ~2.2 nats). R2's delay includes the advance.
4. Exact McNemar at the operating point: a clip is handled correctly
   when it is revised and held, or good and released; the discordant
   pairs between R0 and R1 (and R0 and R2) give the test, the repo's
   convention for paired engine comparisons.
5. Availability: the share of sightings where each motion figure is
   defined, since a figure that is null on most sightings cannot
   improve R1 no matter its AUC on the rest.
6. Momentum, as distinct from velocity: persistence of a reading's
   lead velocity across consecutive advances (Pearson r and sign
   agreement of (lead_delta_k, lead_delta_k+1)) by |lead| band; the
   same for the reading's softmax share of the beam; and the leader's
   next-advance velocity by outcome. First measurement, offline from
   the recorded series (scratchpad, this session): lead r = +0.41 at
   |lead| 1-4 nats (61% same sign), +0.20 below 1, -0.07 at >= 4
   (overall +0.08, n 3185); share r = +0.03 (none: bounded, saturates);
   leader on the hold: survivors mean next delta +1.83, revised -5.33
   (n 1517 / 79); only 854 of 63,420 readings (1.3%) live three
   advances, the chunk's limit. Add as a page section in
   partial_trust.py; report the forward figures only (the consistency
   of a word's deltas over its whole life, 90% positive for survivors
   vs 44% for revised, is partly consequence and is not reported as a
   predictor).
7. Velocity by band, the interaction that makes momentum usable: the
   AUC of lead_delta for survival WITHIN each |lead| band (<1, 1-4,
   >=4). If velocity predicts in the contested band and not past it,
   the README's read is "weigh the velocity while the lead is under 4
   nats, ignore it past", with the boundary from the page. Also a
   reversal indicator on the hold, sign(lead) != sign(lead_delta) for
   the leader (leading but losing): its precision/recall for "rank 0
   changes at the next advance" and its incremental AUC over the gap.
   The decomposition this gives a host: lead = where the word stands
   (accumulated evidence); lead_delta = what the last chunk said (new
   evidence); momentum = whether new evidence tends to continue, a
   property of the band the page reports, not a field.

Outputs: the page's tables in utter, plus partial-trust.json with every
figure; the raw series and the tidy tables go to ~/Repos/utter-analysis
(export/trust.py, notebooks/trust.ipynb), never into utter. That repo's
notebook reproduces the momentum figures exactly.

Outputs (as first written): the page's tables, plus partial-trust.json with every figure
and partial-trust.clips.jsonl with the per-advance feature series per
clip from the sighting to the final (not only the sighting and the
next advance), so any rule's delay-to-clear can be recomputed without
decoding. The before-figures are frozen from the current page; the
page becomes a regression benchmark: every decoder change reruns it
and a drop in revisions caught at equal delay is a finding.

Parity gate after the runtime lands: the harness reads age_ms and
lead_delta from the JSON and asserts equality with its own derivation
on every sighting (3.4 below); the after-figures from the runtime's
fields must equal the after-figures from the harness's derivation.

## 1c. Silence direction and word transitions (a page of their own)

Two more questions the same series answers, benchmarked on a built
stream because single clips carry no transitions and no finishes.
New script scripts/partial_states.py -> docs/benchmarks/partial-states.md
(+ .json, + .streams.jsonl). Held out like 1b: streams built from
validation clips fit, streams built from testing clips score.

### Ground truth, all from the public dataset

- Inside a clip: the word's energy onset and offset, the first and
  last 10 ms frame within 20 dB of the clip's peak (speech_commands.py
  `energy_end`; add the mirror `energy_start`). Independent of the
  decoder.
- Between clips: the stream is built, so every word's sample position
  is exact and every gap's length is chosen. Gaps are cut from the six
  background recordings (dishes, miaowing, bike, pink, tap, white),
  scaled to a fixed floor (about -50 dBFS), never digital zeros (the
  floor tracker treats those apart, TD-8). Pause gaps 100-800 ms
  uniform; finish gaps 2-3 s; N words per utterance 1-5; fixed seed so
  both engines see the identical stream.
- Pure non-speech: the recordings themselves, fed continuously, as the
  noise pass does.
- Caveat on the page: isolated read words joined lack coarticulation
  and prosody, so transitions are cleaner than dictation; the private
  gate corpus is where TD-8's figures come from, this is the
  reproducible counterpart.

### A. Silence direction: toward, away, maintaining

Forecast labels at every block t, from the ground-truth timeline over
the next W ms (W = 240 ms, one advance, and 500 ms): toward silence =
speech at t, silence by t+W; away from silence = silence at t, speech
by t+W; maintaining = silence throughout; (maintaining speech = the
fourth, reported but not the question). Predictor reads only the
partial at t.

Rules:
- R0, before, TD-8's reading of the fields: toward = trailing [sil]
  entry span past a bound (300 ms, TD-8's figure); away = a word
  appears at rank 0 (detection, zero lead); maintaining = the trailing
  span growing, no word.
- R1, after: R0 plus the motion: at utterance start the [sil]
  reading's lead_delta (negative = a word is coming); mid-utterance the
  `extends` reading (relation derived from text in the harness
  until the runtime reports it) present with lead_delta > 0 = away,
  absent while the trailing span grows = toward/maintaining.

Scores, paired on blocks:
1. Per state, precision and recall of the forecast at each W.
2. Lead time: per true transition, ms from the block the rule first
   calls it to the ground-truth transition (negative = before). The
   distribution, and the share called before the transition.
3. False alarms per minute on the recordings alone (maintaining must
   never read as away) and on finishes (toward must not read as away).
4. The end-of-speech confusion, TD-8's core problem, in public form:
   among silent stretches, at each ms of trailing silence the share of
   pauses mistaken for a finish against the share of finishes called,
   with and without the extending rival's motion. TD-8's private
   figures (300 ms bound: 87% of finishes early, 4.5% of pauses
   mistaken) get their public counterpart. A gain here changes TD-8's
   "End of speech is the endpoint, and the trailing silence entry is
   its clock": rr search 'TD-8', revisit every citation.

### A2. How silence persists, in velocity and momentum terms (sent to the states agent)

Hypothesis, to be confirmed or refuted on the streams: silence is kept
in the beam not as a growing lead but as a hovering one. In a quiet
room the [sil] reading (before a word) or the leader against its
`extends` readings (after one) faces freshly started word hypotheses
that are pruned and reborn every few frames, so its best rival is
always young and its lead is bounded by a young rival's deficit: the
lead hovers, velocity sits near zero. Speech beginning shows as the
lead dropping (negative velocity) as a word's first phones score, and
momentum in the 1-4 nat band means that drop tends to continue, so
"away from silence" is callable one chunk before rank 0 flips when
the onset spans two chunks. Measured on the page: the silence
signature (lead and velocity distributions in kept silence and on the
recordings, the best rival's age); transition-aligned velocity at
advances -3..+2 around every onset and offset for the [sil] reading,
the leader and the best `extends` reading; the lead time of a fitted
velocity crossing and its false-alarm rate in kept silence; momentum
by band on the streams, where readings live long enough to measure it.

The trailing [sil] entry's span stays the clock (TD-8): it is position
in silence-time, monotone while silence persists, reset by speech;
velocity and momentum are the beam's complementary view, whether the
word hypotheses are gaining. The page reports whether that view adds
lead time over the span (R0 vs R1 in A), which is the only thing that
would change TD-8.

### B. Transitioning between words

Per ground-truth transition word i -> word i+1: word i's offset, word
i+1's onset and label, the gap.

Signals: the extending rival, its extra word, its first appearance
(advance), its lead trajectory until it takes rank 0 or dies; the
inter-word [sil] entry's span once word i+1 shows; the trailing [sil]
span during the gap.

Scores:
1. Preview lead: advances (and ms) between the extending rival's first
   appearance and word i+1's first appearance at rank 0. If this is
   mostly zero the beam does not foresee a word and the page says so.
   (The trust agent's had_history figure is this at the first word.)
2. Preview accuracy: while an extending rival exists in a gap, how
   often its extra word equals word i+1's label, top-1 and top-3 among
   extending rivals, by lead time.
3. False transitions: extending rivals that appear in a finish or on
   the recordings and die, per minute; and in pauses, wrong-word rivals
   that lead briefly (the flicker the trust page counts as a revision).
4. The pause's measure: the inter-word [sil] span against the built
   gap, mean and p90 error in ms; the trailing [sil] span during the
   gap against elapsed silence, per advance.
5. Transition latency on continuous audio: onset of word i+1 to its
   first appearance at rank 0 and to its hold clearing, per
   transition, beside the per-clip figure the speech-commands page
   gives.

Before/after: R0 = the host sees the transition when rank 0 changes;
R1 = the host reads the extending rival's motion. Paired on
transitions; the lead-time curve; McNemar at the operating point.

The stock wheel runs the same streams for what it has (partial text,
word times with SetPartialWords): the detection baseline, not the
motion.

### Outcome of 1c (testing streams: 75 streams, 78.6 min, 2208 transitions, 1458 pauses, 750 finishes; tree wheel)

- Advances 240 ms exact (15489 of 15491 intervals).
- lead_delta: KEPT, now on the states evidence. The away read (an
  `extends` reading with lead_delta > 0): F1 0.025 -> 0.122 at W=240,
  0.075 -> 0.252 at W=500, bootstrap intervals clear of zero, McNemar
  259/0 p=2e-78; as a crossing detector precision 54%, 40% of onsets
  called, lead p50 -521 ms, 0.13 alarms/min in kept silence, 0.00 on
  the recordings.
- The [sil] reading's velocity is NOT an onset read: flat at -3..-1
  advances, falls only at +1 (-2.03); the validation fit switches any
  threshold on it off; as a crossing it costs 110-132 alarms/min. The
  README read is "an extends reading gaining", never "[sil] falling".
- Hover hypothesis: holds. Kept silence = [sil] leading (3907/3909
  finish-gap interiors, 1584/1584 recording advances), lead 4.22 +- 0.79
  (finish gaps) / 5.16 +- 1.36 (recordings), velocity p50 -0.05 / +0.01.
  Young-rival bound holds after a word (rival age p50 480 ms) but not on
  cold recordings (p50 2880 ms): rivals hover too.
- Momentum by relation (1-4 nat band): all +0.21 (12244 pairs); [sil]
  +0.45; extends -0.28; differs -0.20. Not one phenomenon; the record
  says so.
- Preview: the coming word's reading present before rank 0 grows on
  52.5% (median 240 ms, p90 720 ms); top-1 right 15.7% at 240-480 ms
  lead, top-3 31.2%; ~1.5% beyond 480 ms. One advance of warning, weak
  on identity.
- End of speech: the trailing-span bound fitted at 500 ms on this
  stream (300 ms: 81.3% of pauses mistaken, 96.4% finishes called;
  500 ms: 12.8% / 42.8%). The mistake rate is a function of the built
  pause length (uniform 100-800 ms): 56% at 100-200 ms, 96% at
  600-700 ms at the 300 ms bound; TD-8's private 4.5% reflects real
  pause lengths. The extends-motion veto: 81.3 -> 31.4% mistaken but
  96.4 -> 41.3% called at 300 ms. A trade. TD-8 UNCHANGED; docs step:
  add to TD-8's Considered options "The beam's motion as the endpoint:
  measured on the built stream, a pause filter that pays in finishes"
  with the page's marker once the page is in docs/benchmarks.
- Toward-silence: no gain (-0.005, interval excludes zero). Maintaining
  silence: R0's rule, unchanged.
- Leading-but-losing (rank 0 with lead_delta < 0) for "rank 0 changes
  next advance": precision 20.5% / recall 67.3%; in the 1-4 band 24.8% /
  84.1%, where lead_delta (0.83 inverted) is as strong as the level
  (0.82). For "rank 0 unlike the final" the level wins.

### Surprises from 1c, for 1d (attribution)

1. PHANTOMS AFTER A WORD: false away calls 10.5/min (R0) in finish
   gaps but 0.00/min on the recordings alone; false extenders that die
   265/min over silence inside finish gaps vs 21/min on recordings. A
   word primes phantoms in the noise that follows it. TD-8's private
   corpus saw no phantom on quiet blocks; its gaps were room silence,
   these are recordings at -50 dBFS after a word. Attribute: bigram
   state after a word vs the start state; i-vector adapted to the
   speaker; the gap floor level (sweep -60/-50/-40 dBFS). Also: the
   arriving word is right on 84.9% first-in-utterance but 50.8%
   mid-utterance, because the phantom that grew in the pause is counted
   as the arrival; re-score with the phantom excluded.
2. rule2 (0.5 s trailing silence after a word) closes the utterance
   inside 64.6% of built pauses, so most mid-utterance transitions are
   restarts and the inter-word [sil] span is readable on 157 of 1458
   pauses (mean error -144 ms, p90 |err| 274 ms). Parity behaviour;
   TD-8 accepts it. The stream's pause distribution should be reported
   beside every figure it drives.
3. The trailing [sil] span against the decoder's own word end is a
   constant -160 ms (p10 = p50 = p90): the entry ends at the last
   decoded frame, four blocks behind the audio fed. A host adding its
   bound to the span should know the span lags the audio by the
   chunk; README note.
4. Stock wheel: with SetPartialWords(True) its partial text goes empty
   on most blocks (24 of 1374 vs 510 without); utter's is 510 either
   way. libvosk's partial-words path is lattice-derived and trails.
   Worth a sentence in the README's "What a partial carries" table and
   the states page; a G4-adjacent parity note, not a defect in utter.
5. sc.mcnemar overflow hit again (>1023 discordant); both new scripts
   carry a local log-space version. Fix the shared helper (item in
   findings above) and delete both locals.

## 1d. Diagnostics: from a score to a change

The pages above say whether a host is better off. They do not say
what to change in the decoder, because a revision or a miss is not
attributed to a stage. Three additions do that; each is cheap because
the per-advance series and the readings are already recorded.

### Oracle-in-beam: scoring, search, or model

At the first sighting and at the final, is the true word among the
readings at all? Three outcomes, three levers:
- present and leading: nothing to change;
- present but ranked below: a SCORING problem (bigram cost, graph
  scale, acoustic scale), the kind TD-6 found; the lever is a cost;
- absent: a SEARCH problem (pruned) or the MODEL's; separated by the
  beam sweep below.
Both engines: `SetMaxAlternatives(n)` on the final (vosk's lattice
n-best, utter's beam n-best) and the partial readings at the sighting.
Report the oracle rate at n = 1, 5, 10 and the rank of the truth when
present. Add to speech_commands.py as a pass.

### Search-error rate: the beam sweep, no code change

beam, max-active and min-active come from conf/model.conf and are not
settable per recognizer (utterpy exposes only unknown_cost; `stream`
neither). A sibling model directory (symlinks to am/, graph/, ivector/;
a copied conf/ with a wider beam and max-active) runs both engines at
the wider search, the same trick TD-2 uses for dither. Search error =
clips whose final changes between the stock and the wide beam; if it
is ~0 the beam is not a lever and no host option is needed; if not,
the pair (accuracy gained, compute cost from the steady-state pass)
is the figure a host-settable beam would be justified by, its own
record. The oracle rate at the widest beam is the MODEL'S CEILING
under this grammar: errors above it are not the decoder's to fix.

### Attributing each revision from the series the harness keeps

For every revised first word, from partial-trust.clips.jsonl:
1. resolved by the next advance (97% of revisions where an advance
   follows): the audio was not there yet; inherent at this chunk. The
   only lever is the chunk itself (frames_per_chunk 24 -> 12 would
   halve the 240 ms quantum), and it BREAKS PARITY: libvosk's
   chunking is part of G2's byte identity and the i-vector schedule.
   A record, if ever, with the latency-vs-identity trade measured.
2. truth present at the sighting but ranked below: scoring (above).
3. truth absent at the sighting, present later: label placement in
   the lookahead composition (how early a word's olabel is pushed),
   or pruning; the states page's preview lead is the same lever seen
   from the other side.
4. the rest: noise, a wrong final (the label itself), out of scope.
Report the split. It is the list of levers with sizes.

### Levers the pages already point at

| figure | lever | cost | parity |
|---|---|---|---|
| 240 ms advance quantises every signal; first at 400 ms | frames_per_chunk | more chunks, same frames; i-vector schedule moves | breaks byte identity (G2); own record |
| silence finals, noise false alarms | unknown_cost (TD-8 sweep) | recall of quiet words | additive option, off |
| revisions where truth ranked below | bigram cost, graph scale (TD-6) | parity with libvosk's choices | TD-6 keeps libvosk's |
| preview lead ~0 (if measured so) | olabel placement in composition | latency of the first sighting | G3 latency gate |
| inter-word [sil] span error | word_boundary alignment | none | word times gate |
| compute per block | kernels, memo (TD-3/5/7) | none | none |

### Finer readings: more samples per word without breaking parity

The series is one to three samples per word because readings change
only at an advance (240 ms). Two ways to more, in this order:

1. PER-FRAME TRACE, parity-safe. `advance_decoding` steps the decoder
   one output frame at a time through the chunk's eight frames, so a
   token set exists every 30 ms; only the chunk's end is read. A
   `stream --trace-frames` mode reads the readings after every frame
   (the grouping walk, eight times per chunk; not the product path)
   and writes them in the states/trust series shape. The end-of-chunk
   partial and the acoustics are byte-identical. Gives 8 samples per
   advance, resolves where in the chunk the evidence arrived; samples
   inside a chunk are correlated (same acoustics), so it is finer
   timing, not 8x information; nothing arrives earlier in wall time.
   Product read, if the trace shows it earns one: a last-frames
   velocity beside the chunk's. Export/notebook: same tables with a
   `frame` column; momentum r by band with bootstrap intervals before
   and after, per-word sample counts.
2. CHUNK SWEEP by sibling conf, no code. frames-per-chunk is read from
   conf/model.conf (model.rs), so a sibling model directory (symlinks
   to am/, graph/, ivector/; a copied conf/ with --frames-per-chunk=12,
   then 6) runs utter at 120 / 60 ms advances; libvosk should honour
   the same conf (verify: vosk's model.cc registers the decodable
   options it parses model.conf with). Measure both engines at each
   chunk: G2 agreement against the stock-chunk libvosk (expected to
   fail by construction: the i-vector each chunk sees moves), first
   appearance latency (G3), compute per block (steady state), first
   advance time, and the estimate tightening from (1)'s figures. An
   OPTION with measured divergence and its own record if kept; never
   the default, since parity is the contract.
   Stock vosk cannot go finer: same chunking, and its partial-words
   path trails and empties the partial.

### What the pages cannot show

The acoustic model is a stock Vosk model: its errors are the ceiling,
not a lever, and the oracle rate at the widest beam measures it.
Most first-word revisions are acoustic and resolve with the next
chunk; the improvement there is in the host's reading (the hold, the
entropy, the motion), which is a README change, not a decoder one.
The benchmark's job for those is calibration, and it does that.

## 2. Runtime

### 2a. src/decoder.rs: split the grouping from the trace

- Private `grouped(&self, use_final) -> Vec<(Vec<Label>, rank f32, cost f32, &Token)>`
  sorted exactly as `alternatives` sorts (rank, then newest seq).
- `alternatives(&self, use_final, max)` = `grouped` -> truncate ->
  `trace`; output byte-identical to today.
- Public `reading_costs(&self, use_final) -> Vec<(Vec<Label>, f32 cost)>`
  (all groups, in rank order) for the tracker. Partials use
  `use_final = false`, where rank == cost, so lead needs only the
  smallest and second-smallest cost: lead_i = min_{j != i} cost_j - cost_i.

### 2b. src/recognizer.rs: the memo and the series

New fields on `Recognizer`:

- `readings: Option<Vec<Path>>`, `readings_frames: Option<usize>`,
  `readings_n: usize` (the n the memo was traced at) - TD-7's memo
  pattern; `partial` recomputes only if the count or n moved.
- `history: HashMap<Vec<Label>, Reading>` with
  `Reading { born: u64 /* sample, the clock update_stable uses */,
  lead_prev: Option<f32>, lead_now: Option<f32> }`.

`update_readings(&mut self)`, called in `accept` beside
`update_stable`, when `partial_alternatives > 0`:

1. Return if `readings_frames == Some(decoded)`.
2. `groups = dec.reading_costs(false)`; compute each lead (None when
   one group).
3. Rebuild the map: for each group, `old.remove(&words)` -> Some(h):
   carry `born`, `lead_prev = h.lead_now`; None: `born = now`,
   `lead_prev = None`. Set `lead_now`. Leftovers in `old` died (a
   returning sequence is born again, per the record).
4. Trace the top n into `readings`; set `readings_frames`, `readings_n`.

Clearing: wherever `self.stable.clear()` runs (decoder restart after
an endpoint) and in `forget_best_path` (rebuild/clean_up), also clear
`history` and the readings memo. The record says restart clears
history.

(age_ms dropped after step 1: the map holds lead_prev/lead_now only,
no birth sample.)

Relation, per group against rank 0's `Vec<Label>`: equal -> "same";
proper prefix of rank 0 -> "prefix" (the empty sequence included);
rank 0 a proper prefix of it -> "extends"; else "differs". Exact from
labels; no text.

JSON, in `partial`'s alternatives loop: after `result` (when partial
words are on), append
`, "relation": "<s>", "lead_delta": <number|null>` using
`escape_json_number`; `age_ms = ((now - born) / rate * 1000).round()`,
same arithmetic as `stable_ms`; `lead_delta = lead_now - lead_prev`
when both are Some, else `null`.

No change to src/capi.rs, include/utter.h or utterpy: the ABI passes
the JSON string through.

### 2c. Tests

- tests/model.rs, with the model present: decode a clip with
  alternatives on and partial words on; assert on the sequence of
  partials that (i) rank 0's `age_ms` is non-decreasing while its text
  holds and resets after a final; (ii) `lead_delta` is null on the
  first block a text appears and numeric on the next advance where it
  persists; (iii) stripping the two keys gives byte-identical output
  to the existing determinism fixture path (extend `without_floor` to
  also strip them, or add `without_series`); (iv) `relation` is
  `same` on rank 0, `prefix` on `[sil]` while a word leads, and
  `extends` on a reading one word longer than the partial.
- src/recognizer.rs unit test on the map rebuild alone (no model):
  born/carry/die/rebirth and the null rules, with hand-made groups.

## 3. Gates

1. `stream` over the gate corpus before and after, at 40 ms, dither 0:
   plain, `--partial-words`, `--alternatives 5 --partial-words`; diff
   the JSON lines; for the alternatives run strip `age_ms`/`lead_delta`
   first (python one-liner over the lines). Expect identical.
2. `scripts/g4.py` rerun: rank 0 == partial on every block, `[sil]`
   rule, census figure unchanged.
3. Speech Commands page: no rerun needed (partial text unchanged);
   rerun only if step 2 touched decoding order (it must not).
4. scripts/partial_trust.py: make it read `age_ms`/`lead_delta` from
   the JSON when present and assert they equal its own derivation on
   every first sighting (the harness's advance detection is an
   independent implementation of the tracker; disagreement is a bug in
   one of them). Then regenerate docs/benchmarks/partial-trust.md from
   the runtime's fields; the page's existing tables must reproduce.

## 4. The lattice number: merge-loss census (decoder instrumentation)

The harness's proxy cannot tell a merge from beam pruning. The decoder
can, cheaply and only when asked:

- `Decoder { census: bool, merges_close: u64 }`; in the `better`
  branches of `process_emitting` and `process_nonemitting`, when a
  token at `nextstate` already exists: if `census` and
  `|existing.cost - tot| < 2.0` and `!Rc::ptr_eq(existing.link, new link)`
  and the two chains' word sequences differ (walk both; rare path),
  `merges_close += 1`. The dropped token is the loser either way
  (existing replaced, or incoming discarded); count both.
- `stream --census` prints the per-take total and a per-block count in
  its JSON line; run over the Speech Commands testing split (a small
  wrapper, or extend `stream` to take a list file); report the share
  of first sightings preceded by a close merge, and the revision rate
  with and without one, on the page beside the harness proxy.
- The counter does not touch decisions; the identity run of step 3
  proves it.

This is the figure the record's first ruling names. If it is large and
correlates with revisions, the next record is top-k tokens per state
(Kaldi's forward links without determinization), not this one.

## 5. Docs

- README "What a partial carries": two rows in the table
  (`relation`, `lead_delta`, absent in the stock wheel, what a host
  does with each), and "How much to trust a partial word" gains the
  entropy of the readings' softmax beside the sigmoid (0.88 AUC,
  adds within every gap bucket, no runtime change), the JSON example gains them on each reading,
  "How much to trust a partial word" gains the motion reading with the
  page's figures, and a new short section gives the four reads in a
  line of Python each, thresholds left to the host:
    trust: sigmoid(gap) (exists);
    a word is coming: an `extends` reading with lead_delta > 0, its
      extra word = text beyond the partial (before a first word the
      extends readings are the word readings; the [sil] reading's own
      velocity is not a read, 1c);
    kept silence: the empty reading leading, lead_delta near zero;
    the last word may not be there: the best `prefix` reading's lead
      (null evidence);
    end of speech: the trailing [sil] entry's span against the host's
      bound (TD-8).
  Figures beside each from partial-trust.md and partial-states.md.
- docs/benchmarks/README.md: the partial-trust row now also names
  motion and the merge-loss figure.
- docs/td/README.md: TD-9 row (done in the draft).
- TD-9 "Implemented by": mint with `rr at` after code lands:
  `update_readings`, `reading_costs`, the census counter, and
  `scripts/partial_trust.py#trace`.
- TD-2 untouched, as TD-8 left it for `floor_dbfs`: the new keys are
  appended and TD-2's order stays a prefix.
- `rr index && rr verify` -> 0 findings before every commit.

## 6. Commit series (owner approves each; nothing pushed)

1. Record TD-9 + index row.
2. Harness: partial_trust.py motion features + regenerated page
   (figures from the harness derivation).
3. Runtime: decoder split + memo + tracker + JSON + tests; identity
   and G4 figures in the message.
4. Page regenerated from the runtime's fields, with the equality
   assertion of step 3.4.
5. Census instrumentation + the merge-loss figure on the page; TD-9
   gains its Implemented by.
6. README and benchmarks index.

Trailer: memory of the owner's earlier ruling says Co-Authored-By only,
no Claude-Session line; this session's harness instruction adds one.
Ask before the first commit.

## 7. Open for the owner

- Whether `lead_delta` should be reported on finals' `alternatives`
  too (the record says no: once per utterance, no series).
- Whether `age_ms` on the `[sil]` reading (usually the utterance's
  age) is worth carrying or should read null; the record carries it.
- The hold-one-advance reading: at 240 ms per advance the delay is six
  blocks, which is the whole of the stock wheel's p90 first-appearance
  latency; the page's figure decides whether the README recommends it.
