"""Lower a linked SysML state subset and require pyfcstm AST/model semantic validation."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from pyfcstm.dsl import parse_with_grammar_entry
from pyfcstm.dsl.error import GrammarParseError
from pyfcstm.model import parse_dsl_node_to_state_machine
from pyfcstm.diagnostics import inspect_model
from pyfcstm.utils.validate import ModelValidationError


class Unsupported(ValueError):
    def __init__(self, code, detail):
        self.code = code
        super().__init__(detail)


def expression(expr, variables):
    kind = expr['kind']
    if kind in ('LiteralBoolean', 'LiteralInteger', 'LiteralRational'):
        return json.dumps(expr['value'])
    if kind == 'FeatureReferenceExpression':
        if expr['referent'] not in variables:
            raise Unsupported('external_variable', str(expr['referent']))
        return variables[expr['referent']]
    if kind == 'OperatorExpression':
        operator = {'=': '==', '<>': '!=', '&': 'and', '|': 'or'}.get(expr['operator'], expr['operator'])
        operands = [expression(e, variables) for e in expr['operands']]
        if operator in ('+', '-', 'not') and len(operands) == 1:
            return '(' + operator + ' ' + operands[0] + ')'
        if operator in ('+', '-', '*', '/', '<', '<=', '>', '>=', '==', '!=', 'and', 'or') and len(operands) == 2:
            return '(' + operands[0] + ' ' + operator + ' ' + operands[1] + ')'
        raise Unsupported('operator', expr['operator'])
    raise Unsupported('expression_kind', kind)


def lower(root):
    nodes = []
    def collect(state):
        declaration_only = {'ActionDefinition'}
        unsupported = [kind for kind in state['unsupported'] if kind not in declaration_only]
        if unsupported:
            raise Unsupported('member_kind', ','.join(unsupported))
        if state['parallel']:
            raise Unsupported('parallel', state['id'])
        nodes.append(state)
        for child in state['states']:
            collect(child)
    collect(root)
    if not root['states']:
        raise Unsupported('no_control_states', root['id'])
    variables, declarations, mapping, constants = {}, [], [], set()
    event_ids = []
    for node in nodes:
        for edge in node['transitions']:
            for event in edge.get('triggers', []):
                if event not in event_ids:
                    event_ids.append(event)
    events = {event: 'E' + str(index) for index, event in enumerate(event_ids)}
    for node in nodes:
        for data in node['data']:
            if data['id'] in variables:
                raise Unsupported('reused_data_context', data['id'])
            variables[data['id']] = 'v' + str(len(variables))
            if data['constant']:
                constants.add(data['id'])
    for node in nodes:
        for data in node['data']:
            if not data['scalar']:
                raise Unsupported('data_multiplicity', data['id'])
            types = set(data['types'])
            if not types or not types <= {'ScalarValues::Integer', 'ScalarValues::Real', 'ScalarValues::Boolean', 'ScalarValues::Natural'}:
                raise Unsupported('data_type', str(data['types']))
            if len(data['values']) != 1:
                raise Unsupported('data_initializer', data['id'])
            value = expression(data['values'][0], variables)
            if 'ScalarValues::Boolean' in types:
                value = {'true': '1', 'false': '0'}.get(value, value)
            target_type = 'float' if 'ScalarValues::Real' in types else 'int'
            declarations.append(f'def {target_type} {variables[data["id"]]} = {value};')
            mapping.append({'source_id': data['id'], 'span': data['span'], 'kind': 'variable', 'target': variables[data['id']]})
    def action(body):
        if body['kind'] == 'empty':
            return ''
        if body['kind'] != 'assign':
            raise Unsupported('action_kind', body['kind'])
        if body['target'] not in variables or body['target'] in constants:
            raise Unsupported('assignment_target', str(body['target']))
        return variables[body['target']] + ' = ' + expression(body['value'], variables) + ';'
    names = {node['id']: 'S' + str(index) for index, node in enumerate(nodes)}
    def emit(node, prefix, indent):
        target = prefix + names[node['id']]
        mapping.append({'kind': 'state', 'source_id': node['id'], 'span': node['span'], 'target': target})
        lines = [indent + 'state ' + names[node['id']] + ' {']
        if prefix == '':
            lines.extend(indent + '    event ' + events[event] + ';' for event in event_ids)
        entry_ids = {a['id'] for a in node['actions'] if a['role'] == 'entry'}
        for subaction in node['actions']:
            body = action(subaction['action'])
            if body:
                role = {'entry': 'enter', 'do': 'during', 'exit': 'exit'}[subaction['role']]
                if role == 'during':
                    raise Unsupported('do_action_execution', node['id'])
                lines.append(indent + '    ' + role + ' { ' + body + ' }')
                mapping.append({'kind': 'state_action', 'source_id': subaction['id'],
                                'span': subaction['action']['span'], 'target_owner': target, 'target_role': role})
        child_ids = {c['id'] for c in node['states']}
        for child in node['states']:
            lines.extend(emit(child, target + '.', indent + '    '))
        initial = 0
        outgoing = Counter()
        outgoing_events = {}
        for index, edge in enumerate(node['transitions']):
            triggers = edge.get('triggers', [])
            if edge['trigger_count'] and not triggers:
                raise Unsupported('trigger_event', edge['id'])
            target_element = edge.get('target_element') or {}
            terminal_target = (target_element.get('kind') == 'StateUsage'
                               and target_element.get('declared_name') == 'done'
                               and target_element.get('library') is True)
            if edge['target'] not in child_ids and not terminal_target:
                raise Unsupported('transition_target', str(edge['target']))
            if edge['source'] in entry_ids or edge['source'] == 'States::StateAction::start':
                src = '[*]'
                initial += 1
            elif edge['source'] in child_ids:
                src = names[edge['source']]
                outgoing[src] += 1
                # Distinct single typed events are mutually exclusive. Repeated
                # events, guards, and compound triggers still need an explicit
                # priority model and remain outside this profile.
                signature = tuple(triggers)
                previous = outgoing_events.setdefault(src, set())
                if outgoing[src] > 1 and (edge['guards'] or len(signature) != 1 or signature in previous):
                    raise Unsupported('transition_priority_unspecified', edge['source'])
                previous.add(signature)
            else:
                raise Unsupported('transition_source', str(edge['source']))
            terms = [events[event] for event in triggers]
            if edge['guards']:
                terms.append('[' + ' and '.join(expression(g, variables) for g in edge['guards']) + ']')
            trigger = '' if not terms else ' : ' + ' + '.join(terms)
            effects = ' '.join(action(a) for a in edge['effects'])
            effect = ' effect { ' + effects + ' }' if effects else ''
            destination = '[*]' if terminal_target else names[edge['target']]
            lines.append(indent + f'    {src} -> {destination}{trigger}{effect};')
            mapping.append({'kind': 'transition', 'source_id': edge['id'], 'span': edge['span'],
                            'target_owner': target, 'target_declaration_index': index})
        if child_ids and initial != 1:
            raise Unsupported('initial_transition_count', node['id'])
        lines.append(indent + '}')
        return lines
    return '\n'.join(declarations + emit(root, '', '')) + '\n', mapping


def run(source, output):
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for file in source['models']:
        identity = {k: file[k] for k in ('dataset', 'source', 'sha256', 'context')}
        if file['status'] != 'extracted':
            rows.append({**identity, 'status': file['status'], 'detail': file['detail']})
            continue
        if not file['states']:
            rows.append({**identity, 'status': 'no_state_machine'})
        for state in file['states']:
            row = {**identity, 'state': state['id'], 'has_control_states': bool(state['states'])}
            key = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()[:16]
            try:
                dsl, mapping = lower(state)
                folder = output / key
                folder.mkdir(exist_ok=True)
                (folder / 'model.fcstm').write_text(dsl)
                ast = parse_with_grammar_entry(dsl, 'state_machine_dsl')
                model = parse_dsl_node_to_state_machine(ast)
                report = inspect_model(model, enable_verify=True).to_json()
                errors = [d for d in report['diagnostics'] if d['severity'] == 'error']
                row.update(status='semantic_error' if errors else 'converted', diagnostics=report['diagnostics'],
                           artifact=key, ast_type=type(ast).__name__, model_type=type(model).__name__)
                (folder / 'inspect.json').write_text(json.dumps(report, indent=2) + '\n')
                (folder / 'mapping.json').write_text(json.dumps({'source': identity, 'root': state['id'], 'elements': mapping,
                    'assumptions': ['Explicit periodic controller interpretation; no general SysML execution equivalence claim.',
                                    'Single active path, mathematical numeric domain, no asynchronous messages.']}, indent=2) + '\n')
            except Unsupported as error:
                # Unsupported: lower() reports source features outside the implemented periodic subset.
                row.update(status='unsupported', code=error.code, detail=str(error))
            except (GrammarParseError, ModelValidationError) as error:
                # GrammarParseError: generated grammar failure; ModelValidationError: target semantic rejection.
                row.update(status='target_error', code=type(error).__name__, detail=str(error))
            rows.append(row)
    extracted_roots = [r for r in rows if 'state' in r]
    control_candidates = [r for r in extracted_roots if r['has_control_states']]
    summary = {'source_files': len(source['models']),
               'unique_source_hashes': len({m['sha256'] for m in source['models']}),
               'extracted_state_roots': len(extracted_roots),
               'control_candidates': len(control_candidates),
               'files_with_converted_root': len({(r['dataset'], r['source']) for r in rows if r['status'] == 'converted'}),
               'results': dict(Counter(r['status'] for r in rows)),
               'converted_control_candidates': sum(r['status'] == 'converted' for r in control_candidates),
               'unsupported_first_reason': dict(Counter(r['code'] for r in rows if r['status'] == 'unsupported')),
               'by_dataset': {name: dict(Counter(r['status'] for r in rows if r['dataset'] == name)) for name in sorted({r['dataset'] for r in rows})}}
    (output / 'results.json').write_text(json.dumps({'summary': summary, 'records': rows}, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    run(json.loads(args.source.read_text()), args.output)
