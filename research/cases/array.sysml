package ArrayProbe {
    private import ScalarValues::*;
    state def Controller {
        attribute x : Integer[2] = (0, 0);
        entry; then Idle;
        state Idle;
    }
}
