"""Register every public SysML file containing typed state elements."""
import json
from pathlib import Path
import sys

def register(source, output, markdown):
    inventory = json.loads(Path(source).read_text(encoding='utf-8'))
    rows = []
    for item in inventory:
        if item['dataset'] == 'synthetic' or not item['state_roots']:
            continue
        path = Path(item['source'])
        rows.append({**{key: item[key] for key in ('dataset','source','sha256','syntax_errors','state_definitions','state_usages','state_roots','validation_status')},
            'context_directory': str(path.parent),
            'context_status': 'needs_project_index' if item['validation_status'] != 'extracted' else 'validated_independent_file',
            'conversion_status': 'baseline_extracted' if item['validation_status'] == 'extracted' else 'not_reached'})
    rows.sort(key=lambda item: (item['dataset'], item['source']))
    payload = {'description': '逐个登记语法树中含 StateDefinition/StateUsage 的公开文件；不是可执行控制器清单。', 'count': len(rows), 'assets': rows}
    Path(output).write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    lines = ['# SysML v2 状态资产逐文件登记', '', '本表由官方 Pilot 的 typed AST 生成，不通过字符串搜索。每一行保留数据集、相对路径、SHA-256、语法状态节点数、完整校验状态和建议的项目上下文目录。`validated_independent_file` 只表示单文件加标准库通过，`needs_project_index` 表示应在其工程目录整体索引后复核。', '', f'共登记 **{len(rows)}** 个公开状态候选文件。它们不是可执行控制器清单；一个文件可包含多个状态根，状态 usage 也可能是 snapshot 或语义不完整。', '', '| 数据集 | 文件 | SHA-256（前 12 位） | 定义/使用/根 | 语法 | 基线校验 | 上下文目录 |', '|---|---|---|---:|---|---|---|']
    lines += [f"| {item['dataset']} | `{item['source']}` | `{item['sha256'][:12]}` | {item['state_definitions']}/{item['state_usages']}/{item['state_roots']} | {'错误' if item['syntax_errors'] else '有效'} | {item['validation_status']} | `{item['context_directory']}` |" for item in rows]
    lines += ['', '机器可读版本：[state-assets.json](state-assets.json)。重新生成：`python research/register_state_assets.py artifacts/syntax-state-inventory.json research/state-assets.json research/state-assets.zh.md`。', '']
    Path(markdown).write_text('\n'.join(lines), encoding='utf-8')

if __name__ == '__main__':
    register(*sys.argv[1:])
