# SysML v2 → FCSTM experiments

Independent public research repository for one-way SysML v2 import into
[pyfcstm](https://github.com/HansBug/pyfcstm). Stateflow experiments live in
[their own repository](https://github.com/HansBug/stateflow-experiments).

The current frontend probes compare the official Pilot with legacy sysml-2ls
using linked states, transitions, source spans, inheritance and rejection cases.
The pinned 2024-12/2026-08 state grammar and dependency comparison is under
`research/version-diff/`. A current-syntax constant declaration is accepted by
the official frontend and rejected by the legacy frontend; core state syntax
alone is not enough to claim full cross-version compatibility.

The import corpus work connects source extraction to pyfcstm AST construction,
model validation and structured diagnostics. Unsupported constructs are reported
with source identity and counted separately. This repository does not implement
reverse conversion or claim unrestricted SysML execution equivalence.

```bash
python -m pip install -r requirements.txt
```

Original experiment code is MIT licensed. Third-party tools and corpora retain
their own licences; model sources are obtained from pinned upstream checkouts.

## Reproduce the importer

[Parser choice, public datasets, actual coverage and limitations (中文)](research/import-findings.zh.md)

[Failure attribution and corrected state-file inventory (中文)](research/frontend-audit.zh.md)

```bash
python -m pip install -r requirements.txt
python prepare_corpus.py
# Java 21; use the released v0.1.0 JAR and its matching 2026-07 standard library.
java -Xmx4g -cp /path/to/sysml-v2-pilot-gt-0.1.0-all.jar ExtractStates.java \
  /path/to/sysml.library artifacts/corpus-manifest.json artifacts/corpus-source.json
python check_import.py artifacts/corpus-source.json
python convert_corpus.py artifacts/corpus-source.json artifacts/converted
```

For the fully scripted download/checksum/library setup, run the
[GitHub workflow](.github/workflows/import.yml):

```bash
gh workflow run import.yml --repo HansBug/sysmlv2-experiment
gh run download RUN_ID --repo HansBug/sysmlv2-experiment --dir evidence
```

The workflow uploads source manifests, linked facts, per-file failures, accepted
FCSTM models, mappings and semantic reports. It parses corpus files independently
with the standard library; missing project context is a recorded limitation.
The mandatory check verifies target diagnostics, a two-cycle guard/assignment
trace, and explicit rejection of arrays, parallel states and nonempty do actions.

[Successful full-corpus Actions run](https://github.com/HansBug/sysmlv2-experiment/actions/runs/34703608767), agreeing with local execution: **1,332 files, 24 extracted state roots, 4 accepted
roots (2 external + 2 synthetic)**. There are 20 unsupported roots, 624 parsed
files without state machines and 691 files rejected by source validation in the
current context. These are different counting units. The corpus does not support
a claim that most public SysML models currently convert.

A separate official syntax-AST inventory found **25 syntax-valid external files
with state elements, 928 syntax-valid external files without them, and 369 files
with syntax errors**. Only 11 of the 25 state-containing files passed the baseline
full validation; the remaining 14 require further context/version/constraint
diagnosis. The audit reproduces missing project context, dropped cross-file
inheritance in our exporter, and a missing modern start-edge mapping in our
converter. No official core parser defect has been established by these probes.
