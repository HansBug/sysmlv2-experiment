import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import com.google.gson.*;
import org.eclipse.xtext.resource.XtextResource;
import org.eclipse.xtext.validation.CheckMode;
import org.eclipse.xtext.util.CancelIndicator;
import org.eclipse.xtext.diagnostics.Severity;
import org.omg.sysml.interactive.SysMLInteractive;
import org.omg.sysml.lang.sysml.*;

/** Check official linked facts before attributing converter rejection to the frontend. */
public class AuditFrontend {
    static List<Map<String, Object>> projectContext(SysMLInteractive workspace, Path directory) throws Exception {
        var rows = new ArrayList<Map<String, Object>>();
        List<Path> files;
        try (var paths = Files.list(directory)) {
            files = paths.filter(p -> p.toString().endsWith(".sysml")).sorted().toList();
        }
        for (var path : files) {
            var result = workspace.process(Files.readString(path), false);
            if (result.getException() != null) throw new AssertionError(result.getException());
            rows.add(ExtractStates.object("source", path.getFileName().toString(),
                "sha256", HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))),
                "isolated_errors", result.hasErrors(),
                "isolated_error_count", result.getIssues().stream().filter(issue -> issue.getSeverity() == Severity.ERROR).count(),
                "isolated_issues", result.formatIssues()));
            workspace.removeResource();
        }
        // Index all companion resources before asking the official validator to link them.
        workspace.readAll(directory.toAbsolutePath().normalize().toString(), true, ".sysml");
        for (int i = 0; i < files.size(); i++) {
            var resource = (XtextResource)workspace.getResource(files.get(i).toAbsolutePath().normalize().toString());
            var issues = resource.getResourceServiceProvider().getResourceValidator()
                .validate(resource, CheckMode.ALL, CancelIndicator.NullImpl);
            rows.get(i).put("project_errors", issues.stream().anyMatch(issue -> issue.getSeverity() == Severity.ERROR));
            rows.get(i).put("project_error_count", issues.stream().filter(issue -> issue.getSeverity() == Severity.ERROR).count());
            rows.get(i).put("project_issues", issues.stream().map(issue -> ExtractStates.object(
                "severity", issue.getSeverity().toString(), "message", issue.getMessage(),
                "code", issue.getCode(), "line", issue.getLineNumber())).toList());
        }
        var linked = rows.stream().filter(row -> row.get("source").equals("ServerSequenceModelOutside.sysml")).findFirst().orElseThrow();
        if (!Boolean.TRUE.equals(linked.get("isolated_errors")) || !Boolean.FALSE.equals(linked.get("project_errors")))
            throw new AssertionError("The public companion-file contrast did not reproduce");
        return rows;
    }

    public static void main(String[] args) throws Exception {
        var workspace = SysMLInteractive.createInstance();
        workspace.setVerbose(false);
        workspace.loadLibrary(Path.of(args[0]).toAbsolutePath().normalize().toString());
        var observations = new LinkedHashMap<String, Object>();
        var definitions = workspace.process(Files.readString(Path.of("research/cases/types.sysml")));
        var definitionsResource = workspace.getResource();
        var application = workspace.process(Files.readString(Path.of("research/cases/app.sysml")));
        var applicationResource = workspace.getResource();
        if (definitions.getException() != null) throw new AssertionError(definitions.getException());
        if (application.getException() != null) throw new AssertionError(application.getException());
        if (definitions.hasErrors() || application.hasErrors()) throw new AssertionError("Official project context failed");
        var usage = (StateUsage)workspace.resolve("App::Device::controller");
        var definition = (StateDefinition)workspace.resolve("Types::Controller");
        var inherited = usage.getInheritedMembership().stream()
            .filter(m -> m.eResource() == definition.eResource() && m.getMemberElement() instanceof StateUsage)
            .map(m -> m.getMemberElement().getQualifiedName()).toList();
        ExtractStates.inputResources = Set.of(definitionsResource, applicationResource);
        var exported = ExtractStates.state(usage, new HashSet<>());
        observations.put("cross_file", Map.of("official_inherited_states", inherited, "exported", exported));
        if (inherited.size() != 2) throw new AssertionError("Expected two linked inherited states");
        if (((List<?>)exported.get("states")).size() != 2) throw new AssertionError("Cross-file state export did not include both linked states");

        var modern = workspace.process("package Modern { state def Controller { first start then A; state A; state B; transition first A if true then B; } }");
        if (modern.getException() != null) throw new AssertionError(modern.getException());
        if (modern.hasErrors()) throw new AssertionError(modern.formatIssues());
        ExtractStates.inputResources = Set.of(definitionsResource, applicationResource, workspace.getResource());
        var root = (StateDefinition)workspace.resolve("Modern::Controller");
        var sources = new ArrayList<Object>();
        for (var member : root.getOwnedMembership()) {
            if (member.getMemberElement() instanceof TransitionUsage t) {
                var source = t.getSource();
                sources.add(Map.of("source_kind", source.eClass().getName(), "source_id", ExtractStates.id(source)));
            }
        }
        observations.put("modern_start", Map.of("sources", sources, "exported", ExtractStates.state(root, new HashSet<>())));

        var oldResult = workspace.process("package ConstructorProbe { attribute def Signal; part receiver; action go { send Signal() to receiver; } }", false);
        var newResult = workspace.process("package ConstructorProbe { attribute def Signal; part receiver; action go { send new Signal() to receiver; } }", false);
        if (oldResult.getException() != null) throw new AssertionError(oldResult.getException());
        if (newResult.getException() != null) throw new AssertionError(newResult.getException());
        observations.put("constructor", Map.of("old_errors", oldResult.hasErrors(), "old_issues", oldResult.formatIssues(),
            "new_errors", newResult.hasErrors(), "new_issues", newResult.formatIssues()));
        if (!oldResult.hasErrors() || newResult.hasErrors()) throw new AssertionError("Constructor comparison did not reproduce");
        workspace.removeResource();
        observations.put("project_context", projectContext(workspace,
            Path.of("_external/benchmark/data/examples/Interaction Sequencing Examples")));
        Files.writeString(Path.of(args[1]), new GsonBuilder().setPrettyPrinting().serializeNulls().create().toJson(observations) + "\n");
        System.out.println("PASS: official cross-file linking and modern syntax; exporter boundary reproduced independently");
    }
}
