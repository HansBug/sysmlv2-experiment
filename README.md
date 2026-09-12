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
