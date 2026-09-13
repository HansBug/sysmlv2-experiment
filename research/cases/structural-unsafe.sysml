package StructuralUnsafeProbe {
    private import ScalarValues::*;

    part def Device {
        attribute count : Integer = 0;
        action tick {
            assign count := count + 1;
        }
    }

    state def Controller {
        part context : Device;
        entry; then idle;
        state idle;
    }
}
