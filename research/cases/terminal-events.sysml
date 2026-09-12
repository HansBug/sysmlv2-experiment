package TerminalEvents {
    attribute def Go;

    state def Controller {
        entry; then idle;

        state idle;
        state running;

        transition start_running
            first idle
            accept Go
            then running;

        transition finish
            first running
            then done;
    }
}
