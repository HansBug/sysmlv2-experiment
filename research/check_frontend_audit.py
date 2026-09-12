"""Reproduce converter rejection after the official frontend has accepted each probe."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from convert_corpus import lower, Unsupported


def check(result):
    for name, expected in [('cross_file', 'no_control_states'), ('modern_start', 'transition_source')]:
        try:
            lower(result[name]['exported'])
        except Unsupported as error:
            # Unsupported: lower() rejects linked source facts at the currently measured integration gaps.
            assert error.code == expected, (name, error.code)
            result[name]['conversion'] = {'status': 'unsupported', 'code': error.code, 'detail': str(error)}
        else:
            raise AssertionError('Revisit the measured converter limitation: ' + name)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = check(json.loads(args.source.read_text(encoding='utf-8')))
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS: linked cross-file states and modern start fail at the measured converter boundaries')
