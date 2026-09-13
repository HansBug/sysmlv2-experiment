import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import com.google.gson.*;
import org.eclipse.emf.ecore.EObject;
import org.eclipse.emf.ecore.resource.Resource;
import org.eclipse.xtext.nodemodel.util.NodeModelUtils;
import org.omg.sysml.interactive.SysMLInteractive;
import org.omg.sysml.lang.sysml.*;

/** Export linked state facts for independently parsed corpus files. No execution semantics are invented here. */
public class ExtractStates {
    static final Gson JSON = new GsonBuilder().setPrettyPrinting().serializeNulls().create();
    /** Input resources are project files; all other resources are libraries. */
    static Set<Resource> inputResources = Set.of();
    /** Hashes let inherited elements retain the file that actually defines them. */
    static Map<Resource, String> inputHashes = Map.of();
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
        if (n == null) return null;
        var resource = e.eResource();
        return object("offset", n.getOffset(), "length", n.getLength(), "line", n.getStartLine(),
            "source_uri", resource == null || resource.getURI() == null ? null : resource.getURI().toString(),
            "source_sha256", resource == null ? null : inputHashes.get(resource));
    }
    static String sha256(Path path) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
    }
    static Object expression(Expression e) {
        if (e == null) return null;
        var out = object("kind", e.eClass().getName(), "span", span(e));
        if (e instanceof LiteralBoolean v) out.put("value", v.isValue());
        else if (e instanceof LiteralInteger v) out.put("value", v.getValue());
        else if (e instanceof LiteralRational v) out.put("value", v.getValue());
        else if (e instanceof FeatureReferenceExpression v) {
            out.put("referent", id(v.getReferent()));
            out.put("referent_element", elementReference(v.getReferent()));
        }
        else if (e instanceof OperatorExpression v) {
            out.put("operator", v.getOperator());
            out.put("operands", v.getArgument().stream().map(ExtractStates::expression).toList());
            if (e instanceof FeatureChainExpression chain) {
                out.put("target_feature", elementReference(chain.getTargetFeature()));
                out.put("source_target_feature", elementReference(chain.sourceTargetFeature()));
            }
            if ("[".equals(v.getOperator()) && v.getArgument().size() == 2)
                out.put("unit", expression(v.getArgument().get(1)));
        }
        return out;
    }
    static Object elementReference(Element e) {
        if (e == null) return null;
        return object("id", id(e), "kind", e.eClass().getName(),
            "declared_name", e.getDeclaredName(), "library", e.isLibraryElement());
    }
    /** Export a linear typed action succession; branching remains explicit as an error. */
    static Object actionSequence(ActionUsage action) {
        var members = action.getOwnedMembership().stream()
            .filter(m -> m instanceof FeatureMembership)
            .map(m -> ((FeatureMembership)m).getMemberElement())
            .filter(e -> e instanceof ActionUsage)
            .map(e -> (ActionUsage)e).toList();
        if (members.isEmpty()) return null;
        var byId = new LinkedHashMap<String, ActionUsage>();
        for (var member : members) byId.put(id(member), member);
        var next = new LinkedHashMap<String, String>();
        var starts = new ArrayList<String>();
        var ends = new ArrayList<String>();
        for (var membership : action.getOwnedMembership()) {
            if (!(membership instanceof FeatureMembership fm)
                || !(fm.getMemberElement() instanceof SuccessionAsUsage succession)) continue;
            var source = succession.getSourceFeature();
            var targets = succession.getTargetFeature();
            if (targets.size() != 1) return object("error", "non_single_target");
            var sourceId = source == null ? null : id(source);
            var targetId = id(targets.get(0));
            if (!byId.containsKey(targetId)) {
                if (sourceId != null && byId.containsKey(sourceId)) ends.add(sourceId);
            } else if (sourceId == null || !byId.containsKey(sourceId)) {
                starts.add(targetId);
            } else if (next.put(sourceId, targetId) != null) {
                return object("error", "branching_source");
            }
        }
        if (starts.size() != 1 || ends.size() != 1) return object("error", "sequence_boundary");
        var ordered = new ArrayList<Object>();
        var seen = new HashSet<String>();
        var current = starts.get(0);
        while (current != null && seen.add(current)) {
            var member = byId.get(current);
            if (member == null) return object("error", "unresolved_member");
            ordered.add(object("id", id(member), "kind", member.eClass().getName(),
                "declared_name", member.getDeclaredName(), "library", member.isLibraryElement(),
                "definitions", member.getActionDefinition().stream()
                    .map(ExtractStates::elementReference).toList()));
            current = next.get(current);
        }
        if (seen.size() != members.size() || !seen.contains(ends.get(0))) return object("error", "non_linear");
        return ordered;
    }
    static Object action(ActionUsage a) {
        if (a instanceof AssignmentActionUsage v)
            return object("kind", "assign", "target", id(v.getReferent()),
                "target_expression", expression(v.getTargetArgument()),
                "value", expression(v.getValueExpression()), "span", span(a));
        var node = NodeModelUtils.getNode(a);
        // The official parser represents an empty subaction with a zero-length
        // ActionUsage node. Named/typed/performed actions remain unsupported.
        boolean empty = a.eClass() == SysMLPackage.Literals.ACTION_USAGE && a.getOwnedMembership().isEmpty()
            && node != null && node.getLength() == 0;
        var out = object("kind", empty ? "empty" : a.eClass().getName(), "id", id(a),
            "declared_name", a.getDeclaredName(), "span", span(a),
            "definitions", a.getActionDefinition().stream().map(ExtractStates::elementReference).toList());
        if (a instanceof PerformActionUsage performed) {
            out.put("performed", elementReference(performed.getPerformedAction()));
            out.put("argument_references", actionArgumentReferences(a));
            var sequence = actionSequence(a);
            if (sequence != null) out.put("sequence", sequence);
        }
        if (a instanceof SendActionUsage send) {
            out.put("receiver", expression(send.getReceiverArgument()));
            out.put("payload", expression(send.getPayloadArgument()));
            out.put("sender", expression(send.getSenderArgument()));
        }
        return out;
    }
    /** Export scalar attributes of a single scalar part for safe one-level chains. */
    static List<Object> structuralData(PartUsage usage) {
        if (!scalar(usage) || usage.getPartDefinition().size() != 1) return List.of();
        var definition = usage.getPartDefinition().get(0);
        var result = new ArrayList<Object>();
        for (var membership : definition.getFeatureMembership()) {
            var feature = membership.getMemberElement();
            if (!(feature instanceof AttributeUsage attribute) || !inputResources.contains(attribute.eResource())) continue;
            var values = new ArrayList<Object>();
            for (var relation : attribute.getOwnedRelationship())
                if (relation instanceof FeatureValue value) values.add(expression(value.getValue()));
            result.add(object("id", id(usage) + "." + attribute.getDeclaredName(),
                "structural_base", id(usage), "structural_target", id(attribute),
                "types", attribute.getAttributeDefinition().stream().map(ExtractStates::id).toList(),
                "type_elements", attribute.getAttributeDefinition().stream().map(ExtractStates::elementReference).toList(),
                "values", values, "constant", attribute.isConstant(), "scalar", scalar(attribute),
                "span", span(attribute)));
        }
        return result;
    }
    static List<Object> actionArgumentReferences(ActionUsage action) {
        var result = new ArrayList<Object>();
        var seen = new HashSet<String>();
        var tree = action.eAllContents();
        while (tree.hasNext()) {
            if (tree.next() instanceof FeatureReferenceExpression reference && reference.getReferent() != null
                && seen.add(id(reference.getReferent())))
                result.add(expression(reference));
        }
        return result;
    }
    static Set<String> referencedFeatures(Collection<? extends Membership> memberships) {
        var references = new HashSet<String>();
        for (var membership : memberships) {
            var element = membership.getMemberElement();
            if (element == null) continue;
            // Abstract action calls retain their typed argument references in the
            // exported action record; they are not structural dependencies of the
            // state topology and must not block the surrounding state.
            if (element instanceof PerformActionUsage || element instanceof SendActionUsage) continue;
            // Constraints describe verification properties, not control topology.
            // Their internal references must not make the constraint membership
            // itself look like a required structural control member.
            if (element instanceof ConstraintUsage) continue;
            // A child state owns its own behavior references. Walking its complete
            // subtree here would incorrectly make an ancestor's structural alias
            // look behaviorally referenced.
            if (element instanceof StateUsage || element instanceof StateDefinition) continue;
            var tree = element.eAllContents();
            while (tree.hasNext()) {
                var child = tree.next();
                if (child instanceof FeatureReferenceExpression reference && reference.getReferent() != null)
                    references.add(id(reference.getReferent()));
            }
        }
        return references;
    }
    static Map<String, Object> state(Type s, Set<Type> ancestors) {
        if (!ancestors.add(s)) return object("id", id(s), "unsupported", List.of("recursive_state_typing"));
        var children = new ArrayList<Object>();
        var transitions = new ArrayList<Object>();
        var actions = new ArrayList<Object>();
        var data = new ArrayList<Object>();
        var unsupported = new ArrayList<String>();
        var ignoredStructural = new ArrayList<Object>();
        if (!scalar(s)) unsupported.add("state_multiplicity");
        var memberships = new LinkedHashSet<Membership>(s.getOwnedMembership());
        memberships.addAll(s.getInheritedMembership());
        var references = referencedFeatures(memberships);
        for (Membership member : memberships) {
            // Library feature inheritance is not a user control-state declaration.
            // Project mode keeps inherited members from every input resource.
            if (!inputResources.contains(member.eResource())) continue;
            Element e = member.getMemberElement();
            if (e instanceof StateUsage child) children.add(state(child, new HashSet<>(ancestors)));
            else if (member instanceof StateSubactionMembership sub && e instanceof ActionUsage a) {
                actions.add(object("id", id(a), "role", sub.getKind().getLiteral(),
                    "action", action(a)));
            }
            else if (e instanceof TransitionUsage t) {
                var triggerElements = t.getTriggerAction().stream()
                    .map(a -> a.getPayloadParameter() == null ? List.<Type>of() : a.getPayloadParameter().getType())
                    .flatMap(Collection::stream)
                    .map(ExtractStates::elementReference).filter(Objects::nonNull).toList();
                var triggers = triggerElements.stream().map(v -> ((Map<?, ?>)v).get("id"))
                    .filter(Objects::nonNull).toList();
                var target = t.getTarget();
                transitions.add(object("id", id(t), "source", id(t.getSource()), "source_element", elementReference(t.getSource()),
                    "target", id(t.getTarget()),
                    "guards", t.getGuardExpression().stream().map(ExtractStates::expression).toList(),
                    "effects", t.getEffectAction().stream().map(ExtractStates::action).toList(),
                    "triggers", triggers, "trigger_elements", triggerElements,
                    "trigger_count", t.getTriggerAction().size(), "target_element", elementReference(target),
                    "span", span(t)));
            } else if (e instanceof SuccessionAsUsage t) {
                transitions.add(object("id", id(t), "source", id(t.getSourceFeature()),
                    "source_element", elementReference(t.getSourceFeature()),
                    "target", t.getTargetFeature().size() == 1 ? id(t.getTargetFeature().get(0)) : null,
                    "guards", List.of(), "effects", List.of(), "trigger_count", 0,
                    "target_element", t.getTargetFeature().size() == 1
                        ? elementReference(t.getTargetFeature().get(0)) : null,
                    "span", span(t)));
            } else if (e instanceof AttributeUsage v) {
                var values = new ArrayList<Object>();
                for (var relation : v.getOwnedRelationship())
                    if (relation instanceof FeatureValue fv) values.add(expression(fv.getValue()));
                data.add(object("id", id(v), "types", v.getAttributeDefinition().stream().map(ExtractStates::id).toList(),
                    "type_elements", v.getAttributeDefinition().stream().map(ExtractStates::elementReference).toList(),
                    "values", values, "constant", v.isConstant(), "scalar", scalar(v), "span", span(v)));
            } else if (e instanceof PartUsage part) {
                var structural = structuralData(part);
                if (!structural.isEmpty()) data.addAll(structural);
                else if (!references.contains(id(e)))
                    ignoredStructural.add(object("element", elementReference(e), "reason", "unreferenced_structural_member"));
                else unsupported.add(e.eClass().getName());
            } else if (!(e instanceof Comment) && !(e instanceof Documentation)) {
                var kind = e.eClass().getName();
                if (e instanceof ActionUsage && !(member instanceof StateSubactionMembership)
                    && !references.contains(id(e))) {
                    ignoredStructural.add(object("element", elementReference(e),
                        "reason", "action_declaration_outside_control_profile"));
                } else if ((e instanceof ConstraintUsage
                     || Set.of("ReferenceUsage", "PartUsage", "PortUsage").contains(kind))
                    && !references.contains(id(e))) {
                    String reason = e instanceof ConstraintUsage
                        ? "verification_constraint_outside_control_profile"
                        : "unreferenced_structural_member";
                    ignoredStructural.add(object("element", elementReference(e), "reason", reason));
                } else {
                    unsupported.add(kind);
                }
            }
        }
        boolean parallel = s instanceof StateDefinition d ? d.isParallel() : ((StateUsage)s).isParallel();
        return object("id", id(s), "kind", s.eClass().getName(), "declared_name", s.getDeclaredName(),
            "parallel", parallel, "span", span(s), "states", children,
            "transitions", transitions, "actions", actions, "data", data,
            "ignored_structural", ignoredStructural, "unsupported", unsupported);
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
                inputResources = Set.of(workspace.getResource());
                inputHashes = Map.of(workspace.getResource(), sha256(Path.of(source.get("path").getAsString())));
                var tree = workspace.getRootElement().eAllContents();
                while (tree.hasNext()) {
                    var element = tree.next();
                    if (topState(element)) roots.add(state((Type)element, new HashSet<>()));
                }
                record.put("status", "extracted");
                record.put("states", roots);
                record.put("detail", result.formatIssues());
                workspace.removeResource();
                inputResources = Set.of();
                inputHashes = Map.of();
            }
            results.add(record);
        }
        Files.writeString(Path.of(args[2]), JSON.toJson(object("models", results)) + "\n");
    }
}
