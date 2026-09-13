package StructuralUnsafeProbe {
    part def Device {
        action declaration;
    }

    state def Controller {
        part context : Device;
        entry; then idle;
        state idle;
    }
}
