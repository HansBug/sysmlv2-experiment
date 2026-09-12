"""Compare pinned official state grammar and its library dependencies."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

REPOSITORY = 'Systems-Modeling/SysML-v2-Pilot-Implementation'
REVISIONS = {'2024-12': '92e531783b7a640f5546960092f5acdbaaf1ad32',
             '2026-08': '692170b71867353b8f90341e61556f49a5beb0e5'}
FILES = {
    'grammar': 'org.omg.sysml.xtext/src/org/omg/sysml/xtext/SysML.xtext',
    'states': 'sysml.library/Systems Library/States.sysml',
    'state-performances': 'sysml.library/Kernel Libraries/Kernel Semantic Library/StatePerformances.kerml',
    'transition-performances': 'sysml.library/Kernel Libraries/Kernel Semantic Library/TransitionPerformances.kerml',
    'actions': 'sysml.library/Systems Library/Actions.sysml',
}


def state_grammar(text):
    start = text.index('StateDefinition returns')
    end = text.index('CalculationDefinition returns', start)
    return text[start:end]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--cache', type=Path, default=Path('_external/versions'))
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    observations = []
    for name, relative in FILES.items():
        texts = []
        sources = []
        for tag, revision in REVISIONS.items():
            url = f'https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{quote(relative)}'
            cached = args.cache / f'{revision}-{name}.txt'
            if not cached.exists():
                with urlopen(url, timeout=60) as response:
                    cached.write_bytes(response.read())
            raw = cached.read_bytes()
            texts.append(raw.decode('utf-8'))
            sources.append({'tag': tag, 'revision': revision, 'url': url,
                            'sha256': hashlib.sha256(raw).hexdigest()})
        difference = ''.join(difflib.unified_diff(texts[0].splitlines(True), texts[1].splitlines(True),
                                                 fromfile=f'2024-12/{relative}', tofile=f'2026-08/{relative}'))
        (args.output / f'{name}.diff').write_text(difference, encoding='utf-8')
        row = {'file': relative, 'sources': sources, 'equal': texts[0] == texts[1]}
        if name == 'grammar':
            old, new = map(state_grammar, texts)
            row.update(state_section_equal=old == new, state_section_bytes=len(old.encode()),
                       state_section_sha256=[hashlib.sha256(s.encode()).hexdigest() for s in (old, new)])
            # This gate covers this pinned comparison, not future language versions or all state semantics.
            assert old == new, 'Pinned core state grammar comparison changed'
        observations.append(row)
    (args.output / 'observed.json').write_text(json.dumps(observations, indent=2) + '\n', encoding='utf-8')
    print('PASS: pinned core state grammar is identical; dependency diffs are retained separately')
