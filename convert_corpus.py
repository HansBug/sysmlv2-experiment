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


def expression(expr, variables, structural_variables=None, external_variables=None,
               declarations=None, external_mappings=None):
    structural_variables = {} if structural_variables is None else structural_variables
    external_variables = {} if external_variables is None else external_variables
    kind = expr['kind']
    if kind in ('LiteralBoolean', 'LiteralInteger', 'LiteralRational'):
        return json.dumps(expr['value'])
    if kind == 'FeatureReferenceExpression':
        if expr['referent'] not in variables:
            raise Unsupported('external_variable', str(expr['referent']))
        return variables[expr['referent']]
    if kind == 'FeatureChainExpression':
        operands = expr.get('operands', [])
        target = expr.get('target_feature') or {}
        if len(operands) == 1 and operands[0].get('kind') == 'FeatureReferenceExpression':
            key = (operands[0].get('referent'), target.get('id'))
            if key in structural_variables:
                return structural_variables[key]
            if key in external_variables:
                return external_variables[key]
            scalar_types = {'ScalarValues::Integer', 'ScalarValues::Real',
                            'ScalarValues::Boolean', 'ScalarValues::Natural'}
            target_types = set(target.get('types', []))
            if target.get('kind') in {'AttributeUsage', 'ReferenceUsage'} and target.get('scalar') and target_types & scalar_types:
                name = 'v' + str(len(variables) + len(external_variables))
                external_variables[key] = name
                target_type = 'float' if 'ScalarValues::Real' in target_types else 'int'
                default = '0.0' if target_type == 'float' else '0'
                if declarations is not None:
                    declarations.append(f'def {target_type} {name} = {default};')
                if external_mappings is not None:
                    external_mappings.append({'kind': 'external_feature',
                                              'source_id': target.get('id'),
                                              'source_span': target.get('span'),
                                              'referent': operands[0].get('referent'),
                                              'target': name,
                                              'representation': 'scalar_input_default',
                                              'default': default})
                # A bare identifier is not a FCSTM condition.  Boolean
                # feature chains therefore become an explicit numeric test.
                return '(' + name + ' == 1)' if 'ScalarValues::Boolean' in target_types else name
        raise Unsupported('feature_chain', str(expr.get('target_feature') or expr.get('span')))
    if kind == 'OperatorExpression':
        if expr['operator'] == '[':
            operands = expr.get('operands', [])
            unit = expr.get('unit')
            if len(operands) != 2 or unit is None or not unit_expression(unit):
                raise Unsupported('quantity_unit', str(expr.get('span')))
            # FCSTM has no quantity type in this profile. The linked unit is
            # checked structurally, then the magnitude is kept as a real value.
            return expression(operands[0], variables, structural_variables, external_variables,
                              declarations, external_mappings)
        operator = {'=': '==', '<>': '!=', '&': 'and', '|': 'or'}.get(expr['operator'], expr['operator'])
        operands = [expression(e, variables, structural_variables, external_variables,
                                declarations, external_mappings) for e in expr['operands']]
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


