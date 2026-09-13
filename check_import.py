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
for filename in ('types.sysml', 'assignment.sysml', 'terminal-events.sysml', 'quantity-events.sysml', 'perform-sequence.sysml', 'send-action.sysml', 'structural-context.sysml', 'constraint-ignored.sysml', 'feature-chain-scalar.sysml'):
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
    if filename == 'structural-context.sysml':
        assert any(item['element']['kind'] == 'PartUsage' for item in root['ignored_structural'])
    if filename == 'constraint-ignored.sysml':
        assert any(item['element']['kind'].endswith('ConstraintUsage')
                   and item['reason'] == 'verification_constraint_outside_control_profile'
                   for item in root['ignored_structural'])
        assert any(item['element']['kind'] == 'ActionUsage'
                   and item['reason'] == 'action_declaration_outside_control_profile'
                   for item in root['ignored_structural'])
    if filename == 'feature-chain-scalar.sysml':
        assert any(item.get('structural_base') == 'FeatureChainScalarProbe::Controller::counter'
                   and item.get('structural_target') == 'FeatureChainScalarProbe::Counter::count'
                   for item in root['data'])
        assert 'v0 = 1' in dsl and '(v0 > 0)' in dsl
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

family = next(item for item in source['models']
              if item['dataset'] == 'gfse' and item['source'] == 'example_family/family.sysml')
assert family['status'] == 'extracted', family
try:
    lower(next(item for item in family['states'] if item['states']))
except Unsupported as error:
    # Base::Anything is the official typed fallback for the source time trigger;
    # it must not be turned into an FCSTM event with different semantics.
    assert error.code == 'time_trigger', error.code
else:
    raise AssertionError('Temporal trigger silently accepted as an event')

feature_chain = next(item for item in source['models']
                     if item['dataset'] == 'official_pilot'
                     and item['source'] == 'validation/05-State-based Behavior/5-State-based Behavior-1a.sysml')
assert feature_chain['status'] == 'extracted', feature_chain
try:
    def find_feature_chain_state(state):
        if any(guard.get('kind') == 'FeatureChainExpression'
               for entry in state['transitions'] for guard in entry.get('guards', [])):
            return state
        for child in state['states']:
            found = find_feature_chain_state(child)
            if found is not None:
                return found
        return None

    root = None
    for item in feature_chain['states']:
        root = find_feature_chain_state(item)
        if root is not None:
            break
    assert root is not None, feature_chain
    lower(root)
except Unsupported as error:
    # The typed chain keeps its target feature in the export; flattening an
    # external structural path into a scalar FCSTM variable would be unsound.
    assert error.code == 'feature_chain', error.code
else:
    raise AssertionError('Feature chain silently flattened into FCSTM data')

print('PASS: official source elements -> FCSTM AST -> model -> diagnostics -> two-cycle assignment trace; rejection checks')
