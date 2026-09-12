"""Check actual official source facts, target diagnostics and a two-cycle trace."""
import json
from pathlib import Path
import sys
from convert_corpus import lower, Unsupported
from pyfcstm.dsl import parse_with_grammar_entry
from pyfcstm.model import parse_dsl_node_to_state_machine
from pyfcstm.diagnostics import inspect_model
from pyfcstm.simulate import SimulationRuntime

source = json.loads(Path(sys.argv[1]).read_text())
cases = {m['source']: m for m in source['models'] if m['dataset'] == 'synthetic'}
for filename in ('types.sysml', 'assignment.sysml', 'terminal-events.sysml', 'quantity-events.sysml', 'perform-sequence.sysml', 'send-action.sysml'):
    assert cases[filename]['status'] == 'extracted', cases[filename]
    roots = cases[filename]['states']
    root = next((item for item in roots if item['states']), roots[0])
    dsl, mapping = lower(root)
    ast = parse_with_grammar_entry(dsl, 'state_machine_dsl')
    model = parse_dsl_node_to_state_machine(ast)
    report = inspect_model(model, enable_verify=True).to_json()
    assert not [d for d in report['diagnostics'] if d['severity'] == 'error']
    assert any(m['kind'] == 'transition' and m['span'] for m in mapping)
    if filename == 'assignment.sysml':
        runtime = SimulationRuntime(model)
        runtime.cycle()
        assert runtime.current_state.path == ('S0', 'S1') and runtime.vars['v0'] == 1
        runtime.cycle()
        assert runtime.current_state.path == ('S0', 'S2') and runtime.vars['v0'] == 4
    if filename == 'terminal-events.sysml':
        assert '-> [*]' in dsl
    if filename == 'quantity-events.sysml':
        assert 'def float ' in dsl and ' >= 10' in dsl
    if filename == 'perform-sequence.sysml':
        assert 'during abstract workflow;' in dsl
        assert any(item.get('representation') == 'abstract_hook' and item.get('sequence_length') == 2 for item in mapping)
    if filename == 'send-action.sysml':
        assert 'enter abstract send_action_' in dsl
for filename, code in [('parallel.sysml', 'parallel'), ('actions.sysml', 'do_action_execution'),
                       ('array.sysml', 'data_multiplicity')]:
    assert cases[filename]['status'] == 'extracted', cases[filename]
    try:
        lower(cases[filename]['states'][0])
    except Unsupported as error:
        # Unsupported: these source fixtures deliberately exceed the documented subset.
        assert error.code == code, (filename, error.code)
    else:
        raise AssertionError('Unsupported source silently accepted: ' + filename)
for filename in ('invalid-type.sysml', 'invalid-target.sysml'):
    assert cases[filename]['status'] == 'source_validation_error', cases[filename]
print('PASS: official source elements -> FCSTM AST -> model -> diagnostics -> two-cycle assignment trace; rejection checks')
