"""Convert validated project-context state roots through the pyfcstm target checks."""
import argparse
import json
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from convert_corpus import lower, Unsupported
from pyfcstm.dsl import parse_with_grammar_entry
from pyfcstm.model import parse_dsl_node_to_state_machine
from pyfcstm.diagnostics import inspect_model


def convert(input_dir, output):
    rows = []
    paths = [input_dir] if input_dir.is_file() else sorted(input_dir.glob('*.json'))
    for path in paths:
        if path.name == 'summary.json':
            continue
        project = json.loads(path.read_text(encoding='utf-8'))
        for file in project['files']:
            for state in file.get('states', []):
                row = {'project': project['project'], 'source': file['source'], 'state': state['id']}
                try:
                    dsl, mapping = lower(state)
                    model = parse_dsl_node_to_state_machine(parse_with_grammar_entry(dsl, 'state_machine_dsl'))
                    report = inspect_model(model, enable_verify=True).to_json()
                    errors = [item for item in report['diagnostics'] if item['severity'] == 'error']
                    row.update(status='converted' if not errors else 'target_semantic_error',
                               diagnostics=report['diagnostics'], mapping_count=len(mapping))
                except Unsupported as error:
                    # Unsupported: the validated source uses a construct outside the target profile.
                    row.update(status='unsupported', code=error.code, detail=str(error))
                rows.append(row)
    result = {'summary': {'state_roots': len(rows), 'results': dict(Counter(row['status'] for row in rows))}, 'records': rows}
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['summary'], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    convert(args.input, args.output)