def lower(root):
    nodes = []
    parent_by_id = {}
    node_by_id = {}
    def collect(state):
        declaration_only = {'ActionDefinition'}
        unsupported = [kind for kind in state['unsupported'] if kind not in declaration_only]
        if unsupported:
            raise Unsupported('member_kind', ','.join(unsupported))
        if state['parallel']:
            raise Unsupported('parallel', state['id'])
        nodes.append(state)
        node_by_id[state['id']] = state
        for child in state['states']:
            parent_by_id[child['id']] = state['id']
            collect(child)
    collect(root)
    if not root['states']:
        raise Unsupported('no_control_states', root['id'])
    variables, declarations, mapping, constants = {}, [], [], set()
    structural_variables = {}
    external_variables = {}
    external_mappings = []
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
            if data.get('structural_base') and data.get('structural_target'):
                structural_variables[(data['structural_base'], data['structural_target'])] = variables[data['id']]
            if data['constant']:
                constants.add(data['id'])
                if data.get('structural_target'):
                    constants.add(data['structural_target'])
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
            value = expression(data['values'][0], variables, structural_variables,
                               external_variables, declarations, external_mappings)
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
        target = variables.get(body.get('target'))
        target_expression = body.get('target_expression') or {}
        if target is None and target_expression.get('kind') == 'FeatureReferenceExpression':
            target = structural_variables.get((target_expression.get('referent'), body.get('target')))
        if target is None or body.get('target') in constants:
            raise Unsupported('assignment_target', str(body.get('target')))
        return target + ' = ' + expression(body['value'], variables, structural_variables,
                                           external_variables, declarations, external_mappings) + ';'
    def abstract_action(body, role, used_names=None):
        """Keep a typed action invocation as a pyfcstm abstract hook."""
        if body.get('kind') not in {'ActionUsage', 'PerformActionUsage', 'SendActionUsage'}:
            raise Unsupported('action_kind', body.get('kind'))
        name = action_identifier(body)
        if not name:
            raise Unsupported('action_name', str(body.get('id')))
        if used_names is not None:
            base = name
            suffix = 2
            while name in used_names:
                name = base + '_' + str(suffix)
                suffix += 1
            used_names.add(name)
        # Keep a non-linear or incomplete typed succession as one opaque hook.
        # The structured sequence diagnostic remains in mapping metadata; no
        # source action is deleted, while FCSTM deliberately makes no claim
        # about the inner execution order.
        # The source action remains discoverable through the mapping and can be
        # implemented by the generated model's abstract hook.
        return f'{role} abstract {name};', name
    transition_hooks = {}
    for owner in nodes:
        for edge in owner['transitions']:
            for body in edge.get('effects', []):
                if body.get('kind') in {'ActionUsage', 'PerformActionUsage', 'SendActionUsage'}:
                    transition_hooks.setdefault(edge.get('source'), []).append((edge, body))
    names = {node['id']: 'S' + str(index) for index, node in enumerate(nodes)}

    def pseudo_ids_for(state):
        return {child['id'] for child in state['states']
                if child.get('declared_name') == 'initial'
                and not child['states'] and not child['transitions']}

    def deterministic_initial_child(state):
        """Return a unique typed child reached on state entry, when known."""
        pseudo_ids = pseudo_ids_for(state)
        effective = [child for child in state['states'] if child['id'] not in pseudo_ids]
        entry_ids = {a['id'] for a in state['actions'] if a['role'] == 'entry'}
        targets = []
        for edge in state['transitions']:
            if edge['source'] in pseudo_ids or edge['source'] in entry_ids or edge['source'] == 'States::StateAction::start':
                if edge['target'] in {child['id'] for child in effective}:
                    targets.append(edge['target'])
        unique_targets = list(dict.fromkeys(targets))
        if len(unique_targets) == 1:
            return unique_targets[0]
        if not unique_targets and len(effective) == 1:
            # This is the same profile default emitted below for a missing
            # explicit initial succession.
            return effective[0]['id']
        return None

    def direct_child_for(endpoint, owner):
        """Map a nested endpoint to its direct child only on a deterministic path."""
        direct_ids = {child['id'] for child in owner['states']}
        if endpoint in direct_ids:
            return endpoint, None
        if endpoint not in node_by_id:
            return None, None
        path = []
        current = endpoint
        while current != owner['id']:
            parent = parent_by_id.get(current)
            if parent is None:
                return None, None
            path.append(current)
            current = parent
        path.reverse()
        if not path:
            return None, None
        selected = path[0]
        cursor = node_by_id[selected]
        for expected in path[1:]:
            if deterministic_initial_child(cursor) != expected:
                return None, None
            cursor = node_by_id[expected]
        return selected, path

    def emit(node, prefix, indent):
        target = prefix + names[node['id']]
        mapping.append({'kind': 'state', 'source_id': node['id'], 'span': node['span'], 'target': target})
        lines = [indent + 'state ' + names[node['id']] + ' {']
        if prefix == '':
            lines.extend(indent + '    event ' + events[event] + ';' for event in event_ids)
        entry_ids = {a['id'] for a in node['actions'] if a['role'] == 'entry'}
        used_action_names = set()
        pseudo_initial_ids = pseudo_ids_for(node)
        for subaction in node['actions']:
            role = {'entry': 'enter', 'do': 'during', 'exit': 'exit'}[subaction['role']]
            # pyfcstm does not permit a ``during`` operation on a composite
            # state.  Keep a typed do-action as a single entry hook in that
            # case; the mapping records the profile role below.
            emitted_role = 'enter' if role == 'during' and node['states'] else role
            body = subaction['action']
            if body.get('kind') in {'ActionUsage', 'PerformActionUsage', 'SendActionUsage'}:
                abstract_line, target_action = abstract_action(body, emitted_role, used_action_names)
                lines.append(indent + '    ' + abstract_line)
                mapping.append({'kind': 'state_action', 'source_id': subaction['id'],
                                'span': body['span'], 'target_owner': target, 'target_role': emitted_role,
                                'source_role': role,
                                'representation': 'abstract_hook',
                                'target_action': target_action,
                                'argument_references': body.get('argument_references', []),
                                'sequence_length': len(body.get('sequence', [])) if isinstance(body.get('sequence'), list) else None})
                continue
            body_text = action(body)
            if body_text:
                lines.append(indent + '    ' + emitted_role + ' { ' + body_text + ' }')
                mapping.append({'kind': 'state_action', 'source_id': subaction['id'],
                                'span': body['span'], 'target_owner': target, 'target_role': emitted_role,
                                'source_role': role})
        for edge, body in transition_hooks.get(node['id'], []):
            abstract_line, target_action = abstract_action(body, 'exit', used_action_names)
            lines.append(indent + '    ' + abstract_line)
            mapping.append({'kind': 'transition_effect_hook', 'source_id': body.get('id'),
                            'span': body.get('span'), 'target_owner': target,
                            'target_role': 'exit', 'representation': 'abstract_hook',
                            'target_action': target_action, 'transition_id': edge.get('id'),
                            'argument_references': body.get('argument_references', [])})
        child_ids = {c['id'] for c in node['states']}
        for child in node['states']:
            if child['id'] in pseudo_initial_ids:
                mapping.append({'kind': 'pseudo_state', 'source_id': child['id'],
                                'span': child['span'], 'target': '[*]', 'reason': 'typed_initial_usage'})
                continue
            lines.extend(emit(child, target + '.', indent + '    '))
        initial = 0
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
            mapped_source, source_path = direct_child_for(edge['source'], node)
            mapped_target, target_path = direct_child_for(edge['target'], node)
            if mapped_target is None and not terminal_target:
                raise Unsupported('transition_target', str(edge['target']))
            if edge['source'] in pseudo_initial_ids:
                src = '[*]'
                initial += 1
            elif edge['source'] in entry_ids or edge['source'] == 'States::StateAction::start':
                src = '[*]'
                initial += 1
            elif mapped_source is not None:
                src = names[mapped_source]
            else:
                raise Unsupported('transition_source', str(edge['source']))
            terms = [events[event] for event in triggers]
            if edge['guards']:
                terms.append('[' + ' and '.join(expression(g, variables, structural_variables,
                                                        external_variables, declarations,
                                                        external_mappings) for g in edge['guards']) + ']')
            if not terms:
                trigger = ''
            elif triggers:
                trigger = ' : ' + ' + '.join(terms)
            else:
                # FCSTM spells a guard-only transition ``: if [expr]``.
                trigger = ' : if ' + terms[0]
            effects = ' '.join(action(a) for a in edge['effects']
                               if a.get('kind') not in {'ActionUsage', 'PerformActionUsage', 'SendActionUsage'})
            effect = ' effect { ' + effects + ' }' if effects else ''
            destination = '[*]' if terminal_target else names[mapped_target]
            lines.append(indent + f'    {src} -> {destination}{trigger}{effect};')
            transition_mapping = {'kind': 'transition', 'source_id': edge['id'], 'span': edge['span'],
                                  'target_owner': target, 'target_declaration_index': index}
            if source_path:
                transition_mapping['source_endpoint_path'] = source_path
                transition_mapping['source_endpoint_target'] = names[mapped_source]
            if target_path:
                transition_mapping['target_endpoint_path'] = target_path
                transition_mapping['target_endpoint_target'] = names[mapped_target]
            mapping.append(transition_mapping)
        effective_child_ids = child_ids - pseudo_initial_ids
        if effective_child_ids and initial == 0:
            # Some SysML examples define a composite state without an explicit
            # initial succession. Choose its first typed child so FCSTM can
            # execute the model; the choice is recorded as a profile default.
            fallback = next(child for child in node['states'] if child['id'] in effective_child_ids)
            lines.append(indent + f'    [*] -> {names[fallback["id"]]};')
            mapping.append({'kind': 'implicit_initial', 'target': names[fallback['id']],
                            'source_owner': target, 'reason': 'missing_initial_profile_default'})
            initial = 1
        # FCSTM permits multiple initial edges. The runtime evaluates them in
        # source order; this profile uses that order when SysML has no priority.
        lines.append(indent + '}')
        return lines
    emitted = emit(root, '', '')
    mapping.extend(external_mappings)
    return '\n'.join(declarations + emitted) + '\n', mapping


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
                                    'Assignment do-actions execute as FCSTM during operations once per active cycle; this is a periodic profile approximation.',
                                    'Multiple initial transitions preserve source order; FCSTM runtime selects the first enabled edge.',
                                    'When SysML leaves same-source transition priority unspecified, FCSTM uses declaration order.',
                                    'Typed transition action effects are represented as exit hooks on the source state; receiver and payload stay in mapping metadata.',
                                    'Behavior declared inside a scalar part is retained in ignored_structural mapping; its execution is not synthesized.',
                                    'Reference and port usages used as typed action channels are retained as opaque hook metadata; object identity, port routing, and message queues are not synthesized.',
                                    'Non-linear or incomplete typed action succession is kept as one opaque hook; inner order is not synthesized.',
                                    'Typed quantity literals keep their magnitude; linked library units are erased for the FCSTM numeric domain.',
                                    'A scalar feature chain outside the control state is represented by a generated numeric input with default zero; the source path and typed target remain in mapping.',
                                    'A do-action on a composite state is emitted as an entry hook because FCSTM has no composite during operation; the source role remains in mapping.',
                                    'A nested transition endpoint is lifted to its direct child only when typed entry follows one deterministic descent path; the full endpoint path remains in mapping.']}, indent=2) + '\n')
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
               'converted_unique_source_hashes': len({r['sha256'] for r in rows if r['status'] == 'converted'}),
               'converted_unique_control_source_hashes': len({r['sha256'] for r in control_candidates if r['status'] == 'converted'}),
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
