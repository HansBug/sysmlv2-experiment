import java.nio.file.*;
import org.omg.sysml.interactive.SysMLInteractive;
import org.omg.sysml.lang.sysml.*;
import org.eclipse.xtext.nodemodel.util.NodeModelUtils;

/** Compare the same inputs with the official linked workspace, not a generic EMF dump. */
public class FrontendProbe {
    public static void main(String[] args) throws Exception {
        var workspace = SysMLInteractive.createInstance();
        workspace.setVerbose(false);
        workspace.loadLibrary(args[0]);
        for (String name : new String[]{"types", "app", "parallel", "actions", "inheritance", "constant", "invalid-type", "invalid-target"}) {
            var file = Path.of(args[1], name + ".sysml");
            var result = workspace.process(Files.readString(file));
            if (result.getException() != null) throw result.getException();
            System.out.println(name + " errors=" + result.hasErrors() + " issues=" + result.formatIssues());
            if (result.hasErrors() != name.startsWith("invalid-")) throw new AssertionError(name);
        }
        var t = (TransitionUsage)workspace.resolve("Types::Controller::turnOn");
        if (!t.getSource().getQualifiedName().equals("Types::Controller::Idle")) throw new AssertionError("source");
        if (!t.getTarget().getQualifiedName().equals("Types::Controller::Active")) throw new AssertionError("target");
        System.out.println("transition=" + t.getSource().getQualifiedName() + " -> " + t.getTarget().getQualifiedName());
        var node = NodeModelUtils.getNode(t);
        if (node == null || node.getLength() == 0) throw new AssertionError("span");
        System.out.println("span=" + node.getOffset() + ":" + node.getLength());
        var parallel = (StateDefinition)workspace.resolve("Parallel::Regions");
        if (!parallel.isParallel()) throw new AssertionError("parallel lost");
        var action = (TransitionUsage)workspace.resolve("ActionsProbe::Controller::go");
        if (!(action.getEffectAction().get(0) instanceof AssignmentActionUsage)) throw new AssertionError("assignment lost");
        var usage = (StateUsage)workspace.resolve("Inheritance::Device::controller");
        var inherited = usage.getInheritedMembership().stream().map(m -> m.getMemberElement().getQualifiedName())
            .filter(n -> n != null && n.startsWith("Types::")).toList();
        if (!inherited.contains("Types::Controller::Idle")) throw new AssertionError("inherited state missing");
        System.out.println("inherited=" + inherited);
        System.out.println("PASS: official frontend accepts current constant syntax and retains linked controller facts");
    }
}
