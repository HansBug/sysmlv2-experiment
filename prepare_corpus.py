"""Fetch pinned public model repositories and write a source-hashed manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

REPOSITORIES = {
    'gfse': 'GfSE/SysML-v2-Models',
    'benchmark': 'yasminebouamra/SysMLv2-Benchmark',
    'refinement': 'cmuchancel/NL-to-SysMLv2-via-Conformance-Driven-Refinement',
    'apollo11': 'airbus/apollo-11-sysml-v2',
}


def prepare(output, fixtures_only=False):
    pins = json.loads(Path('research/corpus-pins.json').read_text())
    roots = {'synthetic': Path('research/cases')}
    official = Path('_external/pilot-src/sysml/src')
    if not fixtures_only:
        for name, repository in REPOSITORIES.items():
            pin = pins['systemp' if name == 'benchmark' else name]
            path = Path('_external') / name
            if not path.exists():
                subprocess.run(['git', 'clone', '--no-checkout', 'https://github.com/' + repository + '.git', str(path)], check=True)
                subprocess.run(['git', '-C', str(path), 'checkout', '--detach', pin], check=True)
            head = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
            if head != pin:
                raise ValueError(str(path) + ' is not at the pinned commit: ' + pin)
        roots.update({
            'gfse': Path('_external/gfse/models'),
            'systemp': Path('_external/benchmark/data'),
            'refinement_positive': Path('_external/refinement/Open-Source Dataset Release/604 positive artifacts'),
            'refinement_negative': Path('_external/refinement/Open-Source Dataset Release/439 negative artifacts'),
            'apollo11': Path('_external/apollo11'),
        })
        if official.exists():
            roots['official_pilot'] = official
    files = []
    for dataset, root in roots.items():
        paths = sorted(root.rglob('*.sysml'))
        if not paths:
            raise ValueError('No models found: ' + str(root))
        for path in paths:
            files.append({'dataset': dataset, 'source': path.relative_to(root).as_posix(),
                          'path': path.as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'pins': pins, 'files': files}, indent=2) + '\n')
    print('Manifest:', len(files), 'files')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures-only', action='store_true')
    parser.add_argument('--output', type=Path, default=Path('artifacts/corpus-manifest.json'))
    args = parser.parse_args()
    prepare(args.output, args.fixtures_only)
