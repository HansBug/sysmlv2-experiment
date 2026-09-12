package StructuralContextProbe {
    part def Device;

    state def Controller {
        part context : Device;
        entry; then idle;
        state idle;
    }
}
