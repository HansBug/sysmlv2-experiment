# Official SysML v2 linking probe

This local, executable probe reuses the official Pilot workspace API already
bundled by [sysml-v2-pilot-gt](https://github.com/HansBug/sysml-v2-pilot-gt).
It does not change that repository or implement an importer.

Observed on OpenJDK 21, wrapper commit
`f4ae9fe96de5c27bb6d2088e245762562b7006f8`, official Pilot
`801c6a881954987a9707d396d5767db1ec51d8cb` (2026-07).
The checked-in `observed.txt` is the actual successful local output.

```bash
java -Xmx3g -cp /path/to/sysml-v2-pilot-gt-0.1.0-SNAPSHOT-all.jar \
  research/sysml/LinkedStateProbe.java \
  '/path/to/SysML-v2-Pilot-Implementation/sysml.library'
```

The probe loads the matching standard library and validates two separate model
resources. It asserts transition source/target links and cross-resource state
typing, reads the Boolean guard and inherited memberships, checks a source span,
and requires a semantic error for an unresolved state type.

This proves a reusable source frontend path. It does not prove execution,
cycle semantics, complete inherited-feature/redefinition support, or equivalence
to FCSTM. The existing wrapper CLI's general `semantic-json` serializer is not
used: its current output is a parse-object dump, not this linked workspace
contract; a CLI probe of the same state definition failed with
`ConcurrentModificationException` in this environment.
