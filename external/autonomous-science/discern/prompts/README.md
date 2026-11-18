# DISCERN Prompt Provenance

This directory records model-facing prompt provenance for the frozen DISCERN
benchmark and the preliminary Physics extension.

## Core DISCERN

The frozen core contains 203 tasks:
181 L1/L2 worlds and 22 L3 worlds across eight life-science tracks.

## L1 and L2

L1/L2 prompts are preserved exactly from recorded trace artifacts.

Prompt strings can differ across evaluated model runs, runtime versions, or
repetitions. The release preserves these differences rather than replacing
them with a synthetic common prompt.

- `prompt_index.csv` contains one row per canonical benchmark world.
- `recorded_prompt_variants.csv` contains one row per retained model/rep trace.
- `text/sha256/` stores exact prompt strings deduplicated by SHA-256.

Benchmark membership is determined by the canonical benchmark registry for
the core and by frozen manifests for the Physics extension. A trace alone does
not make a world canonical.

## L3

L3 uses a multi-round agent workflow and its canonical result artifacts do not
contain a single standalone `trace.prompt` field.

Each L3 index row therefore records the frozen run manifest and track-specific
dossier implementation used to construct the interaction, together with their
SHA-256 digests. No synthetic L3 prompt is presented as an original prompt.

## Physics extension

The preliminary Physics extension contains 30 worlds:
15 Calorimetry and 15 Nuclear Decay worlds.

It is reported separately and is excluded from the core DISCERN Overall Score.
