package ConstraintIgnoreProbe {
    private import ScalarValues::*;

    state def Controller {
        action declaration;
        attribute x : Integer = 0;
        entry; then Idle;
        state Idle;
        state Active;
        transition go first Idle if x > 0 then Active;
        assert constraint { x >= 0 }
    }
}
