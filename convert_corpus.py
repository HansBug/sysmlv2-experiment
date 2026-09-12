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


def target_identifier(value):
    """Accept only names already valid in the FCSTM identifier domain."""
    if not isinstance(value, str) or not value:
        return None
    if not (value[0].isalpha() or value[0] == '_'):
        return None
    return value if all(char.isalnum() or char == '_' for char in value) else None


def action_identifier(body):
    """Create a stable FCSTM hook name from a typed action declaration."""
    for value in (body.get('declared_name'), (body.get('performed') or {}).get('declared_name')):
        if target_identifier(value):
            return value
        if isinstance(value, str) and value:
            pieces = []
            for char in value:
                pieces.append(char if char.isalnum() else '_')
            candidate = ''.join(pieces).strip('_')
            if candidate and (candidate[0].isalpha() or candidate[0] == '_'):
                return candidate
    offset = (body.get('span') or {}).get('offset')
    if isinstance(offset, int):
        prefix = 'send_action_' if body.get('kind') == 'SendActionUsage' else 'action_'
        return prefix + str(offset)
    return None


def expression(expr, variables):
    kind = expr['kind']
    if kind in ('LiteralBoolean', 'LiteralInteger', 'LiteralRational'):
        return json.dumps(expr['value'])
    if kind == 'FeatureReferenceExpression':
        if expr['referent'] not in variables:
            raise Unsupported('external_variable', str(expr['referent']))
        return variables[expr['referent']]
    if kind == 'OperatorExpression':
        if expr['operator'] == '[':
            operands = expr.get('operands', [])
            unit = expr.get('unit')
            if len(operands) != 2 or unit is None or not unit_expression(unit):
                raise Unsupported('quantity_unit', str(expr.get('span')))
            # FCSTM has no quantity type in this profile. The linked unit is
            # checked structurally, then the magnitude is kept as a real value.
            return expression(operands[0], variables)
        operator = {'=': '==', '<>': '!=', '&': 'and', '|': 'or'}.get(expr['operator'], expr['operator'])
        operands = [expression(e, variables) for e in expr['operands']]
        if operator in ('+', '-', 'not') and len(operands) == 1:
            return '(' + operator + ' ' + operands[0] + ')'
        if operator in ('+', '-', '*', '/', '<', '<=', '>', '>=', '==', '!=', 'and', 'or') and len(operands) == 2:
            return '(' + operands[0] + ' ' + operator + ' ' + operands[1] + ')'
        raise Unsupported('operator', expr['operator'])
    raise Unsupported('expression_kind', kind)


def unit_expression(expr):
    """Return whether a typed expression contains only library unit elements."""
    kind = expr.get('kind')
    if kind == 'FeatureReferenceExpression':
        element = expr.get('referent_element') or {}
        return element.get('library') is True
    if kind == 'OperatorExpression':
        return all(unit_expression(operand) for operand in expr.get('operands', []))
    return False


def numeric_literal(expr):
    """Return a numeric literal from a typed scalar or quantity expression."""
    if expr['kind'] in ('LiteralInteger', 'LiteralRational'):
        return float(expr['value'])
    if expr['kind'] == 'OperatorExpression' and expr.get('operator') == '[':
        operands = expr.get('operands', [])
        if len(operands) == 2 and unit_expression(expr.get('unit', {})):
            return numeric_literal(operands[0])
    return None


def simple_guard(guard):
    """Extract a scalar comparison whose left side is one typed variable."""
    if guard.get('kind') != 'OperatorExpression' or guard.get('operator') not in {'<', '<=', '>', '>='}:
        return None
    operands = guard.get('operands', [])
    if len(operands) != 2 or operands[0].get('kind') != 'FeatureReferenceExpression':
        return None
    value = numeric_literal(operands[1])
    if value is None:
        return None
    return operands[0].get('referent'), guard['operator'], value


