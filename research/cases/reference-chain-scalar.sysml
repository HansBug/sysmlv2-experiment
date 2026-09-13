package ReferenceChainScalarProbe {
    private import ScalarValues::*;

    part def Counter {
        attribute count : Integer = 0;
    }

    state def Controller {
        in counter : Counter;
        entry; then Idle;
        state Idle {
            entry assign counter.count := 1;
        }
        state Active;
        transition go first Idle if counter.count > 0 then Active;
    }
}
