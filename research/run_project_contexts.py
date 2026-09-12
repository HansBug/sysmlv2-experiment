"""Run the official project loader for every registered state-asset context."""
import argparse
import json
from pathlib import Path
import subprocess


def run(args):
    assets = json.loads(args.assets.read_text(encoding='utf-8'))['assets']
    roots = {name: path for name, path in (item.split('=', 1) for item in args.root)}
    contexts = {}
    for asset in assets:
        root = roots.get(asset['dataset'])
        if root is None:
            continue
        context = (Path(root) / asset['context_directory']).resolve()
        contexts[(asset['dataset'], str(context))] = context
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for (dataset, context), path in sorted(contexts.items()):
        result_path = output / (dataset + '-' + str(len(rows)) + '.json')
        command = ['java', '-Xmx3g', '-cp', str(args.jar) + ':' + str(args.classes), 'ExtractProject', str(args.library), str(path), str(result_path)]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, OSError) as error:
            # CalledProcessError: official loader rejected a project; OSError: Java/paths unavailable.
            rows.append({'dataset': dataset, 'context': str(path), 'status': 'runner_error', 'detail': str(error)})
            continue
        payload = json.loads(result_path.read_text(encoding='utf-8'))
        files = payload['files']
        rows.append({'dataset': dataset, 'context': str(path), 'status': 'completed',
                     'files': len(files), 'error_count': sum(item['errors'] for item in files),
                     'state_roots': sum(len(item['states']) for item in files)})
    (output / 'summary.json').write_text(json.dumps({'contexts': rows}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'contexts': len(rows), 'completed': sum(item['status'] == 'completed' for item in rows),
                      'state_roots': sum(item.get('state_roots', 0) for item in rows)}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, default=Path('research/state-assets.json'))
    parser.add_argument('--root', action='append', required=True, help='dataset=directory containing asset paths')
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--jar', type=Path, required=True)
    parser.add_argument('--classes', type=Path, default=Path('artifacts/audit-classes'))
    parser.add_argument('--output', type=Path, default=Path('artifacts/project-contexts'))
    run(parser.parse_args())
