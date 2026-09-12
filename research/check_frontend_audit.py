"""Reproduce converter rejection after the official frontend has accepted each probe."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from convert_corpus import lower, Unsupported


def check(result):
    try:
        if len(result['cross_file']['exported']['states']) != 2:
            raise AssertionError('Cross-file state export omitted linked members')
        result['cross_file']['conversion'] = {'status': 'exported_two_linked_states'}
    except (KeyError, TypeError) as error:
        # KeyError/TypeError: malformed audit JSON cannot prove cross-file export.
        raise AssertionError('Malformed cross-file audit') from error
    name, expected = 'modern_start', 'transition_source'
    try:
        from pyfcstm.dsl import parse_with_grammar_entry
        from pyfcstm.model import parse_dsl_node_to_state_machine
        from pyfcstm.diagnostics import inspect_model
        dsl, _ = lower(result[name]['exported'])
        report = inspect_model(parse_dsl_node_to_state_machine(parse_with_grammar_entry(dsl, 'state_machine_dsl')), enable_verify=True).to_json()
        errors = [item for item in report['diagnostics'] if item['severity'] == 'error']
        if errors:
            raise AssertionError(errors)
        result[name]['conversion'] = {'status': 'converted', 'diagnostics': report['diagnostics']}
    except Unsupported as error:
        # Unsupported: lower() still rejects the measured modern start boundary.
        assert error.code == expected, error.code
        result[name]['conversion'] = {'status': 'unsupported', 'code': error.code, 'detail': str(error)}
    except (KeyError, TypeError, ValueError) as error:
        # KeyError/TypeError/ValueError: malformed source facts or target DSL/model.
        raise AssertionError('Modern-start audit did not build a valid target model') from error
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = check(json.loads(args.source.read_text(encoding='utf-8')))
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS: linked cross-file states exported and modern start converted through pyfcstm')
