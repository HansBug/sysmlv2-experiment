package AssignmentProbe {
    private import ScalarValues::*;
    state def Controller {
        attribute x : Integer = 0;
        entry; then Idle;
        state Idle { entry assign x := 1; }
        state Active;
        transition go first Idle if x > 0 do assign x := 4 then Active;
    }
}
