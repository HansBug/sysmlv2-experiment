import java.nio.file.*;
import java.util.*;
import com.google.gson.*;
import org.eclipse.emf.ecore.EObject;
import org.omg.sysml.lang.sysml.*;

/** Count typed state nodes before full validation can discard the source resource. */
public class SysmlStateInventory {
    public static void main(String[] args) throws Exception {
        var workspace = org.omg.sysml.interactive.SysMLInteractive.createInstance();
        workspace.setVerbose(false);
        var manifest = JsonParser.parseString(Files.readString(Path.of(args[0]))).getAsJsonObject();
        var validated = new HashMap<String, JsonObject>();
        if (args.length > 2) {
            var baseline = JsonParser.parseString(Files.readString(Path.of(args[2]))).getAsJsonObject();
            for (var value : baseline.getAsJsonArray("models")) {
                var model = value.getAsJsonObject();
                validated.put(model.get("dataset").getAsString() + "/" + model.get("source").getAsString(), model);
            }
        }
        var rows = new ArrayList<Map<String, Object>>();
        for (var item : manifest.getAsJsonArray("files")) {
            var file = item.getAsJsonObject();
            workspace.next(".sysml");
            workspace.parse(Files.readString(Path.of(file.get("path").getAsString())));
            var result = ((org.eclipse.xtext.resource.XtextResource)workspace.getResource()).getParseResult();
            int definitions = 0, usages = 0, roots = 0;
            var tree = result.getRootASTElement().eAllContents();
            while (tree.hasNext()) {
                var node = tree.next();
                if (node instanceof StateDefinition) definitions++;
                if (node instanceof StateUsage) usages++;
                if (node instanceof StateDefinition || node instanceof StateUsage) {
                    boolean nested = false;
                    for (EObject owner = node.eContainer(); owner != null; owner = owner.eContainer())
                        if (owner instanceof StateDefinition || owner instanceof StateUsage) nested = true;
                    if (!nested) roots++;
                }
            }
            var row = new LinkedHashMap<String, Object>();
            row.put("dataset", file.get("dataset").getAsString());
            row.put("source", file.get("source").getAsString());
            row.put("sha256", file.get("sha256").getAsString());
            row.put("syntax_errors", result.hasSyntaxErrors());
            row.put("state_definitions", definitions);
            row.put("state_usages", usages);
            row.put("state_roots", roots);
            if (args.length > 2) {
                var model = validated.get(row.get("dataset") + "/" + row.get("source"));
                if (model == null || !model.get("sha256").getAsString().equals(row.get("sha256")))
                    throw new AssertionError("Manifest and validated baseline differ: " + row);
                var status = model.get("status").getAsString();
                row.put("validation_status", status);
                if (status.equals("extracted")) {
                    int validatedRoots = model.getAsJsonArray("states").size();
                    row.put("validated_roots", validatedRoots);
                    if (result.hasSyntaxErrors() || (roots > 0) != (validatedRoots > 0))
                        throw new AssertionError("Syntax inventory disagrees with validated extraction: " + row);
                }
            }
            rows.add(row);
            workspace.removeResource();
        }
        if (rows.size() != manifest.getAsJsonArray("files").size()) throw new AssertionError("Incomplete inventory");
        Files.writeString(Path.of(args[1]), new GsonBuilder().setPrettyPrinting().create().toJson(rows) + "\n");
    }
}
