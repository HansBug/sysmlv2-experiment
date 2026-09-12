// Probe the existing sysml-2ls runtime; no HTTP service or parser fork is needed.
const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const {createRequire} = require('node:module');

async function main() {
    const [rootArg, library, output] = process.argv.slice(2);
    assert(rootArg && library && output, 'Usage: node legacy_probe.cjs LANGUAGE_SERVER_PACKAGE LIBRARY OUTPUT');
    const root = path.resolve(rootArg);
    const req = createRequire(path.join(root, 'package.json'));
    const {createSysMLServices} = require(path.join(root, 'lib/sysml-module.js'));
    const {SysMLNodeFileSystem} = require(path.join(root, 'lib/node/node-file-system-provider.js'));
    const {URI} = req('vscode-uri');
    const {streamAllContents} = req('langium');
    const services = createSysMLServices(SysMLNodeFileSystem, {
        standardLibrary: true, standardLibraryPath: path.resolve(library),
        skipWorkspaceInit: false, logStatistics: false,
    });
    await services.shared.workspace.WorkspaceManager.initializeWorkspace([]);
    const names = ['types', 'app', 'parallel', 'actions', 'inheritance', 'invalid-type', 'invalid-target', 'constant'];
    const docs = names.map(name => {
        const file = path.join(__dirname, 'cases', name + '.sysml');
        return services.shared.workspace.LangiumDocumentFactory.fromString(fs.readFileSync(file, 'utf8'), URI.file(file));
    });
    docs.forEach(doc => services.shared.workspace.LangiumDocuments.addDocument(doc));
    await services.shared.workspace.DocumentBuilder.build(docs, {
        standalone: false, standardLibrary: 'standard', validationChecks: 'all',
    });
    const rows = docs.map((doc, index) => ({
        name: names[index],
        lexerErrors: doc.parseResult.lexerErrors.map(e => e.message),
        parserErrors: doc.parseResult.parserErrors.map(e => e.message),
        diagnostics: (doc.diagnostics || []).map(d => ({severity: d.severity, message: d.message})),
        elements: [...streamAllContents(doc.parseResult.value)]
            .filter(n => ['StateDefinition', 'StateUsage', 'ExhibitStateUsage', 'TransitionUsage', 'StateSubactionMembership'].includes(n.$type))
            .map(n => {
                const meta = n.$meta;
                return {
                    kind: n.$type, name: meta.qualifiedName, parallel: meta.isParallel,
                    owner: meta.owner()?.qualifiedName,
                    source: n.$type === 'TransitionUsage' ? meta.source?.element()?.qualifiedName : undefined,
                    // Related features are linked connector ends, including the entry action on initial transitions.
                    related: meta.then?.element()?.relatedFeatures().map(f => f?.qualifiedName),
                    guard: meta.guard?.element()?.nodeType(), effect: meta.effect?.element()?.nodeType(),
                    subactionKind: n.$type === 'StateSubactionMembership' ? meta.kind : undefined,
                    types: meta.allTypes ? [...meta.allTypes()].map(t => t.qualifiedName)
                        .filter(t => t?.startsWith('Types::') || t?.startsWith('Inheritance::')) : undefined,
                    span: n.$cstNode ? {offset: n.$cstNode.offset, length: n.$cstNode.length} : undefined,
                };
            }),
    }));
    fs.writeFileSync(output, JSON.stringify(rows, null, 2) + '\n');
    const errors = r => r.lexerErrors.length + r.parserErrors.length + r.diagnostics.filter(d => d.severity === 1).length;
    for (const row of rows) assert.equal(errors(row) > 0, ['invalid-type', 'invalid-target', 'constant'].includes(row.name), row.name);
    const transition = rows[0].elements.find(e => e.name === 'Types::Controller::turnOn');
    assert.equal(transition.source, 'Types::Controller::Idle');
    assert.deepEqual(transition.related, ['Types::Controller::Idle', 'Types::Controller::Active']);
    assert.equal(transition.guard, 'LiteralBoolean');
    assert(rows[1].elements[0].types.includes('Types::Controller'));
    assert(rows[2].elements.some(e => e.parallel === true));
    assert(rows[3].elements.some(e => e.effect === 'AssignmentActionUsage'));
    assert(rows[4].elements.some(e => e.types?.includes('Types::Controller')));
    assert(transition.span.length > 0);
    console.log('PASS: linked hierarchy, endpoints, guard, assignment, subactions, typing, inheritance, parallel detection, source spans, and rejection probes');
}

main();