def guards_disjoint(left, right):
    """Prove disjointness for two one-variable interval comparisons."""
    a, b = simple_guard(left), simple_guard(right)
    if a is None or b is None or a[0] != b[0]:
        return False
    _, op_a, value_a = a
    _, op_b, value_b = b
    if op_a in {'<', '<='} and op_b in {'>', '>='}:
        return value_a <= value_b if op_a == '<' or op_b == '>' else value_a < value_b
    if op_b in {'<', '<='} and op_a in {'>', '>='}:
        return value_b <= value_a if op_b == '<' or op_a == '>' else value_b < value_a
    return False


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
            scalar_types = {'ScalarValues::Integer', 'ScalarValues::Real', 'ScalarValues::Boolean', 'ScalarValues::Natural'}
            quantity_type = (all(item.get('kind') == 'AttributeDefinition' and item.get('library') is True
                                 for item in data.get('type_elements', []))
                             and bool(data.get('type_elements'))
                             and all(value.get('kind') == 'OperatorExpression' and value.get('operator') == '['
                                     for value in data.get('values', [])))
            if not types or (not types <= scalar_types and not quantity_type):
                raise Unsupported('data_type', str(data['types']))
            if len(data['values']) != 1:
                raise Unsupported('data_initializer', data['id'])
            value = expression(data['values'][0], variables)
            if 'ScalarValues::Boolean' in types:
                value = {'true': '1', 'false': '0'}.get(value, value)
            target_type = 'float' if quantity_type or 'ScalarValues::Real' in types else 'int'
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
    def abstract_action(body, role):
        """Keep a typed action invocation as a pyfcstm abstract hook."""
        if body.get('kind') not in {'ActionUsage', 'PerformActionUsage', 'SendActionUsage'}:
            raise Unsupported('action_kind', body.get('kind'))
        name = action_identifier(body)
        if not name:
            raise Unsupported('action_name', str(body.get('id')))
        # Keep a non-linear or incomplete typed succession as one opaque hook.
        # The structured sequence diagnostic remains in mapping metadata; no
        # source action is deleted, while FCSTM deliberately makes no claim
        # about the inner execution order.
        # The source action remains discoverable through the mapping and can be
        # implemented by the generated model's abstract hook.
        return f'{role} abstract {name};', name
    names = {node['id']: 'S' + str(index) for index, node in enumerate(nodes)}
    def emit(node, prefix, indent):
        target = prefix + names[node['id']]
        mapping.append({'kind': 'state', 'source_id': node['id'], 'span': node['span'], 'target': target})
        lines = [indent + 'state ' + names[node['id']] + ' {']
        if prefix == '':
            lines.extend(indent + '    event ' + events[event] + ';' for event in event_ids)
        entry_ids = {a['id'] for a in node['actions'] if a['role'] == 'entry'}
        pseudo_initial_ids = {child['id'] for child in node['states']
                              if child.get('declared_name') == 'initial'
                              and not child['states'] and not child['transitions']}
        for subaction in node['actions']:
            role = {'entry': 'enter', 'do': 'during', 'exit': 'exit'}[subaction['role']]
            body = subaction['action']
            if body.get('kind') in {'ActionUsage', 'PerformActionUsage', 'SendActionUsage'}:
                abstract_line, target_action = abstract_action(body, role)
                lines.append(indent + '    ' + abstract_line)
                mapping.append({'kind': 'state_action', 'source_id': subaction['id'],
                                'span': body['span'], 'target_owner': target, 'target_role': role,
                                'representation': 'abstract_hook',
                                'target_action': target_action,
                                'argument_references': body.get('argument_references', []),
                                'sequence_length': len(body.get('sequence', [])) if isinstance(body.get('sequence'), list) else None})
                continue
            body_text = action(body)
            if body_text:
                if role == 'during':
                    raise Unsupported('do_action_execution', node['id'])
                lines.append(indent + '    ' + role + ' { ' + body_text + ' }')
                mapping.append({'kind': 'state_action', 'source_id': subaction['id'],
                                'span': body['span'], 'target_owner': target, 'target_role': role})
        child_ids = {c['id'] for c in node['states']}
        for child in node['states']:
            if child['id'] in pseudo_initial_ids:
                mapping.append({'kind': 'pseudo_state', 'source_id': child['id'],
                                'span': child['span'], 'target': '[*]', 'reason': 'typed_initial_usage'})
                continue
            lines.extend(emit(child, target + '.', indent + '    '))
        initial = 0
        outgoing = Counter()
        outgoing_events = {}
        for index, edge in enumerate(node['transitions']):
            triggers = edge.get('triggers', [])
            if edge['trigger_count'] and not triggers:
                raise Unsupported('trigger_event', edge['id'])
            # The official Pilot resolves time/change accepts to the generic
            # Base::Anything classifier. FCSTM events require a concrete typed
            # signal; treating this classifier as an event would change the
            # source trigger semantics.
            if any(item.get('kind') == 'Classifier' for item in edge.get('trigger_elements', [])):
                raise Unsupported('time_trigger', edge['id'])
            target_element = edge.get('target_element') or {}
            terminal_target = (target_element.get('kind') == 'StateUsage'
                               and target_element.get('declared_name') == 'done'
                               and target_element.get('library') is True)
            if edge['target'] not in child_ids and not terminal_target:
                raise Unsupported('transition_target', str(edge['target']))
            if edge['source'] in pseudo_initial_ids:
                src = '[*]'
                initial += 1
            elif edge['source'] in entry_ids or edge['source'] == 'States::StateAction::start':
                src = '[*]'
                initial += 1
            elif edge['source'] in child_ids:
                src = names[edge['source']]
                outgoing[src] += 1
                # Distinct single typed events are mutually exclusive. Repeated
                # events, guards, and compound triggers still need an explicit
                # priority model and remain outside this profile unless two
                # simple typed interval guards are provably disjoint.
                signature = tuple(triggers)
                previous = outgoing_events.setdefault(src, [])
                conflict = any(old_signature == signature and not (
                    len(edge['guards']) == len(old_guards) == 1
                    and guards_disjoint(edge['guards'][0], old_guards[0]))
                    for old_signature, old_guards in previous)
                if outgoing[src] > 1 and (len(signature) != 1 or conflict):
                    raise Unsupported('transition_priority_unspecified', edge['source'])
                previous.append((signature, edge['guards']))
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
        effective_child_ids = child_ids - pseudo_initial_ids
        if effective_child_ids and initial != 1:
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
                    'ignored_structural': state.get('ignored_structural', []),
                    'assumptions': ['Explicit periodic controller interpretation; no general SysML execution equivalence claim.',
                                    'Single active path, mathematical numeric domain, no asynchronous messages.',
                                    'Abstract action arguments remain typed mapping metadata; hook execution is not synthesized.',
                                    'Non-linear or incomplete typed action succession is kept as one opaque hook; inner order is not synthesized.',
                                    'Typed quantity literals keep their magnitude; linked library units are erased for the FCSTM numeric domain.']}, indent=2) + '\n')
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
