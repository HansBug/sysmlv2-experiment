"""Cross-check every reported root and candidate against the exported typed source tree."""
import json
from collections import Counter
from pathlib import Path
import sys


def check(expected, report, identity, root_count):
    rows = [row for row in report['records'] if 'state' in row]
    actual = Counter((*(row[key] for key in identity), row['state'], row['has_control_states'])
                     for row in rows)
    assert actual == Counter(expected), '转换报告必须逐根对应源 AST，候选标记不能由拒绝原因反推'
    summary = report['summary']
    assert summary[root_count] == len(expected)
    assert summary['control_candidates'] == sum(item[-1] for item in expected)
    assert summary['converted_control_candidates'] == sum(
        row['status'] == 'converted' and row['has_control_states'] for row in rows)


if __name__ == '__main__':
    artifact = Path(sys.argv[1])
    source = json.loads((artifact / 'corpus-source.json').read_text(encoding='utf-8'))
    expected = [(file['dataset'], file['source'], file['sha256'], root['id'], bool(root['states']))
                for file in source['models'] if file['status'] == 'extracted'
                for root in file['states']]
    report = json.loads((artifact / 'converted/results.json').read_text(encoding='utf-8'))
    check(expected, report, ('dataset', 'source', 'sha256'), 'extracted_state_roots')
    expected = []
    for path in sorted((artifact / 'project-contexts').glob('*.json')):
        if path.name == 'summary.json':
            continue
        project = json.loads(path.read_text(encoding='utf-8'))
        expected.extend((project['project'], file['source'], root['id'], bool(root['states']))
                        for file in project['files'] for root in file.get('states', []))
    report = json.loads((artifact / 'project-context-conversion.json').read_text(encoding='utf-8'))
    check(expected, report, ('project', 'source'), 'state_roots')
    print('通过：独立批次及项目批次逐根登记完整，候选数直接匹配源状态树。')
