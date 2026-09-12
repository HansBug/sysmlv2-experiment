import org.omg.sysml.interactive.SysMLInteractive;
import org.omg.sysml.lang.sysml.*;
import org.eclipse.xtext.nodemodel.util.NodeModelUtils;

public class LinkedStateProbe {
    public static void main(String[] args) throws Exception {
        var workspace = SysMLInteractive.createInstance();
        workspace.setVerbose(false);
        workspace.loadLibrary(args[0]);
        String[] sources = {
            "package Types { state def Controller { entry; then Idle; state Idle; state Active; transition turnOn first Idle if true then Active; } }",
            "package App { private import Types::*; part def Device { exhibit state controller : Controller; } }"
        };
        for (String source : sources) {
            var result = workspace.process(source);
            System.out.println("issues=" + result.formatIssues());
            if (result.getException() != null) throw result.getException();
            if (result.hasErrors()) throw new AssertionError("Invalid input: " + result.formatIssues());
        }
        var transition = (TransitionUsage) workspace.resolve("Types::Controller::turnOn");
        var controller = (StateUsage) workspace.resolve("App::Device::controller");
        if (transition == null || controller == null) throw new AssertionError("Names unresolved");
        System.out.println("source=" + transition.getSource().getQualifiedName());
        System.out.println("target=" + transition.getTarget().getQualifiedName());
        System.out.println("guard=" + transition.getGuardExpression().get(0).eClass().getName());
        System.out.println("type=" + controller.getStateDefinition().get(0).getQualifiedName());
        System.out.println("inherited=" + controller.getInheritedMembership().stream().map(m -> m.getMemberElement().getQualifiedName()).filter(n -> n != null && n.startsWith("Types::")).toList());
        if (!"Types::Controller::Idle".equals(transition.getSource().getQualifiedName())) throw new AssertionError("Source link");
        if (!"Types::Controller::Active".equals(transition.getTarget().getQualifiedName())) throw new AssertionError("Target link");
        if (controller.getStateDefinition().stream().noneMatch(t -> "Types::Controller".equals(t.getQualifiedName()))) throw new AssertionError("Cross-resource typing");
        var node = NodeModelUtils.getNode(transition);
        if (node == null || node.getLength() == 0) throw new AssertionError("Source span unavailable");
        System.out.println("transition source offset=" + node.getOffset() + " length=" + node.getLength());
        var invalid = workspace.process("package Invalid { part def Device { exhibit state c : MissingController; } }");
        if (invalid.getException() != null) throw invalid.getException();
        if (invalid.getSemanticErrors().isEmpty()) throw new AssertionError("Unresolved typing accepted");
        System.out.println("unresolved-type-errors=" + invalid.getSemanticErrors().size());
        System.out.println("PASS: native linking, transition endpoints, guard, inherited state typing, source span, unresolved reference rejection");
    }
}
