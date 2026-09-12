import java.nio.file.*;
import java.util.*;
import com.google.gson.*;
import org.eclipse.emf.ecore.EObject;
import org.eclipse.emf.ecore.resource.Resource;
import org.eclipse.xtext.resource.XtextResource;
import org.eclipse.xtext.resource.IResourceServiceProvider;
import org.eclipse.xtext.validation.CheckMode;
import org.eclipse.xtext.util.CancelIndicator;
import org.eclipse.xtext.diagnostics.Severity;
import org.omg.sysml.interactive.SysMLInteractive;
import org.omg.sysml.lang.sysml.Element;

/** Load one SysML project with its companion files before exporting typed state facts. */
public class ExtractProject {
    static boolean topState(EObject value) {
        if (!(value instanceof org.omg.sysml.lang.sysml.StateUsage)
            && !(value instanceof org.omg.sysml.lang.sysml.StateDefinition)) return false;
        for (EObject owner = value.eContainer(); owner != null; owner = owner.eContainer())
            if (owner instanceof org.omg.sysml.lang.sysml.StateUsage
                || owner instanceof org.omg.sysml.lang.sysml.StateDefinition) return false;
        return true;
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("usage: ExtractProject LIBRARY PROJECT OUTPUT");
        var workspace = SysMLInteractive.createInstance();
        workspace.setVerbose(false);
        workspace.loadLibrary(Path.of(args[0]).toAbsolutePath().normalize().toString());
        Path project = Path.of(args[1]).toAbsolutePath().normalize();
        workspace.readAll(project.toString(), true, ".sysml");
        var inputs = new LinkedHashSet<Resource>();
        for (Resource resource : workspace.getResourceSet().getResources())
            if (workspace.isInputResource(resource)) inputs.add(resource);
        ExtractStates.inputResources = inputs;
        var hashes = new LinkedHashMap<Resource, String>();
        for (Resource resource : inputs)
            hashes.put(resource, ExtractStates.sha256(Path.of(resource.getURI().toFileString())));
        ExtractStates.inputHashes = hashes;
        var files = new ArrayList<Object>();
        for (Resource resource : inputs) {
            var provider = IResourceServiceProvider.Registry.INSTANCE.getResourceServiceProvider(resource.getURI());
            var issues = provider.getResourceValidator()
                .validate(resource, CheckMode.ALL, CancelIndicator.NullImpl);
            var row = ExtractStates.object("source", Path.of(resource.getURI().toFileString()).toString(),
                "errors", issues.stream().filter(issue -> issue.getSeverity() == Severity.ERROR).count(),
                "issues", issues.stream().map(issue -> ExtractStates.object(
                    "severity", issue.getSeverity().toString(), "message", issue.getMessage(),
                    "code", issue.getCode(), "line", issue.getLineNumber())).toList());
            if (issues.stream().noneMatch(issue -> issue.getSeverity() == Severity.ERROR)) {
                var roots = new ArrayList<Object>();
                for (EObject content : resource.getContents()) {
                    var tree = content.eAllContents();
                    while (tree.hasNext()) {
                        var element = tree.next();
                        if (topState(element)) roots.add(ExtractStates.state((org.omg.sysml.lang.sysml.Type) element, new HashSet<>()));
                    }
                }
                row.put("status", "validated");
                row.put("states", roots);
            } else {
                row.put("status", "validation_error");
                row.put("states", List.of());
            }
            files.add(row);
        }
        var output = Path.of(args[2]);
        Files.writeString(output, new GsonBuilder().setPrettyPrinting().serializeNulls().create()
            .toJson(ExtractStates.object("project", project.toString(), "files", files)) + "\n");
    }
}
