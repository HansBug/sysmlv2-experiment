import java.nio.file.*;
import java.util.*;
import com.google.gson.*;
import org.eclipse.emf.ecore.EObject;
import org.eclipse.xtext.nodemodel.util.NodeModelUtils;
import org.omg.sysml.interactive.SysMLInteractive;
import org.omg.sysml.lang.sysml.*;

/** Export linked state facts for independently parsed corpus files. No execution semantics are invented here. */
public class ExtractStates {
    static final Gson JSON = new GsonBuilder().setPrettyPrinting().serializeNulls().create();
    static Map<String, Object> object(Object... pairs) {
        var out = new LinkedHashMap<String, Object>();
        for (int i = 0; i < pairs.length; i += 2) out.put((String)pairs[i], pairs[i + 1]);
        return out;
    }
    static String id(Element e) {
        if (e == null) return null;
        var node = NodeModelUtils.getNode(e);
        return e.getQualifiedName() != null ? e.getQualifiedName() : "@" + (node == null ? "implicit" : node.getOffset());
    }
    static Object span(Element e) {
        var n = NodeModelUtils.getNode(e);
        return n == null ? null : object("offset", n.getOffset(), "length", n.getLength(), "line", n.getStartLine());
    }
    static Object expression(Expression e) {
        if (e == null) return null;
        var out = object("kind", e.eClass().getName(), "span", span(e));
        if (e instanceof LiteralBoolean v) out.put("value", v.isValue());
        else if (e instanceof LiteralInteger v) out.put("value", v.getValue());
        else if (e instanceof LiteralRational v) out.put("value", v.getValue());
        else if (e instanceof FeatureReferenceExpression v) out.put("referent", id(v.getReferent()));
        else if (e instanceof OperatorExpression v) {
            out.put("operator", v.getOperator());
            out.put("operands", v.getArgument().stream().map(ExtractStates::expression).toList());
        }
        return out;
    }
    static Object action(ActionUsage a) {
        if (a instanceof AssignmentActionUsage v)
            return object("kind", "assign", "target", id(v.getReferent()), "value", expression(v.getValueExpression()), "span", span(a));
        var node = NodeModelUtils.getNode(a);
        // The official parser represents an empty subaction with a zero-length
        // ActionUsage node. Named/typed/performed actions remain unsupported.
        boolean empty = a.eClass() == SysMLPackage.Literals.ACTION_USAGE && a.getOwnedMembership().isEmpty()
            && node != null && node.getLength() == 0;
        return object("kind", empty ? "empty" : a.eClass().getName(), "span", span(a));
    }
    static Map<String, Object> state(Type s, Set<Type> ancestors) {
        if (!ancestors.add(s)) return object("id", id(s), "unsupported", List.of("recursive_state_typing"));
        var children = new ArrayList<Object>();
        var transitions = new ArrayList<Object>();
        var actions = new ArrayList<Object>();
        var data = new ArrayList<Object>();
        var unsupported = new ArrayList<String>();
        if (!scalar(s)) unsupported.add("state_multiplicity");
        var memberships = new LinkedHashSet<Membership>(s.getOwnedMembership());
        memberships.addAll(s.getInheritedMembership());
        for (Membership member : memberships) {
            // Library feature inheritance is not a user control-state declaration.
            if (member.eResource() != s.eResource()) continue;
            Element e = member.getMemberElement();
            if (e instanceof StateUsage child) children.add(state(child, new HashSet<>(ancestors)));
            else if (member instanceof StateSubactionMembership sub && e instanceof ActionUsage a) {
                actions.add(object("id", id(a), "role", sub.getKind().getLiteral(),
                    "action", action(a)));
            }
            else if (e instanceof TransitionUsage t) {
                transitions.add(object("id", id(t), "source", id(t.getSource()), "target", id(t.getTarget()),
                    "guards", t.getGuardExpression().stream().map(ExtractStates::expression).toList(),
                    "effects", t.getEffectAction().stream().map(ExtractStates::action).toList(),
                    "trigger_count", t.getTriggerAction().size(), "span", span(t)));
            } else if (e instanceof SuccessionAsUsage t) {
                transitions.add(object("id", id(t), "source", id(t.getSourceFeature()),
                    "target", t.getTargetFeature().size() == 1 ? id(t.getTargetFeature().get(0)) : null,
                    "guards", List.of(), "effects", List.of(), "trigger_count", 0, "span", span(t)));
            } else if (e instanceof AttributeUsage v) {
                var values = new ArrayList<Object>();
                for (var relation : v.getOwnedRelationship())
                    if (relation instanceof FeatureValue fv) values.add(expression(fv.getValue()));
                data.add(object("id", id(v), "types", v.getAttributeDefinition().stream().map(ExtractStates::id).toList(),
                    "values", values, "constant", v.isConstant(), "scalar", scalar(v), "span", span(v)));
            } else if (!(e instanceof Comment) && !(e instanceof Documentation)) {
                unsupported.add(e.eClass().getName());
            }
        }
        boolean parallel = s instanceof StateDefinition d ? d.isParallel() : ((StateUsage)s).isParallel();
        return object("id", id(s), "parallel", parallel, "span", span(s), "states", children,
            "transitions", transitions, "actions", actions, "data", data, "unsupported", unsupported);
    }
    static boolean scalar(Type type) {
        var multiplicity = type.getMultiplicity();
        if (multiplicity == null) return true;
        // MultiplicityAdapter documents that the grammar inserts an empty
        // Multiplicity for omitted bounds. Our controller profile uses one
        // instance for this default; explicit ranges still require [1..1].
        if (multiplicity.eClass() == SysMLPackage.Literals.MULTIPLICITY
            && NodeModelUtils.getNode(multiplicity) == null) return true;
        if (!(multiplicity instanceof MultiplicityRange range)) return false;
        return range.getUpperBound() instanceof LiteralInteger upper && upper.getValue() == 1
            && (range.getLowerBound() == null || range.getLowerBound() instanceof LiteralInteger lower && lower.getValue() == 1);
    }
    static boolean topState(EObject e) {
        if (!(e instanceof StateUsage) && !(e instanceof StateDefinition)) return false;
        for (EObject p = e.eContainer(); p != null; p = p.eContainer())
            if (p instanceof StateUsage || p instanceof StateDefinition) return false;
        return true;
    }
    public static void main(String[] args) throws Exception {
        var workspace = SysMLInteractive.createInstance();
        workspace.setVerbose(false);
        // Pilot's EMF loader misinterprets escaped spaces in relative library
        // paths. Resolve the library root before it constructs resource URIs.
        workspace.loadLibrary(Path.of(args[0]).toAbsolutePath().normalize().toString());
        var manifest = JsonParser.parseString(Files.readString(Path.of(args[1]))).getAsJsonObject();
        var results = new ArrayList<Object>();
        for (var entry : manifest.getAsJsonArray("files")) {
            var source = entry.getAsJsonObject();
            var text = Files.readString(Path.of(source.get("path").getAsString()));
            System.out.println("SOURCE " + source.get("dataset").getAsString() + " " + source.get("source").getAsString());
            var record = object("dataset", source.get("dataset").getAsString(), "source", source.get("source").getAsString(),
                "sha256", source.get("sha256").getAsString(), "context", "independent-file-with-standard-library");
            var result = workspace.process(text, false);
            if (result.getException() != null) {
                record.put("status", "frontend_error");
                record.put("detail", result.getException().toString());
            } else if (result.hasErrors()) {
                record.put("status", "source_validation_error");
                record.put("detail", result.formatIssues());
            } else {
                var roots = new ArrayList<Object>();
                var tree = workspace.getRootElement().eAllContents();
                while (tree.hasNext()) {
                    var element = tree.next();
                    if (topState(element)) roots.add(state((Type)element, new HashSet<>()));
                }
                record.put("status", "extracted");
                record.put("states", roots);
                record.put("detail", result.formatIssues());
                workspace.removeResource();
            }
            results.add(record);
        }
        Files.writeString(Path.of(args[2]), JSON.toJson(object("models", results)) + "\n");
    }
}
